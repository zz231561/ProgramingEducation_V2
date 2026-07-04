"""Rate limit dependency 測試 — 固定窗口計數、fail-open、未登入 401。"""

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch

from core.errors import AppError, app_error_handler
from core.rate_limit import rate_limit
from tests.helpers import encrypt_test_token


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


SAMPLE_PAYLOAD = {
    "sub": "user-123",
    "email": "test@example.com",
    "name": "Test User",
    "googleId": "google-456",
}


@pytest.fixture
def rl_app() -> FastAPI:
    _app = FastAPI()
    _app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]

    @_app.post("/limited", dependencies=[Depends(rate_limit("test", limit_per_minute=3))])
    async def _limited():
        return {"ok": True}

    return _app


@pytest.fixture
def rl_client(rl_app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=rl_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_rate_limit_allows_within_quota(rl_client: AsyncClient):
    """額度內請求應放行。"""
    token = encrypt_test_token(SAMPLE_PAYLOAD)
    stub = _StubRedis()
    with patch("core.rate_limit.get_redis", return_value=stub):
        for _ in range(3):
            resp = await rl_client.post(
                "/limited", cookies={"authjs.session-token": token}
            )
            assert resp.status_code == 200


async def test_rate_limit_blocks_over_quota(rl_client: AsyncClient):
    """超過額度應回 429 + retry_after_seconds。"""
    token = encrypt_test_token(SAMPLE_PAYLOAD)
    stub = _StubRedis()
    with patch("core.rate_limit.get_redis", return_value=stub):
        for _ in range(3):
            await rl_client.post("/limited", cookies={"authjs.session-token": token})
        resp = await rl_client.post(
            "/limited", cookies={"authjs.session-token": token}
        )

    assert resp.status_code == 429
    body = resp.json()
    assert body["error"] == "RATE_LIMITED"
    assert body["detail"]["retry_after_seconds"] == 30


async def test_rate_limit_fail_open_when_redis_down(rl_client: AsyncClient):
    """Redis 不可用時 fail-open 放行 — 限流是保護，不可反過來擋掉整個服務。"""
    token = encrypt_test_token(SAMPLE_PAYLOAD)
    with patch(
        "core.rate_limit.get_redis", side_effect=RuntimeError("Redis 尚未初始化")
    ):
        resp = await rl_client.post(
            "/limited", cookies={"authjs.session-token": token}
        )
    assert resp.status_code == 200


async def test_rate_limit_requires_auth(rl_client: AsyncClient):
    """未登入應在限流檢查前即回 401。"""
    resp = await rl_client.post("/limited")
    assert resp.status_code == 401


async def test_rate_limit_isolated_per_user(rl_client: AsyncClient):
    """不同使用者各自計數，互不影響。"""
    stub = _StubRedis()
    token_a = encrypt_test_token({**SAMPLE_PAYLOAD, "googleId": "google-aaa"})
    token_b = encrypt_test_token({**SAMPLE_PAYLOAD, "googleId": "google-bbb"})

    with patch("core.rate_limit.get_redis", return_value=stub):
        for _ in range(3):
            await rl_client.post("/limited", cookies={"authjs.session-token": token_a})
        resp_a = await rl_client.post(
            "/limited", cookies={"authjs.session-token": token_a}
        )
        resp_b = await rl_client.post(
            "/limited", cookies={"authjs.session-token": token_b}
        )

    assert resp_a.status_code == 429
    assert resp_b.status_code == 200
