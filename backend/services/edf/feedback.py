"""Feedback 層 — LLM 回應生成 + 輸出驗證。

prompt 組裝在 `prompt_blocks.py`（7-C2a 抽出）；本檔只管呼叫 LLM 與把關輸出。
輸出驗證：阻擋完整程式碼洩漏，保持教學引導。
RAG（K4b）：每次互動都檢索，由相似度分數決定是否注入（rag_integration 過濾）。
K-Graph state（K4a）：學生 mastery 狀態 + 鷹架指令，由 caller 預先渲染傳入。
"""

import logging
import re

from openai import AsyncOpenAI

from core.config import settings
from core.errors import AppError
from core.llm_params import chat_model_kwargs
from services.edf.citations import extract_citations, strip_ungrounded_citations
from services.edf.off_topic import generate_off_topic_reply
from services.edf.prompt_blocks import build_system_prompt
from services.edf.rag_integration import fetch_rag_chunks_safe
from services.rag import RetrievedChunk
from services.security.sanitizer import wrap_student_input

from .decision import TeachingStrategy
from .models import EvidenceResult

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise AppError(503, "LLM_UNAVAILABLE", "OpenAI API Key 未設定")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client



_CODE_BLOCK_RE = re.compile(r"```[\w]*\n(.*?)```", re.DOTALL)
_GUARD_TOKENS = {"TODO", "FIXME", "// ...", "/* ... */", "___"}


def validate_output(text: str, allow_code: bool) -> str:
    """驗證 LLM 回應，阻擋完整程式碼洩漏。

    規則：
    - 若 allow_code=False，移除所有 code block
    - 若 allow_code=True，code block 超過 8 行且無 guard token → 截斷
    """
    if not allow_code:
        return _CODE_BLOCK_RE.sub("[程式碼片段已移除 — 請自己動手試試看]", text)

    def _check_block(match: re.Match) -> str:
        code = match.group(1)
        lines = [line for line in code.strip().splitlines() if line.strip()]

        if len(lines) <= 8:
            return match.group(0)

        # 超過 8 行：檢查是否有 guard token
        has_guard = any(token in code for token in _GUARD_TOKENS)
        if has_guard:
            return match.group(0)

        # 截斷為前 6 行 + 提示
        truncated = "\n".join(lines[:6])
        lang = match.group(0).split("\n")[0]  # ```cpp 等
        return f"{lang}\n{truncated}\n// ... 剩餘部分請自己完成\n```"

    return _CODE_BLOCK_RE.sub(_check_block, text)



async def generate_feedback(
    evidence: EvidenceResult,
    strategy: TeachingStrategy,
    student_message: str,
    chat_history: list[dict[str, str]] | None = None,
    reflection_block: str = "",
    kgraph_block: str = "",
    debug_sink: dict | None = None,
    citations_sink: list[dict] | None = None,
) -> str:
    """組裝 prompt、呼叫 LLM、驗證輸出，回傳教學回應。

    `reflection_block` 是學生反思的詳細版字串；空字串代表不注入。
    `kgraph_block`（K4a）：學生 K-Graph 知識狀態 + 鷹架指令；空字串代表不注入。
    RAG（K4b）：一律檢索，`fetch_rag_chunks_safe` 內部依相似度分數過濾。
    `debug_sink`（DEV-7）：dev 帳號的中間層觀測 dict；非 None 時寫入 RAG 命中明細。
    `citations_sink`：非 None 時寫入本次引用的教材出處（供前端顯示原文核對）。
    """
    client = _get_client()

    # 成本分流：離題訊息不需要 RAG 檢索與完整教學 prompt（input 約降至 1/8）。
    # 注意這是「換一條路徑」不是「攔截」——學生一樣會收到回應，只是簡短並引導回課程。
    if not evidence.is_on_topic:
        return await generate_off_topic_reply(client, student_message)

    rag_chunks: list[RetrievedChunk] = await fetch_rag_chunks_safe(
        evidence, student_message
    )
    if debug_sink is not None:
        debug_sink["rag_chunks"] = [
            {"score": round(c.score, 4), "doc_id": c.doc_id, "preview": c.text[:200]}
            for c in rag_chunks
        ]
    system_prompt = build_system_prompt(
        evidence, strategy, rag_chunks, reflection_block, kgraph_block
    )

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    if chat_history:
        messages.extend(chat_history[-10:])  # 最多保留最近 10 輪

    messages.append({"role": "user", "content": wrap_student_input(student_message)})

    try:
        response = await client.chat.completions.create(
            messages=messages,
            **chat_model_kwargs(
                model=settings.LLM_MODEL, temperature=0.7, max_tokens=600
            ),
        )
    except Exception as e:
        # 502 是預期內的錯誤碼，不會進 unhandled_error_handler 的 traceback logging——
        # 沒有這行，生產環境只會留下一句 "502 Bad Gateway"，查不到任何原因
        logger.warning(
            "Feedback LLM 呼叫失敗（model=%s）：%s: %s",
            settings.LLM_MODEL, type(e).__name__, e,
        )
        raise AppError(502, "LLM_ERROR", f"AI 服務暫時不可用：{e}") from e

    raw = response.choices[0].message.content or ""
    validated = validate_output(raw, strategy.allow_code_snippet)

    # 機械式防幻覺：prompt 規則不保證 LLM 遵守，這裡把不在檢索結果內的影片連結移除
    cleaned, removed = strip_ungrounded_citations(validated, rag_chunks)
    if debug_sink is not None:
        debug_sink["citations_stripped"] = removed
    if citations_sink is not None:
        citations_sink.extend(extract_citations(rag_chunks))
    return cleaned
