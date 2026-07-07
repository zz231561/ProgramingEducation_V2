"""作業 CRUD service（5-5a-2）— 教師端建立 / 列出 / 取得 / 編輯 / 刪除。

授權：教師僅能操作自己班級的作業；他人一律 404（不洩漏存在性，比照 classroom 慣例）。
編輯支援 due_at 清空——用 UNSET 哨兵區分「未提供（不動）」與「明確設為 null（清除截止）」。
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.assignment import Assignment, AssignmentSubmission, Attachment
from models.classroom import Classroom

# 哨兵：PATCH 時區分「欄位未提供」與「明確設為 None」
UNSET: Any = object()


async def _get_owned_class(
    db: AsyncSession, class_id: uuid.UUID, teacher_id: uuid.UUID
) -> Classroom:
    cls = await db.get(Classroom, class_id)
    if cls is None or cls.teacher_id != teacher_id:
        raise AppError(404, "CLASS_NOT_FOUND", "班級不存在")
    return cls


async def _get_owned_assignment(
    db: AsyncSession, assignment_id: uuid.UUID, teacher_id: uuid.UUID
) -> Assignment:
    a = await db.get(Assignment, assignment_id)
    if a is None or a.teacher_id != teacher_id:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "作業不存在")
    return a


async def create_assignment(
    db: AsyncSession,
    *,
    teacher_id: uuid.UUID,
    class_id: uuid.UUID,
    title: str,
    description: str = "",
    due_at: datetime | None = None,
) -> Assignment:
    """建立作業（須為班級擁有者）。"""
    await _get_owned_class(db, class_id, teacher_id)
    a = Assignment(
        class_id=class_id, teacher_id=teacher_id, title=title,
        description=description, due_at=due_at,
    )
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return a


async def list_assignments(
    db: AsyncSession, *, teacher_id: uuid.UUID, class_id: uuid.UUID | None = None
) -> list[Assignment]:
    """列出教師的作業（可選班級過濾），建立時間新到舊。"""
    stmt = select(Assignment).where(Assignment.teacher_id == teacher_id)
    if class_id is not None:
        stmt = stmt.where(Assignment.class_id == class_id)
    stmt = stmt.order_by(Assignment.created_at.desc())
    return list((await db.execute(stmt)).scalars())


async def get_assignment(
    db: AsyncSession, *, teacher_id: uuid.UUID, assignment_id: uuid.UUID
) -> Assignment:
    """取得單一作業（僅擁有者）。"""
    return await _get_owned_assignment(db, assignment_id, teacher_id)


async def update_assignment(
    db: AsyncSession,
    *,
    teacher_id: uuid.UUID,
    assignment_id: uuid.UUID,
    title: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
    due_at: Any = UNSET,
) -> Assignment:
    """編輯作業內容 / 截止時間 / 啟用狀態（None 或 UNSET＝不動；due_at 可設 None 清除）。"""
    a = await _get_owned_assignment(db, assignment_id, teacher_id)
    if title is not None:
        a.title = title
    if description is not None:
        a.description = description
    if is_active is not None:
        a.is_active = is_active
    if due_at is not UNSET:
        a.due_at = due_at
    await db.commit()
    await db.refresh(a)
    return a


async def delete_assignment(
    db: AsyncSession, *, teacher_id: uuid.UUID, assignment_id: uuid.UUID
) -> None:
    """刪除作業 + 其繳交 + 全部附件（多型附件無 FK cascade，顯式清理）。"""
    a = await _get_owned_assignment(db, assignment_id, teacher_id)
    sub_ids = list(
        (
            await db.execute(
                select(AssignmentSubmission.id).where(
                    AssignmentSubmission.assignment_id == assignment_id
                )
            )
        ).scalars()
    )
    owner_ids = [assignment_id, *sub_ids]
    await db.execute(delete(Attachment).where(Attachment.owner_id.in_(owner_ids)))
    await db.execute(
        delete(AssignmentSubmission).where(
            AssignmentSubmission.assignment_id == assignment_id
        )
    )
    await db.delete(a)
    await db.commit()
