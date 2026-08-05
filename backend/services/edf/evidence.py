"""Evidence 層 — LLM 結構化分析學生程式碼。

呼叫 OpenAI GPT-4o，以 JSON mode 回傳錯誤分類、ConceptTag、Bloom 認知等級。
"""

import json
import logging

from openai import AsyncOpenAI
from pydantic import ValidationError

from core.config import settings
from core.llm_params import chat_model_kwargs
from core.errors import AppError
from .models import EvidenceResult, CONCEPT_TAGS
from services.security.sanitizer import wrap_student_code, wrap_student_input

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    """Lazy init OpenAI client。"""
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise AppError(503, "LLM_UNAVAILABLE", "OpenAI API Key 未設定")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


SYSTEM_PROMPT = f"""\
你是 C++ 程式教學分析引擎。根據學生的程式碼和執行結果，進行結構化分析。

回傳嚴格 JSON，欄位如下：
- error_type: "syntax" | "logic" | "runtime" | "compilation" | "semantic" | "none"
- error_message: 一句話描述錯誤（若無錯誤則為空字串）
- concept_tags: 涉及的概念標籤陣列（從以下選擇）
  {json.dumps(CONCEPT_TAGS)}
- bloom_level: 1-6 整數（1=REMEMBER, 2=UNDERSTAND, 3=APPLY, 4=ANALYZE, 5=EVALUATE, 6=CREATE）
- bloom_reasoning: 判斷 Bloom 等級的依據（一句話）
- code_analysis: 程式碼問題的詳細分析（2-3 句話，供教學策略使用）
- is_on_topic: 布林值 — 學生的提問是否與 C++ 程式學習相關

判斷規則：
- is_on_topic 只在提問明顯與程式學習無關時才為 false（閒聊、時事、生活話題等）。
  以下一律視為 true：任何程式問題、對教材/影片/課程的詢問（例如「老師上課有講嗎」）、
  對錯誤訊息的困惑、極簡短但語境上在求助的訊息（例如「?」「這是什麼意思」）
- bloom_level 根據學生「嘗試做的事」判斷，不是根據錯誤嚴重度
- concept_tags 最多選 3 個最相關的
- 若程式碼正確無誤，error_type 為 "none"，仍需分析涉及的概念和 Bloom 等級
"""


def _is_failing_status(status_description: str, exit_code: int | None) -> bool:
    """執行平台是否把這次執行判為失敗（NZEC / 逾時 / signal 等）。

    NZEC（非零 exit）這類失敗 stderr 全空，只有狀態欄看得到——
    沒有這個判斷，prompt 會對 LLM 說「程式執行成功」而學生螢幕上是 Runtime Error。
    """
    status = (status_description or "").strip()
    if status and status.lower() != "accepted":
        return True
    return isinstance(exit_code, int) and exit_code != 0


def _build_user_prompt(
    source_code: str,
    stdout: str,
    stderr: str,
    compile_output: str,
    reflection_summary: str = "",
    question: str = "",
    exit_code: int | None = None,
    status_description: str = "",
) -> str:
    """組裝送給 LLM 的使用者 prompt（XML 標籤隔離學生程式碼）。

    `reflection_summary` 由 caller 透過 `services.edf.reflection_context` 預先格式化。
    為何加在最後：避免反思內容稀釋 LLM 對程式碼/錯誤訊息的關注（核心仍是程式碼分析）。
    """
    parts = [wrap_student_code(source_code)]

    # 學生提問是 is_on_topic 判斷的唯一依據；沿用 sanitizer 包裝防 prompt injection
    if question:
        parts.append(wrap_student_input(question))

    if compile_output:
        parts.append(f"編譯器輸出:\n```\n{compile_output}\n```")
    if stderr:
        parts.append(f"stderr:\n```\n{stderr}\n```")
    if stdout:
        parts.append(f"stdout:\n```\n{stdout}\n```")

    if _is_failing_status(status_description, exit_code):
        exit_note = f"，exit code {exit_code}" if exit_code is not None else ""
        parts.append(
            f"執行平台狀態：{status_description or 'Runtime Error'}{exit_note}。"
            "（stderr 為空時這是唯一的失敗訊號，例如 main 回傳非零值）"
        )
    elif not compile_output and not stderr:
        parts.append("程式執行成功，無錯誤。")

    if reflection_summary:
        parts.append(reflection_summary)

    return "\n\n".join(parts)


async def analyze_evidence(
    source_code: str,
    stdout: str = "",
    stderr: str = "",
    compile_output: str = "",
    reflection_summary: str = "",
    question: str = "",
    exit_code: int | None = None,
    status_description: str = "",
) -> EvidenceResult:
    """呼叫 LLM 分析程式碼，回傳結構化 Evidence。

    `reflection_summary`（Phase 2-5e）：學生先前提交的反思摘要字串。
    傳空字串等於不注入；caller 應透過 `format_reflection_for_evidence` 預先渲染。
    `exit_code` / `status_description`：執行平台的結束狀態——NZEC 這類
    「stderr 全空的失敗」只有這兩個欄位看得到。
    """
    client = _get_client()
    user_prompt = _build_user_prompt(
        source_code, stdout, stderr, compile_output, reflection_summary, question,
        exit_code=exit_code, status_description=status_description,
    )

    try:
        response = await client.chat.completions.create(
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            **chat_model_kwargs(
                model=settings.LLM_MODEL, temperature=0.2, max_tokens=500
            ),
        )
    except Exception as e:
        logger.warning(
            "Evidence LLM 呼叫失敗（model=%s）：%s: %s",
            settings.LLM_MODEL, type(e).__name__, e,
        )
        raise AppError(502, "LLM_ERROR", f"AI 服務暫時不可用：{e}") from e

    raw = response.choices[0].message.content or "{}"

    # JSON mode 只保證合法 JSON，不保證符合 schema（如非法 enum 值）→ 兩段都要防
    try:
        data = json.loads(raw)
        return EvidenceResult(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise AppError(502, "LLM_PARSE_ERROR", "AI 回傳格式異常") from e
