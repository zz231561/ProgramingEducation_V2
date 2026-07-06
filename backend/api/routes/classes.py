"""班級管理 API — 教師端 CRUD（roadmap 5-1b-2）。

- POST   /classes         — 建立班級（回傳 6 位數字邀請碼）
- GET    /classes         — 列出教師自己的班級（含成員數）
- PATCH  /classes/{id}    — 更新名稱 / 停用班級

全端點以 require_roles(TEACHER) gating；學生加入班級與名冊查詢屬 5-1b-3。
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, require_roles
from models.classroom import Classroom
from models.user import User, UserRole
from services.classroom import (
    create_classroom,
    list_classrooms,
    update_classroom,
)

router = APIRouter(prefix="/classes", tags=["classes"])

_teacher = require_roles(UserRole.TEACHER)


# === Schemas ===


class CreateClassRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class PatchClassRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None


class ClassOut(BaseModel):
    id: uuid.UUID
    name: str
    invite_code: str
    is_active: bool
    member_count: int
    created_at: str

    @classmethod
    def from_model(cls, c: Classroom, member_count: int = 0) -> "ClassOut":
        return cls(
            id=c.id,
            name=c.name,
            invite_code=c.invite_code,
            is_active=c.is_active,
            member_count=member_count,
            created_at=c.created_at.isoformat(),
        )


# === Endpoints ===


@router.post("", response_model=ClassOut, status_code=201)
async def create(
    body: CreateClassRequest,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(_teacher),
) -> ClassOut:
    classroom = await create_classroom(db, teacher_id=teacher.id, name=body.name)
    return ClassOut.from_model(classroom)


@router.get("", response_model=list[ClassOut])
async def list_own(
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(_teacher),
) -> list[ClassOut]:
    rows = await list_classrooms(db, teacher.id)
    return [ClassOut.from_model(c, count) for c, count in rows]


@router.patch("/{class_id}", response_model=ClassOut)
async def patch(
    class_id: uuid.UUID,
    body: PatchClassRequest,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(_teacher),
) -> ClassOut:
    classroom = await update_classroom(
        db,
        class_id=class_id,
        teacher_id=teacher.id,
        name=body.name,
        is_active=body.is_active,
    )
    return ClassOut.from_model(classroom)
