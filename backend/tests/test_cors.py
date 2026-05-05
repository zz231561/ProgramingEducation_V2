"""CORS 測試 — 確認僅允許 NEXTAUTH_URL origin。"""

import pytest
from httpx import ASGITransport, AsyncClient

from core.config import Settings
from main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_cors_allows_configured_origin(client: AsyncClient):
    """NEXTAUTH_URL origin 應被允許。"""
    resp = await client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"


async def test_cors_blocks_unknown_origin(client: AsyncClient):
    """非允許 origin 不應有 ACAO header。"""
    resp = await client.options(
        "/health",
        headers={
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    acao = resp.headers.get("access-control-allow-origin")
    assert acao != "http://evil.com"


# === 4-2c：cors_origins 容錯（trailing slash） ===


def test_cors_origins_strips_trailing_slash():
    """生產 NEXTAUTH_URL 帶尾斜線時 cors_origins 應自動 rstrip。"""
    settings = Settings(NEXTAUTH_URL="https://domain.com/")
    assert settings.cors_origins == ["https://domain.com"]


def test_cors_origins_keeps_no_trailing_slash():
    """無尾斜線情況不應變動。"""
    settings = Settings(NEXTAUTH_URL="https://domain.com")
    assert settings.cors_origins == ["https://domain.com"]


def test_cors_origins_strips_multiple_trailing_slashes():
    """多個尾斜線（極端情況）也清乾淨。"""
    settings = Settings(NEXTAUTH_URL="https://domain.com///")
    assert settings.cors_origins == ["https://domain.com"]
