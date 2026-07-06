"""Feedback 層 — 分層 prompt 組裝 + LLM 回應生成 + 輸出驗證。

組裝順序：preamble → persona → strategy → context → kgraph → reflection → rag
輸出驗證：阻擋完整程式碼洩漏，保持教學引導。
RAG（K4b）：每次互動都檢索，由相似度分數決定是否注入（rag_integration 過濾）。
K-Graph state（K4a）：學生 mastery 狀態 + 鷹架指令，由 caller 預先渲染傳入。
"""

import re

from openai import AsyncOpenAI

from core.config import settings
from core.llm_params import chat_model_kwargs
from core.errors import AppError
from services.edf.rag_integration import fetch_rag_chunks_safe
from services.rag import RetrievedChunk
from services.security.sanitizer import wrap_student_input

from .decision import TeachingStrategy
from .models import EvidenceResult

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise AppError(503, "LLM_UNAVAILABLE", "OpenAI API Key 未設定")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


# === Prompt 各層 ===

PREAMBLE = """\
你是一位 C++ 程式設計課程的 AI 教學助理。你的目標是引導學生自主理解和解決問題，\
而不是直接給出答案。

不可違反的規則：
RULE-1: 絕對不要提供完整的解答程式碼。
RULE-2: 程式碼片段最多 8 行，且必須包含 TODO 或 FIXME 註解讓學生完成。
RULE-3: 用繁體中文回覆，技術術語保留英文。
RULE-4: 回覆控制在 200 字以內，簡潔有力。
RULE-5: 以自然的下一步收尾 — 可以是引導式提問，也可以是具體的行動建議\
（如「試著把第 6 行改掉再跑一次」）；不必刻意反問。\
"""

PERSONA = """\
你叫 Coddy，是一位陪學生寫 code 的大學助教。語氣自然口語，像坐在學生旁邊一起看螢幕：\
先肯定學生做對或想對的部分，再聊卡住的地方。\
避免制式句型（「你覺得呢？」「你認為會發生什麼？」連續出現會顯得機械），\
提問要具體到程式碼本身。學生只是確認小事時，直接給答案加一句補充即可，不用硬展開教學。\
"""


def build_system_prompt(
    evidence: EvidenceResult,
    strategy: TeachingStrategy,
    rag_chunks: list[RetrievedChunk] | None = None,
    reflection_block: str = "",
    kgraph_block: str = "",
) -> str:
    """組裝完整 system prompt。

    順序：preamble → persona → strategy → context → kgraph → reflection → rag
    （`.claude/rules/edf-pipeline.md` 規範的層次）

    `reflection_block`（Phase 2-5e）/ `kgraph_block`（K4a）：
    caller 預先渲染；傳空字串等於不注入。
    """
    strategy_block = f"""\
教學策略指令：{strategy.instruction}
允許程式碼片段：{"是（最多 8 行，必須含 TODO）" if strategy.allow_code_snippet else "否，不要提供任何程式碼"}
當前提示等級：{strategy.hint_level}/5\
"""

    context_block = f"""\
程式碼分析結果：
- 錯誤類型：{evidence.error_type.value}
- 錯誤摘要：{evidence.error_message}
- 涉及概念：{", ".join(evidence.concept_tags) or "無"}
- Bloom 認知等級：{evidence.bloom_level.name} (Level {evidence.bloom_level})
- 詳細分析：{evidence.code_analysis}\
"""

    blocks = [PREAMBLE, PERSONA, strategy_block, context_block]

    if kgraph_block:
        blocks.append(kgraph_block)

    if reflection_block:
        blocks.append(reflection_block)

    if rag_chunks:
        rag_lines = [f"[{i}] {c.text.strip()}" for i, c in enumerate(rag_chunks, 1)]
        rag_block = (
            "教材參考片段（請以這些教材內容為依據引導學生，避免自編未驗證的細節）：\n"
            + "\n\n".join(rag_lines)
        )
        blocks.append(rag_block)

    return "\n\n".join(blocks)


# === 輸出驗證 ===

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
        lines = [l for l in code.strip().splitlines() if l.strip()]

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


# === 主函式 ===

async def generate_feedback(
    evidence: EvidenceResult,
    strategy: TeachingStrategy,
    student_message: str,
    chat_history: list[dict[str, str]] | None = None,
    reflection_block: str = "",
    kgraph_block: str = "",
    debug_sink: dict | None = None,
) -> str:
    """組裝 prompt、呼叫 LLM、驗證輸出，回傳教學回應。

    `reflection_block`（Phase 2-5e）：學生反思的詳細版字串；空字串代表不注入。
    `kgraph_block`（K4a）：學生 K-Graph 知識狀態 + 鷹架指令；空字串代表不注入。
    RAG（K4b）：一律檢索，`fetch_rag_chunks_safe` 內部依相似度分數過濾。
    `debug_sink`（DEV-7）：dev 帳號的中間層觀測 dict；非 None 時寫入 RAG 命中明細。
    """
    client = _get_client()

    rag_chunks: list[RetrievedChunk] = await fetch_rag_chunks_safe(evidence)
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
        raise AppError(502, "LLM_ERROR", f"AI 服務暫時不可用：{e}") from e

    raw = response.choices[0].message.content or ""

    return validate_output(raw, strategy.allow_code_snippet)
