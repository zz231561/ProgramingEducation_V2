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

from api.deps import get_current_db_user, get_db, require_roles
from models.classroom import Classroom
from models.student_profile import StudentProfile
from models.user import User, UserRole
from services.classroom import (
    create_classroom,
    join_class,
    list_classrooms,
    list_joined_classes,
    list_members,
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


class JoinClassRequest(BaseModel):
    invite_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class MemberOut(BaseModel):
    user_id: uuid.UUID
    email: str
    real_name: str | None
    school: str | None
    department: str | None
    student_id: str | None

    @classmethod
    def from_row(cls, user: User, profile: StudentProfile | None) -> "MemberOut":
        return cls(
            user_id=user.id,
            email=user.email,
            real_name=profile.real_name if profile else None,
            school=profile.school if profile else None,
            department=profile.department if profile else None,
            student_id=profile.student_id if profile else None,
        )


class MyClassOut(BaseModel):
    """學生視角的班級資訊（不含邀請碼/成員數等教師端欄位）。"""

    id: uuid.UUID
    name: str
    teacher_name: str
    joined_at: str


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


@router.get("/mine", response_model=list[MyClassOut])
async def list_mine(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> list[MyClassOut]:
    """學生列出自己已加入的班級（依加入時間排序）。"""
    rows = await list_joined_classes(db, user_id=user.id)
    return [
        MyClassOut(
            id=c.id, name=c.name, teacher_name=teacher_name,
            joined_at=joined_at.isoformat(),
        )
        for c, teacher_name, joined_at in rows
    ]


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


@router.post("/join", response_model=ClassOut, status_code=200)
async def join(
    body: JoinClassRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> ClassOut:
    """學生以邀請碼加入班級（idempotent）；未填 profile 回 409 PROFILE_REQUIRED。"""
    classroom = await join_class(db, user_id=user.id, invite_code=body.invite_code)
    return ClassOut.from_model(classroom)


@router.get("/{class_id}/members", response_model=list[MemberOut])
async def members(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(_teacher),
) -> list[MemberOut]:
    """教師查看班級名冊（僅擁有者，否則 404）。"""
    rows = await list_members(db, class_id=class_id, teacher_id=teacher.id)
    return [MemberOut.from_row(u, p) for u, p in rows]
