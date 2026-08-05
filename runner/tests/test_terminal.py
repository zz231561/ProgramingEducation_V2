"""WS /terminal 測試 — 真實 PTY 互動（starlette TestClient）。"""

from fastapi.testclient import TestClient

from app.main import app

HDRS = {"X-Runner-Token": "test-token"}

ECHO_NAME = (
    "#include <iostream>\n#include <string>\nusing namespace std;\n"
    'int main(){ cout << "name: "; string n; cin >> n;'
    ' cout << "hi " << n << endl; return 0; }\n'
)


def _drain_until(ws, frame_type: str, limit: int = 50) -> tuple[dict, list[dict]]:
    """收 frame 直到指定型別；回傳 (該 frame, 沿途全部 frames)。"""
    seen: list[dict] = []
    for _ in range(limit):
        frame = ws.receive_json()
        seen.append(frame)
        if frame["type"] == frame_type:
            return frame, seen
    raise AssertionError(f"never saw {frame_type}: {seen}")


def _output_text(frames: list[dict]) -> str:
    return "".join(f["data"] for f in frames if f["type"] == "output")


def test_non_interactive_program_runs_to_exit():
    client = TestClient(app)
    code = '#include <iostream>\nint main(){ std::cout << "plain done"; return 0; }\n'
    with client.websocket_connect("/terminal", headers=HDRS) as ws:
        ws.send_json({"type": "start", "code": code})
        exit_frame, seen = _drain_until(ws, "exit")
    assert exit_frame["status_description"] == "Accepted"
    assert exit_frame["exit_code"] == 0
    assert "plain done" in _output_text(seen)
    assert "plain done" in exit_frame["output_summary"]


def test_interactive_stdin_roundtrip():
    """PTY 關鍵驗證：無 endl 的提示字先出現 → 送輸入 → 得到回應。"""
    client = TestClient(app)
    with client.websocket_connect("/terminal", headers=HDRS) as ws:
        ws.send_json({"type": "start", "code": ECHO_NAME})
        # 等到提示字出現（行緩衝：PTY 下應在 cin 阻塞前就送到）
        collected = ""
        for _ in range(50):
            frame = ws.receive_json()
            if frame["type"] == "output":
                collected += frame["data"]
                if "name:" in collected:
                    break
        assert "name:" in collected
        ws.send_json({"type": "stdin", "data": "Alice\r"})
        exit_frame, seen = _drain_until(ws, "exit")
    assert exit_frame["status_description"] == "Accepted"
    assert "hi Alice" in collected + _output_text(seen)


def test_compile_error_frame():
    client = TestClient(app)
    with client.websocket_connect("/terminal", headers=HDRS) as ws:
        ws.send_json({"type": "start", "code": "int main(){ broken"})
        frame, _ = _drain_until(ws, "compile_error")
    assert frame["output"] != ""
    assert frame["status_description"] == "Compilation Error"


def test_idle_timeout_kills_session(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "session_idle_seconds", 1)
    client = TestClient(app)
    with client.websocket_connect("/terminal", headers=HDRS) as ws:
        # 程式等輸入但從不送 → idle 看門狗收掉
        ws.send_json({"type": "start", "code": ECHO_NAME})
        exit_frame, _ = _drain_until(ws, "exit")
    assert exit_frame["status_description"] == "Session Idle Timeout"
    assert exit_frame["exit_code"] is None


def test_session_limit(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "max_sessions", 0)
    client = TestClient(app)
    with client.websocket_connect("/terminal", headers=HDRS) as ws:
        frame = ws.receive_json()
    assert frame == {"type": "error", "code": "SESSION_LIMIT"}


def test_bad_token_closed():
    client = TestClient(app)
    import pytest

    with pytest.raises(Exception):  # 未 accept 即 close(4401) → handshake 失敗
        with client.websocket_connect("/terminal", headers={"X-Runner-Token": "no"}):
            pass


def test_bad_start_frame():
    client = TestClient(app)
    with client.websocket_connect("/terminal", headers=HDRS) as ws:
        ws.send_json({"type": "stdin", "data": "x"})
        frame = ws.receive_json()
    assert frame == {"type": "error", "code": "BAD_START"}
