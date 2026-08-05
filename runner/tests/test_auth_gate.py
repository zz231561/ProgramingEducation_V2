"""認證與並行閘測試。"""

import asyncio

import httpx
import pytest

from app.gate import Gate, QueueTimeout
from app.main import app


async def _client_with(headers: dict):
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://runner.test",
        headers=headers,
    )


async def test_missing_token_rejected():
    async with await _client_with({}) as c:
        resp = await c.post("/run", json={"code": "int main(){}"})
    assert resp.status_code == 401


async def test_wrong_token_rejected():
    async with await _client_with({"X-Runner-Token": "nope"}) as c:
        resp = await c.post("/run", json={"code": "int main(){}"})
    assert resp.status_code == 401


async def test_healthz_no_token(client):
    async with await _client_with({}) as c:
        resp = await c.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["sandbox"] == "none"


async def test_gate_queue_timeout(monkeypatch):
    from app.config import settings

    # 0.05s：holder 取空閒 slot 綽綽有餘，排隊者則快速逾時
    monkeypatch.setattr(settings, "gate_slots", 1)
    monkeypatch.setattr(settings, "gate_queue_timeout", 0.05)
    gate = Gate()

    async def hold():
        async with gate.slot():
            await asyncio.sleep(0.5)

    holder = asyncio.create_task(hold())
    await asyncio.sleep(0.05)  # 確保 slot 已被佔住
    with pytest.raises(QueueTimeout):
        async with gate.slot():
            pass
    await holder


async def test_gate_position_tracking(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "gate_slots", 1)
    gate = Gate()
    positions: list[int] = []

    async def hold():
        async with gate.slot():
            await asyncio.sleep(0.2)

    async def wait_and_record():
        async with gate.slot(on_wait=positions.append):
            pass

    holder = asyncio.create_task(hold())
    await asyncio.sleep(0.05)
    await wait_and_record()
    await holder
    assert positions == [1]  # 排在第 1 位
