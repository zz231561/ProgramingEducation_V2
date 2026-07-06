"""學生身分 profile API（roadmap 5-1b-3）。

- GET  /profile   — 取得自己的身分資料（未填回 404 供前端引導）
- POST /profile   — 提交/更新身分資料（upsert）

email 沿用 users，不由前端提交；僅登入使用者可操作自己的 profile。
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from core.errors import AppError
from models.student_profile import StudentProfile
from models.user import User
from services.student_profile import get_profile, upsert_profile

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileRequest(BaseModel):
    school: str = Field(..., min_length=1, max_length=100)
    department: str = Field(..., min_length=1, max_length=100)
    student_id: str = Field(..., min_length=1, max_length=50)
    real_name: str = Field(..., min_length=1, max_length=100)


class ProfileOut(BaseModel):
    school: str
    department: str
    student_id: str
    real_name: str
    email: str

    @classmethod
    def from_model(cls, p: StudentProfile, email: str) -> "ProfileOut":
        return cls(
            school=p.school,
            department=p.department,
            student_id=p.student_id,
            real_name=p.real_name,
            email=email,
        )


@router.get("", response_model=ProfileOut)
async def get_own(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> ProfileOut:
    profile = await get_profile(db, user.id)
    if profile is None:
        raise AppError(404, "PROFILE_NOT_FOUND", "尚未填寫個人身分資料")
    return ProfileOut.from_model(profile, user.email)


@router.post("", response_model=ProfileOut)
async def submit(
    body: ProfileRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> ProfileOut:
    profile = await upsert_profile(
        db,
        user_id=user.id,
        school=body.school,
        department=body.department,
        student_id=body.student_id,
        real_name=body.real_name,
    )
    return ProfileOut.from_model(profile, user.email)
