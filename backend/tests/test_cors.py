"""CORS 測試 — 確認僅允許 NEXTAUTH_URL origin。"""

import pytest
from httpx import ASGITransport, AsyncClient

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
