"""Phase 6-3b：從 questions 題庫隨機抽 validated grounded 題目（避開即時 LLM）。

設計：
- 篩選條件：validated=True 且 concept_tags JSON 陣列含目標 tag
- 隨機策略：Python random.choice；n 不大（每 concept ≤ 數十題），效能可接受
- U2d（2026-07-06）：`exclude_answered_by` 排除該學生已答過的題（消除重複曝光
  tech-debt）；全部答過 → None → caller fallback 至現生（新題入庫，題庫自然成長）
- 與 generate.py 區隔：本層完全不呼叫 LLM、不需 retry；caller 失敗時 fallback 至現生
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.quiz import Question, QuestionSource, StudentAnswer


async def pick_random_validated_question(
    db: AsyncSession,
    concept_tag: str,
    exclude_question_ids: list | None = None,
    question_type: str | None = None,
    exclude_answered_by: UUID | None = None,
) -> Question | None:
    """依 concept_tag 隨機抽一題 validated=True 的題目。

    Args:
        db: SQLAlchemy async session
        concept_tag: 目標概念 tag（須完整匹配 concept_tags JSON 陣列其中一元素）
        exclude_question_ids: 可選排除清單（已答過 / 不想再出的 question.id）
        question_type: 可選題型過濾（U2d：Quiz 頁依使用者選的題型抽）
        exclude_answered_by: 可選使用者 UUID——排除其已作答過的題（重複曝光防護）

    Returns:
        Question 物件；題庫無符合題目 → None（caller 決定 fallback 行為）
    """
    # 取所有 validated 題 + concept_tags 內含 tag — JSON contains 寫法 SQLite/PG 不同，
    # 為相容性先撈出 validated rows 再 Python filter（n 不大，每 concept ≤ 數十題可接受）。
    stmt = select(Question).where(Question.validated.is_(True))
    if question_type is not None:
        stmt = stmt.where(Question.type == question_type)
    if exclude_question_ids:
        stmt = stmt.where(Question.id.notin_(exclude_question_ids))
    if exclude_answered_by is not None:
        answered = select(StudentAnswer.question_id).where(
            StudentAnswer.user_id == exclude_answered_by
        )
        stmt = stmt.where(Question.id.notin_(answered))
    rows = (await db.execute(stmt)).scalars().all()
    candidates = [q for q in rows if concept_tag in (q.concept_tags or [])]
    if not candidates:
        return None

    return random.choice(candidates)


@dataclass(frozen=True)
class UnitQuestionItem:
    """單元題組中的一題 + 該學生作答狀態。"""

    question: Question
    is_answered: bool
    is_correct: bool


async def list_unit_question_set(
    db: AsyncSession,
    concept_tag: str,
    answered_by: UUID,
    question_type: str | None = None,
) -> list[UnitQuestionItem]:
    """取某概念「預生成題組」全部題 + 該學生作答狀態（LEARN 逐題作答用）。

    只列 source='batch' 的題（QUIZ 弱項現生題 source='generated' 不進單元題組）。
    依 created_at 排序保持穩定順序；每題附 is_answered / is_correct（取最後一次作答）。
    """
    stmt = select(Question).where(
        Question.validated.is_(True),
        Question.source == QuestionSource.BATCH.value,
    )
    if question_type is not None:
        stmt = stmt.where(Question.type == question_type)
    stmt = stmt.order_by(Question.created_at)
    rows = (await db.execute(stmt)).scalars().all()
    questions = [q for q in rows if concept_tag in (q.concept_tags or [])]

    # 該學生對這些題的最後一次作答結果
    answers = (
        await db.execute(
            select(StudentAnswer.question_id, StudentAnswer.is_correct)
            .where(StudentAnswer.user_id == answered_by)
            .order_by(StudentAnswer.answered_at)
        )
    ).all()
    last_correct: dict[UUID, bool] = {qid: correct for qid, correct in answers}

    return [
        UnitQuestionItem(
            question=q,
            is_answered=q.id in last_correct,
            is_correct=last_correct.get(q.id, False),
        )
        for q in questions
    ]
