"""Reflection CRUD service — 資料操作層（roadmap 2-5a）+ LLM 評分整合（2-5b）。

職責邊界：
- 本層做 schema 驗證 + DB 讀寫 + 觸發 LLM 評分（evaluate.py）。
- `source_id` 對 `quiz` 來源驗證指向 questions 表存在；`learning_unit` 來源
  因 learning_units 表尚未建立（Phase 3-1a），暫不驗證，由 caller 負責。
- 重複建立同一份反思（UNIQUE 衝突）回 409 而非 500。
- LLM 評分失敗（API down / parse error）→ fallback 為 quality_score=None，
  反思仍寫入；不阻擋學生流程（與 chat / quiz mastery 容錯哲學一致）。
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.quiz import Question
from models.reflection import Reflection, ReflectionSourceType
from services.reflection.evaluate import (
    ReflectionEvaluation,
    evaluate_reflection,
)


@dataclass(slots=True)
class ReflectionUpdate:
    """PATCH 反思時可更新的欄位（皆為 nullable，未提供者保留原值）。"""

    planned_steps: list[str] | None = None
    expected_concepts: str | None = None
    followup_answer: str | None = None
    problem_understanding: str | None = None


async def _validate_source_for_create(
    db: AsyncSession, source_type: ReflectionSourceType, source_id: UUID
) -> Question | None:
    """**僅 create 用** — 確認 source_id 指向有效對象，並回傳 Question 供 LLM 評分用。

    learning_unit 暫不驗證（表尚未建立）；回 None 代表「無題目脈絡」。

    Raises:
        AppError 404 REFLECTION_SOURCE_NOT_FOUND — quiz 來源指向不存在的題目
    """
    if source_type is ReflectionSourceType.QUIZ:
        question = (
            await db.execute(select(Question).where(Question.id == source_id))
        ).scalar_one_or_none()
        if question is None:
            raise AppError(
                404,
                "REFLECTION_SOURCE_NOT_FOUND",
                f"找不到題目：{source_id}",
            )
        return question
    return None


async def _load_question_best_effort(
    db: AsyncSession, reflection: Reflection
) -> Question | None:
    """**update 用** — 找題目當 LLM 評分脈絡；找不到不擋流程，回 None。"""
    if reflection.source_type != ReflectionSourceType.QUIZ.value:
        return None
    return (
        await db.execute(
            select(Question).where(Question.id == reflection.source_id)
        )
    ).scalar_one_or_none()


def _apply_evaluation(reflection: Reflection, evaluation: ReflectionEvaluation) -> None:
    """把 LLM 評分結果寫回 reflection 物件（不 commit）。"""
    reflection.quality_score = evaluation.quality_score
    reflection.followup_question = evaluation.followup_question


async def create_reflection(
    db: AsyncSession,
    user_id: UUID,
    source_type: ReflectionSourceType,
    source_id: UUID,
    problem_understanding: str,
    planned_steps: list[str],
    expected_concepts: str,
) -> Reflection:
    """建立反思紀錄並觸發 LLM 評分。

    流程：驗證 source → INSERT → LLM 評分 → 寫回 quality_score/followup_question → commit。
    LLM 失敗（fallback 評估）→ quality_score 留 None，不擋寫入。

    Raises:
        AppError 404 REFLECTION_SOURCE_NOT_FOUND — quiz 來源指向不存在的題目
        AppError 409 REFLECTION_ALREADY_EXISTS — 同 (user, source_type, source_id) 已存在
    """
    question = await _validate_source_for_create(db, source_type, source_id)

    reflection = Reflection(
        user_id=user_id,
        source_type=source_type.value,
        source_id=source_id,
        problem_understanding=problem_understanding,
        planned_steps=planned_steps,
        expected_concepts=expected_concepts,
    )
    db.add(reflection)
    try:
        # flush 取得 id 但保留同 transaction
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise AppError(
            409,
            "REFLECTION_ALREADY_EXISTS",
            "此題已存在反思紀錄，請改用 PATCH 更新",
        ) from exc

    evaluation = await evaluate_reflection(reflection, question)
    _apply_evaluation(reflection, evaluation)

    await db.commit()
    await db.refresh(reflection)
    return reflection


async def get_reflection(
    db: AsyncSession, reflection_id: UUID, user_id: UUID
) -> Reflection:
    """取得反思；非本人擁有的回 404（避免列舉攻擊揭露存在性）。"""
    reflection = (
        await db.execute(
            select(Reflection).where(Reflection.id == reflection_id)
        )
    ).scalar_one_or_none()
    if reflection is None or reflection.user_id != user_id:
        raise AppError(
            404,
            "REFLECTION_NOT_FOUND",
            f"找不到反思：{reflection_id}",
        )
    return reflection


async def update_reflection(
    db: AsyncSession,
    reflection_id: UUID,
    user_id: UUID,
    payload: ReflectionUpdate,
) -> Reflection:
    """更新反思。任一內容欄位變動 → `is_modified=True` + 刷新 `updated_at` + 重新評分。

    重評分時機（PRIMM Modify 階段）：
    - 任何「內容類」欄位變動（planned_steps / expected_concepts / followup_answer /
      problem_understanding）都會觸發 LLM 重新評分，因為這些都是學生的反思產出。
    - 若全部欄位都未提供（no-op PATCH）→ 不重評分（避免無謂 LLM 呼叫）。

    Raises:
        AppError 404 REFLECTION_NOT_FOUND
    """
    reflection = await get_reflection(db, reflection_id, user_id)

    changed = False
    if payload.planned_steps is not None:
        reflection.planned_steps = payload.planned_steps
        changed = True
    if payload.expected_concepts is not None:
        reflection.expected_concepts = payload.expected_concepts
        changed = True
    if payload.followup_answer is not None:
        reflection.followup_answer = payload.followup_answer
        changed = True
    if payload.problem_understanding is not None:
        reflection.problem_understanding = payload.problem_understanding
        changed = True

    if changed:
        reflection.is_modified = True
        reflection.updated_at = datetime.now(timezone.utc)
        question = await _load_question_best_effort(db, reflection)
        evaluation = await evaluate_reflection(reflection, question)
        _apply_evaluation(reflection, evaluation)

    await db.commit()
    await db.refresh(reflection)
    return reflection
