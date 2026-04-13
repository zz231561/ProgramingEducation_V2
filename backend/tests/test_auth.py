"""Auth middleware 測試 — JWT 解碼、依賴注入、未登入保護。"""

import json
from collections.abc import AsyncGenerator

import pytest
from authlib.jose import JsonWebEncryption
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.auth import _derive_encryption_key, decode_nextauth_token, TokenPayload
from core.config import settings
from core.database import Base, get_db
from main import app


# === 工具函式 ===

def _encrypt_token(payload: dict, secret: str) -> str:
    """模擬 NextAuth v5 加密 token（dir + A256CBC-HS512）。"""
    key = _derive_encryption_key(secret)
    jwe = JsonWebEncryption()
    header = {"alg": "dir", "enc": "A256CBC-HS512"}
    token = jwe.serialize_compact(header, json.dumps(payload).encode(), key)
    return token.decode() if isinstance(token, bytes) else token


SAMPLE_PAYLOAD = {
    "sub": "user-123",
    "email": "test@example.com",
    "name": "Test User",
    "picture": "https://example.com/avatar.jpg",
    "googleId": "google-456",
}


# === 測試用 DB（SQLite in-memory） ===

_test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
_test_session_factory = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def _setup_test_db():
    """每個測試前建立 / 測試後清除 DB schema。"""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _test_session_factory() as session:
        yield session


# 覆蓋 app 的 DB 依賴
app.dependency_overrides[get_db] = _override_get_db


# === 單元測試：金鑰衍生 ===

def test_derive_key_deterministic():
    """相同 secret 應產生相同金鑰。"""
    k1 = _derive_encryption_key("test-secret")
    k2 = _derive_encryption_key("test-secret")
    assert k1 == k2
    assert len(k1) == 64


def test_derive_key_different_secrets():
    """不同 secret 應產生不同金鑰。"""
    k1 = _derive_encryption_key("secret-a")
    k2 = _derive_encryption_key("secret-b")
    assert k1 != k2


# === 單元測試：token 解碼 ===

def test_decode_valid_token():
    """合法 token 應正確解碼。"""
    secret = settings.NEXTAUTH_SECRET or "test-secret-for-ci"
    token = _encrypt_token(SAMPLE_PAYLOAD, secret)

    original = settings.NEXTAUTH_SECRET
    settings.NEXTAUTH_SECRET = secret

    import core.auth
    core.auth._encryption_key = None

    try:
        result = decode_nextauth_token(token)
        assert isinstance(result, TokenPayload)
        assert result.sub == "user-123"
        assert result.email == "test@example.com"
        assert result.name == "Test User"
        assert result.picture == "https://example.com/avatar.jpg"
        assert result.google_id == "google-456"
    finally:
        settings.NEXTAUTH_SECRET = original
        core.auth._encryption_key = None


def test_decode_invalid_token():
    """無效 token 應拋出 401 AppError。"""
    from core.errors import AppError

    with pytest.raises(AppError) as exc_info:
        decode_nextauth_token("invalid.token.value")
    assert exc_info.value.status_code == 401


# === 整合測試：/auth/me 端點 ===

@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_auth_me_without_token(client: AsyncClient):
    """未帶 token 應回傳 401。"""
    resp = await client.get("/auth/me")
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"] == "UNAUTHORIZED"


async def test_auth_me_with_valid_token(client: AsyncClient):
    """帶合法 cookie 應回傳使用者資訊 + 自動建立 DB 記錄。"""
    secret = "test-secret-for-auth-me"
    token = _encrypt_token(SAMPLE_PAYLOAD, secret)

    import core.auth
    original = settings.NEXTAUTH_SECRET
    settings.NEXTAUTH_SECRET = secret
    core.auth._encryption_key = None

    try:
        resp = await client.get(
            "/auth/me",
            cookies={"authjs.session-token": token},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "test@example.com"
        assert body["name"] == "Test User"
        assert body["role"] == "student"
        assert "id" in body
    finally:
        settings.NEXTAUTH_SECRET = original
        core.auth._encryption_key = None


async def test_auth_me_repeat_returns_same_user(client: AsyncClient):
    """重複呼叫 /auth/me 應回傳同一使用者（不重複建立）。"""
    secret = "test-secret-for-repeat"
    token = _encrypt_token(SAMPLE_PAYLOAD, secret)

    import core.auth
    original = settings.NEXTAUTH_SECRET
    settings.NEXTAUTH_SECRET = secret
    core.auth._encryption_key = None

    try:
        resp1 = await client.get("/auth/me", cookies={"authjs.session-token": token})
        resp2 = await client.get("/auth/me", cookies={"authjs.session-token": token})
        assert resp1.json()["id"] == resp2.json()["id"]
    finally:
        settings.NEXTAUTH_SECRET = original
        core.auth._encryption_key = None
