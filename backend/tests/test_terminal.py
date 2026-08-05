"""終端 ticket 發放 + WS 中繼測試（runner 端以 fake WS 模擬）。"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from main import app
from tests.helpers import encrypt_test_token

USER = {"sub": "term-a", "email": "term@ex.com", "name": "T", "googleId": "g-term-a"}
_CK = {"authjs.session-token": encrypt_test_token(USER)}
_UID = str(uuid.uuid4())


class _StubRedis:
    def __init__(self, store: dict | None = None):
        self.store = store if store is not None else {}

    async def setex(self, key, ttl, value):
        self.store[key] = value

    async def getdel(self, key):
        return self.store.pop(key, None)


def _set_runner(monkeypatch):
    from core.config import settings

    monkeypatch.setattr(settings, "RUNNER_BACKEND", "self")
    monkeypatch.setattr(settings, "RUNNER_URL", "http://runner.internal:8080")
    monkeypatch.setattr(settings, "RUNNER_TOKEN", "tok")


# === POST /terminal/ticket ===


async def test_ticket_503_when_runner_disabled(client: AsyncClient, monkeypatch):
    from core.config import settings

    monkeypatch.setattr(settings, "RUNNER_URL", "")
    resp = await client.post("/terminal/ticket", cookies=_CK)
    assert resp.status_code == 503
    assert resp.json()["error"] == "RUNNER_UNAVAILABLE"


async def test_ticket_issued_and_stored(client: AsyncClient, monkeypatch):
    _set_runner(monkeypatch)
    stub = _StubRedis()
    with patch("api.routes.terminal.get_redis", return_value=stub):
        resp = await client.post("/terminal/ticket", cookies=_CK)
    assert resp.status_code == 200
    ticket = resp.json()["ticket"]
    assert stub.store[f"terminal:ticket:{ticket}"]  # 存了 user id


async def test_ticket_requires_auth(client: AsyncClient, monkeypatch):
    _set_runner(monkeypatch)
    resp = await client.post("/terminal/ticket")
    assert resp.status_code == 401


# === WS /terminal/ws ===


class _FakeRunnerWS:
    """模擬 runner 端 WS：記錄收到的 frame，照腳本回放輸出。"""

    def __init__(self, frames: list[dict]):
        self.sent: list[dict] = []
        self._frames = frames

    async def send(self, raw: str):
        self.sent.append(json.loads(raw))

    def __aiter__(self):
        async def gen():
            for f in self._frames:
                yield json.dumps(f)

        return gen()


def _fake_connect(fake_ws):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=fake_ws)
    cm.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=cm)


def test_ws_invalid_ticket_rejected():
    stub = _StubRedis()  # 空 store → getdel 回 None
    tc = TestClient(app)
    with patch("api.routes.terminal.get_redis", return_value=stub):
        with tc.websocket_connect("/terminal/ws") as ws:
            ws.send_json({"type": "start", "ticket": "bogus", "code": "int main(){}"})
            frame = ws.receive_json()
    assert frame == {"type": "error", "code": "UNAUTHORIZED"}


def test_ws_relay_forwards_frames_and_logs():
    stub = _StubRedis({"terminal:ticket:t1": _UID})
    fake = _FakeRunnerWS(
        [
            {"type": "compiling"},
            {"type": "started"},
            {"type": "output", "data": "hi\r\n"},
            {
                "type": "exit",
                "exit_code": 0,
                "status_description": "Accepted",
                "time": "1.234",
                "output_summary": "hi\r\n",
            },
        ]
    )
    log = AsyncMock()
    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=MagicMock())
    session_cm.__aexit__ = AsyncMock(return_value=False)
    tc = TestClient(app)
    with (
        patch("api.routes.terminal.get_redis", return_value=stub),
        patch("api.routes.terminal.websockets.connect", _fake_connect(fake)),
        patch("api.routes.terminal.async_session", MagicMock(return_value=session_cm)),
        patch("api.routes.terminal.log_execution", log),
    ):
        with tc.websocket_connect("/terminal/ws") as ws:
            ws.send_json(
                {"type": "start", "ticket": "t1", "code": "int main(){}", "args": "a"}
            )
            frames = [ws.receive_json() for _ in range(4)]

    assert [f["type"] for f in frames] == ["compiling", "started", "output", "exit"]
    # start frame 轉發給 runner（不含 ticket）
    assert fake.sent[0] == {"type": "start", "code": "int main(){}", "args": "a"}
    # 行為事件：以 exit frame 建 ExecutionResult
    log.assert_awaited_once()
    result = log.await_args.kwargs["result"]
    assert result.status_description == "Accepted"
    assert result.stdout == "hi\r\n"
    assert log.await_args.kwargs["user_id"] == uuid.UUID(_UID)


def test_ws_ticket_single_use():
    stub = _StubRedis({"terminal:ticket:t1": _UID})
    fake = _FakeRunnerWS([{"type": "exit", "status_description": "Accepted"}])
    tc = TestClient(app)
    with (
        patch("api.routes.terminal.get_redis", return_value=stub),
        patch("api.routes.terminal.websockets.connect", _fake_connect(fake)),
        patch("api.routes.terminal._log_session", AsyncMock()),
    ):
        with tc.websocket_connect("/terminal/ws") as ws:
            ws.send_json({"type": "start", "ticket": "t1", "code": "int main(){}"})
            ws.receive_json()
        # 同一 ticket 再用一次 → 拒絕
        with tc.websocket_connect("/terminal/ws") as ws:
            ws.send_json({"type": "start", "ticket": "t1", "code": "int main(){}"})
            frame = ws.receive_json()
    assert frame == {"type": "error", "code": "UNAUTHORIZED"}


def test_ws_runner_connect_failure_reports_error():
    stub = _StubRedis({"terminal:ticket:t1": _UID})
    boom = MagicMock(side_effect=OSError("refused"))
    tc = TestClient(app)
    with (
        patch("api.routes.terminal.get_redis", return_value=stub),
        patch("api.routes.terminal.websockets.connect", boom),
    ):
        with tc.websocket_connect("/terminal/ws") as ws:
            ws.send_json({"type": "start", "ticket": "t1", "code": "int main(){}"})
            frame = ws.receive_json()
    assert frame == {"type": "error", "code": "RUNNER_UNAVAILABLE"}
