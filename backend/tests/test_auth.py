"""Auth middleware 測試 — JWT 解碼、依賴注入、未登入保護。"""

import pytest
from httpx import AsyncClient

from core.auth import _derive_encryption_key, decode_nextauth_token, TokenPayload
from tests.helpers import encrypt_test_token


SAMPLE_PAYLOAD = {
    "sub": "user-123",
    "email": "test@example.com",
    "name": "Test User",
    "picture": "https://example.com/avatar.jpg",
    "googleId": "google-456",
}


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
    token = encrypt_test_token(SAMPLE_PAYLOAD)
    result = decode_nextauth_token(token)

    assert isinstance(result, TokenPayload)
    assert result.sub == "user-123"
    assert result.email == "test@example.com"
    assert result.name == "Test User"
    assert result.picture == "https://example.com/avatar.jpg"
    assert result.google_id == "google-456"


def test_decode_invalid_token():
    """無效 token 應拋出 401 AppError。"""
    from core.errors import AppError

    with pytest.raises(AppError) as exc_info:
        decode_nextauth_token("invalid.token.value")
    assert exc_info.value.status_code == 401


# === 整合測試：/auth/me 端點 ===

async def test_auth_me_without_token(client: AsyncClient):
    """未帶 token 應回傳 401。"""
    resp = await client.get("/auth/me")
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"] == "UNAUTHORIZED"


async def test_auth_me_with_valid_token(client: AsyncClient):
    """帶合法 cookie 應回傳使用者資訊 + 自動建立 DB 記錄。"""
    token = encrypt_test_token(SAMPLE_PAYLOAD)
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


async def test_auth_me_repeat_returns_same_user(client: AsyncClient):
    """重複呼叫 /auth/me 應回傳同一使用者（不重複建立）。"""
    token = encrypt_test_token(SAMPLE_PAYLOAD)
    resp1 = await client.get("/auth/me", cookies={"authjs.session-token": token})
    resp2 = await client.get("/auth/me", cookies={"authjs.session-token": token})
    assert resp1.json()["id"] == resp2.json()["id"]
