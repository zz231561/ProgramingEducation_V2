"""開發者模式 gating 測試（DEV-1）— 白名單判定、status 端點、rate limit 豁免。"""

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch

from core.config import settings
from core.dev_mode import is_dev_email
from core.errors import AppError, app_error_handler
from core.rate_limit import rate_limit
from tests.helpers import encrypt_test_token

DEV_EMAIL = "dev@test.com"

DEV_PAYLOAD = {
    "sub": "dev-user",
    "email": DEV_EMAIL,
    "name": "Dev Tester",
    "googleId": "g-dev-user",
}

STUDENT_PAYLOAD = {
    "sub": "normal-user",
    "email": "student@test.com",
    "name": "Normal Tester",
    "googleId": "g-normal-user",
}


@pytest.fixture
def dev_mode_on(monkeypatch):
    monkeypatch.setattr(settings, "DEV_MODE_ENABLED", True)
    monkeypatch.setattr(settings, "DEV_MODE_EMAILS", DEV_EMAIL)


# === is_dev_email 單元 ===

def test_is_dev_email_disabled_by_default(monkeypatch):
    """總開關關閉時，白名單命中也一律 False。"""
    monkeypatch.setattr(settings, "DEV_MODE_ENABLED", False)
    monkeypatch.setattr(settings, "DEV_MODE_EMAILS", DEV_EMAIL)
    assert is_dev_email(DEV_EMAIL) is False


def test_is_dev_email_matching(dev_mode_on):
    assert is_dev_email(DEV_EMAIL) is True


def test_is_dev_email_case_and_whitespace_insensitive(dev_mode_on):
    assert is_dev_email("  DEV@Test.Com ") is True


def test_is_dev_email_non_matching(dev_mode_on):
    assert is_dev_email("student@test.com") is False
    assert is_dev_email("") is False
    assert is_dev_email(None) is False


def test_dev_mode_emails_parses_csv(monkeypatch):
    monkeypatch.setattr(settings, "DEV_MODE_EMAILS", "a@x.com, B@Y.com ,, ")
    assert settings.dev_mode_emails == {"a@x.com", "b@y.com"}


# === GET /dev/status ===

@pytest.mark.asyncio
async def test_dev_status_requires_auth(client: AsyncClient):
    resp = await client.get("/dev/status")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_dev_status_true_for_dev_account(client: AsyncClient, dev_mode_on):
    token = encrypt_test_token(DEV_PAYLOAD)
    resp = await client.get(
        "/dev/status", cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    assert resp.json() == {"is_dev": True}


@pytest.mark.asyncio
async def test_dev_status_false_for_normal_account(client: AsyncClient, dev_mode_on):
    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.get(
        "/dev/status", cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    assert resp.json() == {"is_dev": False}


@pytest.mark.asyncio
async def test_dev_status_false_when_disabled(client: AsyncClient, monkeypatch):
    """生產保險：開關關閉時 dev 帳號也不是 dev。"""
    monkeypatch.setattr(settings, "DEV_MODE_ENABLED", False)
    monkeypatch.setattr(settings, "DEV_MODE_EMAILS", DEV_EMAIL)
    token = encrypt_test_token(DEV_PAYLOAD)
    resp = await client.get(
        "/dev/status", cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    assert resp.json() == {"is_dev": False}


# === Rate limit 豁免 ===

class _StubRedis:
    """最小 Redis stub — 只實作 rate limit 用到的 incr / expire / ttl。"""

    def __init__(self) -> None:
        self.store: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    async def expire(self, key: str, ttl: int) -> None:
        pass

    async def ttl(self, key: str) -> int:
        return 30


@pytest.fixture
def rl_app() -> FastAPI:
    _app = FastAPI()
    _app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]

    @_app.get("/probe", dependencies=[Depends(rate_limit("probe", 1))])
    async def probe() -> dict:
        return {"ok": True}

    return _app


@pytest.mark.asyncio
async def test_rate_limit_exempts_dev_account(rl_app: FastAPI, dev_mode_on):
    """dev 帳號超過額度也不 429（且不寫入 Redis 計數）。"""
    stub = _StubRedis()
    token = encrypt_test_token(DEV_PAYLOAD)
    async with AsyncClient(
        transport=ASGITransport(app=rl_app), base_url="http://test",
    ) as ac:
        with patch("core.rate_limit.get_redis", return_value=stub):
            for _ in range(3):
                resp = await ac.get(
                    "/probe", cookies={"authjs.session-token": token},
                )
                assert resp.status_code == 200
    assert stub.store == {}


@pytest.mark.asyncio
async def test_rate_limit_still_applies_to_normal_account(rl_app: FastAPI, dev_mode_on):
    """非 dev 帳號限流行為不變（limit=1 → 第二次 429）。"""
    stub = _StubRedis()
    token = encrypt_test_token(STUDENT_PAYLOAD)
    async with AsyncClient(
        transport=ASGITransport(app=rl_app), base_url="http://test",
    ) as ac:
        with patch("core.rate_limit.get_redis", return_value=stub):
            first = await ac.get(
                "/probe", cookies={"authjs.session-token": token},
            )
            second = await ac.get(
                "/probe", cookies={"authjs.session-token": token},
            )
    assert first.status_code == 200
    assert second.status_code == 429
