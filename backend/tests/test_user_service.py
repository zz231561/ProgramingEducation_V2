"""使用者 service 測試 — 首次登入建立記錄、重複登入更新資訊。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import TokenPayload
from models.user import User, UserRole
from services.user import get_or_create_user
from tests.helpers import TestSessionFactory


SAMPLE_TOKEN = TokenPayload(
    sub="nextauth-id-1",
    email="alice@example.com",
    name="Alice",
    picture="https://example.com/alice.jpg",
    google_id="google-001",
)


async def test_create_user_on_first_login():
    """首次登入應自動建立 DB 記錄。"""
    async with TestSessionFactory() as db:
        user = await get_or_create_user(db, SAMPLE_TOKEN)

        assert user.email == "alice@example.com"
        assert user.name == "Alice"
        assert user.avatar_url == "https://example.com/alice.jpg"
        assert user.google_id == "google-001"
        assert user.role == UserRole.STUDENT
        assert user.last_login_at is not None
        assert user.id is not None


async def test_return_existing_user_on_repeat_login():
    """重複登入應回傳同一筆記錄，不建立新的。"""
    async with TestSessionFactory() as db:
        user1 = await get_or_create_user(db, SAMPLE_TOKEN)
        user2 = await get_or_create_user(db, SAMPLE_TOKEN)

        assert user1.id == user2.id

        result = await db.execute(select(User))
        users = result.scalars().all()
        assert len(users) == 1


async def test_update_profile_on_repeat_login():
    """重複登入應更新 name / avatar_url。"""
    async with TestSessionFactory() as db:
        await get_or_create_user(db, SAMPLE_TOKEN)

        updated_token = TokenPayload(
            sub="nextauth-id-1",
            email="alice@example.com",
            name="Alice Updated",
            picture="https://example.com/alice-new.jpg",
            google_id="google-001",
        )
        user = await get_or_create_user(db, updated_token)

        assert user.name == "Alice Updated"
        assert user.avatar_url == "https://example.com/alice-new.jpg"


async def test_update_last_login_at():
    """重複登入應更新 last_login_at。"""
    async with TestSessionFactory() as db:
        user1 = await get_or_create_user(db, SAMPLE_TOKEN)
        first_login = user1.last_login_at

        user2 = await get_or_create_user(db, SAMPLE_TOKEN)
        assert user2.last_login_at >= first_login


async def test_fallback_to_sub_when_no_google_id():
    """google_id 為 None 時，應以 sub 作為 google_id。"""
    async with TestSessionFactory() as db:
        token = TokenPayload(
            sub="fallback-sub-id",
            email="bob@example.com",
            name="Bob",
            google_id=None,
        )
        user = await get_or_create_user(db, token)
        assert user.google_id == "fallback-sub-id"
