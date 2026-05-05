"""動態觸發 comprehension check 決策（roadmap 2-6e）。

依學生過往 comprehension 通過率 + 當前題型，決定：
- 是否觸發
- 若觸發，建議哪一種類型（epl / predict_output / variation）

決策規則（純函式 + DB 查詢，可預測、易測）：
- 取近 LOOKBACK_LIMIT 筆「有 comprehension_passed 結果」的紀錄（不限題目）
- 計算 pass_rate；無紀錄 = cold start

| 條件                         | should_trigger | type             |
|------------------------------|----------------|------------------|
| 無歷史紀錄（cold start）     | True           | EPL              |
| pass_rate ≥ 0.8              | False          | None             |
| 0.6 ≤ pass_rate < 0.8        | True           | VARIATION (高挑戰) |
| 0.3 ≤ pass_rate < 0.6        | True           | PREDICT_OUTPUT   |
| pass_rate < 0.3              | True           | EPL（回基礎）    |

題型限制：PREDICT_OUTPUT / VARIATION 僅對 coding 題型有效；非 coding 題自動 fallback EPL。
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.quiz import ComprehensionType, Question, QuestionType, StudentAnswer
from services.comprehension.crud import _get_owned_answer

LOOKBACK_LIMIT = 5
HIGH_PASS_THRESHOLD = 0.8
MID_HIGH_PASS_THRESHOLD = 0.6
MID_LOW_PASS_THRESHOLD = 0.3


@dataclass(frozen=True)
class TriggerDecision:
    """trigger-suggestion API 回傳的決策。"""

    should_trigger: bool
    suggested_type: ComprehensionType | None
    pass_rate: float | None  # None = 無歷史
    sample_size: int  # 近 N 筆樣本實際數
    reason: str  # 中文，給前端顯示用


async def _recent_pass_rate(
    db: AsyncSession, user_id: UUID
) -> tuple[float | None, int]:
    """取該使用者近 LOOKBACK_LIMIT 筆有 comprehension_passed 的紀錄，回 (rate, sample_size)。"""
    rows = (
        await db.execute(
            select(StudentAnswer.comprehension_passed)
            .where(StudentAnswer.user_id == user_id)
            .where(StudentAnswer.comprehension_passed.is_not(None))
            .order_by(desc(StudentAnswer.answered_at))
            .limit(LOOKBACK_LIMIT)
        )
    ).scalars().all()
    history = [bool(p) for p in rows]
    if not history:
        return None, 0
    return sum(history) / len(history), len(history)


def _coding_or_epl_fallback(
    is_coding: bool, preferred: ComprehensionType
) -> tuple[ComprehensionType, str]:
    """preferred 為 PREDICT/VARIATION 時，若非 coding 題型 → fallback 為 EPL + 補上 reason。"""
    if is_coding:
        return preferred, ""
    return ComprehensionType.EPL, "（題型非 coding，fallback EPL）"


def _decide(pass_rate: float | None, is_coding: bool) -> tuple[bool, ComprehensionType | None, str]:
    """純規則決策；獨立函式方便 unit test。"""
    if pass_rate is None:
        return True, ComprehensionType.EPL, "無歷史紀錄，cold start 觸發 EPL 暖身"

    if pass_rate >= HIGH_PASS_THRESHOLD:
        return False, None, f"通過率 {pass_rate:.0%} 高，跳過 comprehension 減少干擾"

    if pass_rate >= MID_HIGH_PASS_THRESHOLD:
        chosen, suffix = _coding_or_epl_fallback(is_coding, ComprehensionType.VARIATION)
        return True, chosen, f"通過率 {pass_rate:.0%} 中高，挑戰升級至 {chosen.value}{suffix}"

    if pass_rate >= MID_LOW_PASS_THRESHOLD:
        chosen, suffix = _coding_or_epl_fallback(is_coding, ComprehensionType.PREDICT_OUTPUT)
        return True, chosen, f"通過率 {pass_rate:.0%} 中等，驗證 {chosen.value}{suffix}"

    return True, ComprehensionType.EPL, f"通過率 {pass_rate:.0%} 低，回基礎 EPL 鞏固"


async def decide_trigger(
    db: AsyncSession, user_id: UUID, student_answer_id: UUID
) -> TriggerDecision:
    """為當前 student_answer 計算 comprehension trigger 建議。

    Raises:
        AppError 404 STUDENT_ANSWER_NOT_FOUND — 不存在或非本人擁有
        AppError 404 QUESTION_NOT_FOUND — FK 異常（理論上不會發生）
    """
    answer = await _get_owned_answer(db, student_answer_id, user_id)
    question = (
        await db.execute(select(Question).where(Question.id == answer.question_id))
    ).scalar_one_or_none()
    if question is None:
        raise AppError(404, "QUESTION_NOT_FOUND", f"找不到題目：{answer.question_id}")

    pass_rate, sample_size = await _recent_pass_rate(db, user_id)
    is_coding = question.type == QuestionType.CODING.value
    should_trigger, suggested_type, reason = _decide(pass_rate, is_coding)

    return TriggerDecision(
        should_trigger=should_trigger,
        suggested_type=suggested_type,
        pass_rate=pass_rate,
        sample_size=sample_size,
        reason=reason,
    )
