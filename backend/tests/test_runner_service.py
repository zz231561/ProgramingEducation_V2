"""services/runner dispatcher 測試 — 分派規則 + 自建路徑回應/錯誤映射。"""

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.errors import AppError
from services.judge0 import ExecutionResult
from services.runner import submit_and_poll


def _mock_client(resp: MagicMock | None = None, raise_exc: Exception | None = None):
    client = AsyncMock()
    if raise_exc is not None:
        client.post.side_effect = raise_exc
    else:
        client.post.return_value = resp
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


def _resp(status_code: int, json_data: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    return resp


def _set_self_backend(monkeypatch):
    from services.runner import settings

    monkeypatch.setattr(settings, "RUNNER_BACKEND", "self")
    monkeypatch.setattr(settings, "RUNNER_URL", "http://runner.internal:8080")
    monkeypatch.setattr(settings, "RUNNER_TOKEN", "tok")


# === 分派規則 ===


@pytest.mark.asyncio
async def test_dispatch_judge0_when_backend_judge0(monkeypatch):
    """RUNNER_BACKEND=judge0 → 強制走 Judge0（手動降級開關）。"""
    from services.runner import settings

    monkeypatch.setattr(settings, "RUNNER_BACKEND", "judge0")
    monkeypatch.setattr(settings, "RUNNER_URL", "http://runner.internal:8080")
    fake = ExecutionResult(status_description="Accepted")
    with patch(
        "services.runner._judge0_submit_and_poll", new=AsyncMock(return_value=fake)
    ) as j0:
        result = await submit_and_poll(source_code="int main(){}")
    assert result.status_description == "Accepted"
    j0.assert_awaited_once()


@pytest.mark.asyncio
async def test_dispatch_judge0_when_url_empty(monkeypatch):
    """RUNNER_URL 未設 → 自動退 Judge0（R5 部署前生產不會斷）。"""
    from services.runner import settings

    monkeypatch.setattr(settings, "RUNNER_BACKEND", "self")
    monkeypatch.setattr(settings, "RUNNER_URL", "")
    fake = ExecutionResult(status_description="Accepted")
    with patch(
        "services.runner._judge0_submit_and_poll", new=AsyncMock(return_value=fake)
    ) as j0:
        await submit_and_poll(source_code="int main(){}")
    j0.assert_awaited_once()


# === 自建路徑 ===


@pytest.mark.asyncio
async def test_self_runner_success(monkeypatch):
    _set_self_backend(monkeypatch)
    payload = {
        "stdout": "42",
        "stderr": "",
        "compile_output": "",
        "exit_code": 0,
        "time": "0.012",
        "memory": None,
        "status_description": "Accepted",
        "cache_hit": True,  # runner 額外欄位，映射時應忽略
        "queued_ms": 3,
    }
    client = _mock_client(_resp(200, payload))
    with patch("services.runner.httpx.AsyncClient", return_value=client):
        result = await submit_and_poll(
            source_code="int main(){}", stdin="in", command_line_arguments="a b"
        )
    assert result.status_description == "Accepted"
    assert result.stdout == "42"
    assert result.time == "0.012"
    # 請求內容：欄位名對齊 runner API + token header
    kwargs = client.post.await_args.kwargs
    assert kwargs["json"] == {"code": "int main(){}", "stdin": "in", "args": "a b"}
    assert kwargs["headers"]["X-Runner-Token"] == "tok"


@pytest.mark.asyncio
async def test_self_runner_timeout_maps_504(monkeypatch):
    _set_self_backend(monkeypatch)
    client = _mock_client(raise_exc=httpx.ReadTimeout("slow"))
    with patch("services.runner.httpx.AsyncClient", return_value=client):
        with pytest.raises(AppError) as exc:
            await submit_and_poll(source_code="int main(){}")
    assert exc.value.status_code == 504


@pytest.mark.asyncio
async def test_self_runner_network_error_maps_503(monkeypatch):
    _set_self_backend(monkeypatch)
    client = _mock_client(raise_exc=httpx.ConnectError("refused"))
    with patch("services.runner.httpx.AsyncClient", return_value=client):
        with pytest.raises(AppError) as exc:
            await submit_and_poll(source_code="int main(){}")
    assert exc.value.status_code == 503
    assert exc.value.error == "RUNNER_UNAVAILABLE"


@pytest.mark.asyncio
async def test_self_runner_busy_maps_503(monkeypatch):
    """runner 排隊滿（503）→ 503 RUNNER_BUSY，訊息提示稍候。"""
    _set_self_backend(monkeypatch)
    client = _mock_client(_resp(503, {"detail": "RUNNER_BUSY"}))
    with patch("services.runner.httpx.AsyncClient", return_value=client):
        with pytest.raises(AppError) as exc:
            await submit_and_poll(source_code="int main(){}")
    assert exc.value.status_code == 503
    assert exc.value.error == "RUNNER_BUSY"


@pytest.mark.asyncio
async def test_self_runner_auth_error_maps_502(monkeypatch):
    """token 配置錯誤（401）屬服務端問題 → 502，不對學生洩漏細節。"""
    _set_self_backend(monkeypatch)
    client = _mock_client(_resp(401))
    with patch("services.runner.httpx.AsyncClient", return_value=client):
        with pytest.raises(AppError) as exc:
            await submit_and_poll(source_code="int main(){}")
    assert exc.value.status_code == 502
