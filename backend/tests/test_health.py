"""Health check 端點測試。"""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
def client():
    """建立不啟動真實 server 的測試 client。"""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_health_returns_ok(client: AsyncClient):
    """GET /health 應回傳 200 + {"status": "ok"}。"""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_not_found_returns_404(client: AsyncClient):
    """不存在的路由應回傳 404。"""
    resp = await client.get("/nonexistent")
    assert resp.status_code == 404
