"""班級管理 service — 教師端 CRUD（roadmap 5-1b-2）。

- 邀請碼：6 位數字（含前導零），以 `secrets` 產生避免可預測；DB unique
  約束把關，碰撞則重試。
- 授權：教師僅能操作自己建立的班級；他人班級一律回 404（不洩漏存在性，
  比照 reflection 的 other-user 慣例）。
"""

import secrets
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.classroom import ClassMember, Classroom

INVITE_CODE_LENGTH = 6
_INVITE_CODE_CEIL = 10**INVITE_CODE_LENGTH
_MAX_CODE_RETRIES = 10


async def _generate_unique_invite_code(db: AsyncSession) -> str:
    """產生未被使用的 6 位數字邀請碼（前導零保留）。"""
    for _ in range(_MAX_CODE_RETRIES):
        code = f"{secrets.randbelow(_INVITE_CODE_CEIL):0{INVITE_CODE_LENGTH}d}"
        exists = await db.scalar(
            select(Classroom.id).where(Classroom.invite_code == code)
        )
        if exists is None:
            return code
    # 10 次仍撞碼在 100 萬碼空間下機率趨近於零，視為系統異常
    raise AppError(503, "INVITE_CODE_UNAVAILABLE", "邀請碼產生失敗，請重試")


async def create_classroom(
    db: AsyncSession, *, teacher_id: uuid.UUID, name: str
) -> Classroom:
    """建立班級並配發唯一邀請碼。"""
    code = await _generate_unique_invite_code(db)
    classroom = Classroom(name=name, teacher_id=teacher_id, invite_code=code)
    db.add(classroom)
    await db.commit()
    await db.refresh(classroom)
    return classroom


async def list_classrooms(
    db: AsyncSession, teacher_id: uuid.UUID
) -> list[tuple[Classroom, int]]:
    """列出教師自己的班級 + 各班成員數（建立時間新到舊）。"""
    stmt = (
        select(Classroom, func.count(ClassMember.user_id))
        .outerjoin(ClassMember, ClassMember.class_id == Classroom.id)
        .where(Classroom.teacher_id == teacher_id)
        .group_by(Classroom.id)
        .order_by(Classroom.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [(row[0], row[1]) for row in rows]


async def update_classroom(
    db: AsyncSession,
    *,
    class_id: uuid.UUID,
    teacher_id: uuid.UUID,
    name: str | None = None,
    is_active: bool | None = None,
) -> Classroom:
    """更新班級名稱 / 啟用狀態（僅擁有者，否則 404）。"""
    classroom = await _get_owned_classroom(db, class_id, teacher_id)
    if name is not None:
        classroom.name = name
    if is_active is not None:
        classroom.is_active = is_active
    await db.commit()
    await db.refresh(classroom)
    return classroom


async def _get_owned_classroom(
    db: AsyncSession, class_id: uuid.UUID, teacher_id: uuid.UUID
) -> Classroom:
    """取得班級並確認屬於該教師；否則 404。"""
    classroom = await db.get(Classroom, class_id)
    if classroom is None or classroom.teacher_id != teacher_id:
        raise AppError(404, "CLASS_NOT_FOUND", "班級不存在")
    return classroom
