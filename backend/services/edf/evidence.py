"""Evidence 層 — LLM 結構化分析學生程式碼。

呼叫 OpenAI GPT-4o，以 JSON mode 回傳錯誤分類、ConceptTag、Bloom 認知等級。
"""

import json

from openai import AsyncOpenAI

from core.config import settings
from core.errors import AppError
from .models import EvidenceResult, CONCEPT_TAGS

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

判斷規則：
- bloom_level 根據學生「嘗試做的事」判斷，不是根據錯誤嚴重度
- concept_tags 最多選 3 個最相關的
- 若程式碼正確無誤，error_type 為 "none"，仍需分析涉及的概念和 Bloom 等級
"""


def _build_user_prompt(
    source_code: str,
    stdout: str,
    stderr: str,
    compile_output: str,
) -> str:
    """組裝送給 LLM 的使用者 prompt。"""
    parts = [f"```cpp\n{source_code}\n```"]

    if compile_output:
        parts.append(f"編譯器輸出:\n```\n{compile_output}\n```")
    if stderr:
        parts.append(f"stderr:\n```\n{stderr}\n```")
    if stdout:
        parts.append(f"stdout:\n```\n{stdout}\n```")

    if not compile_output and not stderr:
        parts.append("程式執行成功，無錯誤。")

    return "\n\n".join(parts)


async def analyze_evidence(
    source_code: str,
    stdout: str = "",
    stderr: str = "",
    compile_output: str = "",
) -> EvidenceResult:
    """呼叫 LLM 分析程式碼，回傳結構化 Evidence。"""
    client = _get_client()
    user_prompt = _build_user_prompt(source_code, stdout, stderr, compile_output)

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=500,
        )
    except Exception as e:
        raise AppError(502, "LLM_ERROR", f"AI 服務暫時不可用：{e}") from e

    raw = response.choices[0].message.content or "{}"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AppError(502, "LLM_PARSE_ERROR", "AI 回傳格式異常") from e

    return EvidenceResult(**data)
