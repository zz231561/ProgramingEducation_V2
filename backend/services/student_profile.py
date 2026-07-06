"""學生身分 profile service — 提交 / 查詢（roadmap 5-1b-3）。

Google OAuth 顯示名不一定是真名，故學生需補填 school / department /
student_id / real_name；email 沿用 users。以 user_id 為主鍵做 upsert。
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.student_profile import StudentProfile


async def get_profile(db: AsyncSession, user_id: uuid.UUID) -> StudentProfile | None:
    """取得學生 profile；未填回 None（由 caller 決定 404 或引導填寫）。"""
    return await db.get(StudentProfile, user_id)


async def upsert_profile(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    school: str,
    department: str,
    student_id: str,
    real_name: str,
) -> StudentProfile:
    """建立或更新學生 profile（存在則覆蓋欄位，updated_at 自動更新）。"""
    profile = await db.get(StudentProfile, user_id)
    if profile is None:
        profile = StudentProfile(user_id=user_id)
        db.add(profile)
    profile.school = school
    profile.department = department
    profile.student_id = student_id
    profile.real_name = real_name
    await db.commit()
    await db.refresh(profile)
    return profile
