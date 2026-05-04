"""Reflection CRUD service — 純資料操作層（roadmap 2-5a）。

職責邊界：
- 本層只做 schema 驗證 + DB 讀寫；LLM 品質評分 / 追問生成 留給 2-5b。
- `source_id` 對 `quiz` 來源驗證指向 questions 表存在；`learning_unit` 來源
  因 learning_units 表尚未建立（Phase 3-1a），暫不驗證，由 caller 負責。
- 重複建立同一份反思（UNIQUE 衝突）回 409 而非 500。
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


@dataclass(slots=True)
class ReflectionUpdate:
    """PATCH 反思時可更新的欄位（皆為 nullable，未提供者保留原值）。"""

    planned_steps: list[str] | None = None
    expected_concepts: str | None = None
    followup_answer: str | None = None
    problem_understanding: str | None = None


async def _validate_source(
    db: AsyncSession, source_type: ReflectionSourceType, source_id: UUID
) -> None:
    """確認 source_id 指向有效對象。learning_unit 暫不驗證（表尚未建立）。"""
    if source_type is ReflectionSourceType.QUIZ:
        exists = (
            await db.execute(select(Question.id).where(Question.id == source_id))
        ).scalar_one_or_none()
        if exists is None:
            raise AppError(
                404,
                "REFLECTION_SOURCE_NOT_FOUND",
                f"找不到題目：{source_id}",
            )


async def create_reflection(
    db: AsyncSession,
    user_id: UUID,
    source_type: ReflectionSourceType,
    source_id: UUID,
    problem_understanding: str,
    planned_steps: list[str],
    expected_concepts: str,
) -> Reflection:
    """建立反思紀錄。

    Raises:
        AppError 404 REFLECTION_SOURCE_NOT_FOUND — quiz 來源指向不存在的題目
        AppError 409 REFLECTION_ALREADY_EXISTS — 同 (user, source_type, source_id) 已存在
    """
    await _validate_source(db, source_type, source_id)

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
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise AppError(
            409,
            "REFLECTION_ALREADY_EXISTS",
            "此題已存在反思紀錄，請改用 PATCH 更新",
        ) from exc
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
    """更新反思。任一欄位變動即將 `is_modified=True` 並刷新 `updated_at`。

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

    await db.commit()
    await db.refresh(reflection)
    return reflection
