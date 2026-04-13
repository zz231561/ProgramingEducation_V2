"""Feedback 層 — 分層 prompt 組裝 + LLM 回應生成 + 輸出驗證。

組裝順序：preamble → persona → strategy → context → student message
輸出驗證：阻擋完整程式碼洩漏，保持教學引導。
"""

import re

from openai import AsyncOpenAI

from core.config import settings
from core.errors import AppError
from .models import EvidenceResult
from .decision import TeachingStrategy
from services.security.sanitizer import wrap_student_input

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
RULE-5: 永遠以提問結尾，引導學生思考下一步。\
"""

PERSONA = """\
你是一位有耐心的大學助教，說話風格親切但專業。\
你會根據學生的程度調整解釋深度。\
"""


def build_system_prompt(
    evidence: EvidenceResult,
    strategy: TeachingStrategy,
) -> str:
    """組裝完整 system prompt。"""
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

    return "\n\n".join([PREAMBLE, PERSONA, strategy_block, context_block])


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
) -> str:
    """組裝 prompt、呼叫 LLM、驗證輸出，回傳教學回應。"""
    client = _get_client()
    system_prompt = build_system_prompt(evidence, strategy)

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    if chat_history:
        messages.extend(chat_history[-10:])  # 最多保留最近 10 輪

    messages.append({"role": "user", "content": wrap_student_input(student_message)})

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=600,
        )
    except Exception as e:
        raise AppError(502, "LLM_ERROR", f"AI 服務暫時不可用：{e}") from e

    raw = response.choices[0].message.content or ""

    return validate_output(raw, strategy.allow_code_snippet)
