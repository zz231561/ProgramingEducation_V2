"""Health check 端點測試。"""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
def client():
    """建立不啟動真實 server 的測試 client。"""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_health_returns_200(client: AsyncClient):
    """GET /health 應回傳 200 並包含 status 與 services。"""
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert "services" in body
    assert "database" in body["services"]
    assert "redis" in body["services"]


async def test_health_degraded_without_services(client: AsyncClient):
    """無 DB/Redis 連線時，status 應為 degraded。"""
    resp = await client.get("/health")
    body = resp.json()
    # 測試環境無真實 DB/Redis，預期 degraded
    assert body["status"] == "degraded"
    assert body["services"]["database"] == "disconnected"
    assert body["services"]["redis"] == "disconnected"


async def test_not_found_returns_404(client: AsyncClient):
    """不存在的路由應回傳 404。"""
    resp = await client.get("/nonexistent")
    assert resp.status_code == 404
