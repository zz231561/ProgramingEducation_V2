"""Quiz Hint 生成 — LLM 依 hint_level (1-5) 給提示（roadmap 3-2b）。

Hint Ladder（與 .claude/rules/edf-pipeline.md 對齊）：
- Level 1：指出錯誤方向，不指出具體位置 — 「問題和迴圈邏輯有關，再看看」
- Level 2：指出具體位置 + 概念名稱 — 「第 3 行的 for 迴圈條件可能寫錯」
- Level 3：給出部分程式碼框架（含 TODO）— 「試試 for(int i=0; i<???; i++)」
- Level 4：逐步引導，只差最後一步 — 「i 範圍到 N 後，迴圈內要做什麼？」
- Level 5：接近完整解釋 + 修正片段（不可直接給完整答案）

設計：
- 純 LLM 即時生成，不寫入 DB（hint_level_used 已透過 /quiz/submit 帶回）
- 失敗 fallback：固定鼓勵句，不擋學生
- max 5：caller 負責檢查 level 範圍（API 層 422）
"""

import json
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI

from core.config import settings
from models.quiz import Question, QuestionType

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            return None
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


@dataclass(frozen=True)
class HintResult:
    """LLM 生成的提示。`fallback=True` 表示 LLM 失敗用了固定句子。"""

    level: int
    hint: str
    fallback: bool


_FALLBACK_HINTS: dict[int, str] = {
    1: "想想題目要解決什麼問題？從輸入與輸出的關係開始拆解。",
    2: "看看題目提到的關鍵概念，回想對應的語法或函式。",
    3: "試著寫出基本框架（如迴圈或條件式），即使還不完整也沒關係。",
    4: "你已經接近答案了。檢查每個步驟是否完整覆蓋了題目要求。",
    5: "把每一行對照題目要求逐一檢查；通常問題出在邊界條件或型別轉換。",
}


def _ladder_description(level: int) -> str:
    rules = {
        1: "指出問題方向但不指位置（例：「問題和迴圈邏輯有關」）",
        2: "指出具體位置 + 概念名稱（例：「第 3 行 for 迴圈條件可能錯」）",
        3: "給部分程式碼框架含 TODO（例：「試試 for(int i=0; i<???; i++)」）",
        4: "逐步引導只差最後一步（例：「i 到 N 後，迴圈內該做什麼？」）",
        5: "接近完整解釋 + 修正片段；**不可給完整答案**",
    }
    return rules.get(level, "提供合適的引導")


def _format_question_for_prompt(question: Question) -> str:
    content = question.content or {}
    stem = content.get("stem", "")
    if question.type == QuestionType.MULTIPLE_CHOICE.value:
        options = content.get("options", [])
        return (
            f"題型：選擇題\n題幹：{stem}\n"
            f"選項：{json.dumps(options, ensure_ascii=False)}"
        )
    if question.type == QuestionType.CODING.value:
        starter = content.get("starter_code", "")
        return (
            f"題型：程式撰寫題\n題幹：{stem}\n"
            f"起始碼：\n```cpp\n{starter}\n```"
        )
    return f"題型：{question.type}\n題幹：{stem}"


def _build_prompt(
    question: Question, hint_level: int, student_attempt: str
) -> str:
    attempt_block = (
        f"\n學生目前作答：\n```\n{student_attempt}\n```"
        if student_attempt
        else ""
    )
    return f"""\
你是 C++ 學習教練。學生正在解題，請依 Hint Level {hint_level} 給對應的提示。

{_format_question_for_prompt(question)}
涉及概念：{question.concept_tags}
Bloom 等級：{question.bloom_level}{attempt_block}

Level {hint_level} 規則：{_ladder_description(hint_level)}

通用規則：
- 回 1-2 句中文，溫暖鼓勵口吻
- **不可給完整答案 / 完整程式碼**（即使 Level 5）
- 不可單純複述題目；要提供新的引導資訊

回傳嚴格 JSON：{{"hint": "<1-2 句中文提示>"}}
"""


async def generate_hint(
    question: Question,
    hint_level: int,
    student_attempt: str = "",
) -> HintResult:
    """LLM 生成對應 level 的 hint；失敗回 fallback 鼓勵句。

    Args:
        question: 題目物件
        hint_level: 1-5（caller 負責驗證範圍）
        student_attempt: 學生目前的作答（coding 時很有幫助；MC 可填選項描述）

    Returns:
        HintResult（fallback=True 表示用了固定 fallback 句）
    """
    client = _get_client()
    if client is None:
        return HintResult(
            level=hint_level,
            hint=_FALLBACK_HINTS.get(hint_level, "請再仔細思考題目要求。"),
            fallback=True,
        )

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _build_prompt(question, hint_level, student_attempt)},
                {"role": "user", "content": "請給提示並回傳 JSON。"},
            ],
            temperature=0.4,
            max_tokens=200,
        )
    except Exception:
        return HintResult(
            level=hint_level,
            hint=_FALLBACK_HINTS.get(hint_level, "請再仔細思考題目要求。"),
            fallback=True,
        )

    raw = response.choices[0].message.content or "{}"
    try:
        data: dict[str, Any] = json.loads(raw)
        hint = data.get("hint")
        if not isinstance(hint, str) or not hint.strip():
            raise ValueError("empty hint")
    except (json.JSONDecodeError, ValueError):
        return HintResult(
            level=hint_level,
            hint=_FALLBACK_HINTS.get(hint_level, "請再仔細思考題目要求。"),
            fallback=True,
        )

    return HintResult(level=hint_level, hint=hint.strip(), fallback=False)
