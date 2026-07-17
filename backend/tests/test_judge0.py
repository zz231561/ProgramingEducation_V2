"""Judge0 service 單元測試 — mock httpx 驗證 submit + polling 流程。"""

import base64
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from services.judge0 import submit_and_poll, ExecutionResult, _build_headers, _decode_b64
from core.errors import AppError


def _b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


# === _build_headers（authn 分支：RapidAPI / 自架 X-Auth-Token / 無 key）===

def test_headers_rapidapi_url_uses_rapidapi_key(monkeypatch):
    """URL 含 rapidapi 網域 → 自動帶 X-RapidAPI-Key。"""
    from services.judge0 import settings
    monkeypatch.setattr(settings, "JUDGE0_API_URL", "https://judge0-ce.p.rapidapi.com")
    monkeypatch.setattr(settings, "JUDGE0_API_KEY", "rapid-key")
    monkeypatch.setattr(settings, "JUDGE0_AUTH_MODE", "")

    headers = _build_headers()
    assert headers["X-RapidAPI-Key"] == "rapid-key"
    assert "X-Auth-Token" not in headers


def test_headers_self_hosted_url_uses_auth_token(monkeypatch):
    """自架 URL + key → 自動帶 X-Auth-Token（不帶 RapidAPI header）。"""
    from services.judge0 import settings
    monkeypatch.setattr(settings, "JUDGE0_API_URL", "http://judge0.internal:2358")
    monkeypatch.setattr(settings, "JUDGE0_API_KEY", "self-host-token")
    monkeypatch.setattr(settings, "JUDGE0_AUTH_MODE", "")

    headers = _build_headers()
    assert headers["X-Auth-Token"] == "self-host-token"
    assert "X-RapidAPI-Key" not in headers


def test_headers_explicit_auth_mode_overrides_url(monkeypatch):
    """JUDGE0_AUTH_MODE 顯式指定時強制覆蓋 URL 自動判斷。"""
    from services.judge0 import settings
    # URL 看起來像 rapidapi，但顯式指定 self-hosted
    monkeypatch.setattr(settings, "JUDGE0_API_URL", "https://proxy.rapidapi.example.com")
    monkeypatch.setattr(settings, "JUDGE0_API_KEY", "tok")
    monkeypatch.setattr(settings, "JUDGE0_AUTH_MODE", "self-hosted")

    headers = _build_headers()
    assert headers["X-Auth-Token"] == "tok"
    assert "X-RapidAPI-Key" not in headers


def test_headers_no_key_has_no_auth_header(monkeypatch):
    """無 key（自架未開 authn）→ 不帶任何 auth header。"""
    from services.judge0 import settings
    monkeypatch.setattr(settings, "JUDGE0_API_URL", "http://judge0.internal:2358")
    monkeypatch.setattr(settings, "JUDGE0_API_KEY", "")
    monkeypatch.setattr(settings, "JUDGE0_AUTH_MODE", "")

    headers = _build_headers()
    assert "X-Auth-Token" not in headers
    assert "X-RapidAPI-Key" not in headers


# === _decode_b64 ===

def test_decode_b64_normal():
    assert _decode_b64(_b64("Hello")) == "Hello"


def test_decode_b64_none():
    assert _decode_b64(None) == ""


def test_decode_b64_empty():
    assert _decode_b64("") == ""


# === submit_and_poll ===

def _mock_response(status_code: int, json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


@pytest.mark.asyncio
async def test_submit_and_poll_success():
    """正常提交 + polling 成功取得結果。"""
    submit_resp = _mock_response(201, {"token": "abc-123"})
    poll_resp = _mock_response(200, {
        "stdout": _b64("42\n"),
        "stderr": None,
        "compile_output": None,
        "exit_code": 0,
        "time": "0.01",
        "memory": 3200,
        "status": {"id": 3, "description": "Accepted"},
    })

    mock_client = AsyncMock()
    mock_client.post.return_value = submit_resp
    mock_client.get.return_value = poll_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("services.judge0.httpx.AsyncClient", return_value=mock_client):
        with patch("services.judge0.asyncio.sleep", new_callable=AsyncMock):
            result = await submit_and_poll("int main(){}")

    assert isinstance(result, ExecutionResult)
    assert result.stdout == "42\n"
    assert result.exit_code == 0
    assert result.status_description == "Accepted"


@pytest.mark.asyncio
async def test_submit_and_poll_compile_error():
    """編譯失敗回傳 compile_output。"""
    submit_resp = _mock_response(201, {"token": "xyz"})
    poll_resp = _mock_response(200, {
        "stdout": None,
        "stderr": None,
        "compile_output": _b64("error: expected ';'"),
        "exit_code": 1,
        "time": None,
        "memory": None,
        "status": {"id": 6, "description": "Compilation Error"},
    })

    mock_client = AsyncMock()
    mock_client.post.return_value = submit_resp
    mock_client.get.return_value = poll_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("services.judge0.httpx.AsyncClient", return_value=mock_client):
        with patch("services.judge0.asyncio.sleep", new_callable=AsyncMock):
            result = await submit_and_poll("bad code")

    assert result.compile_output == "error: expected ';'"
    assert result.status_description == "Compilation Error"


@pytest.mark.asyncio
async def test_submit_rate_limited():
    """Judge0 回傳 429 時拋出 AppError。"""
    submit_resp = _mock_response(429, {})

    mock_client = AsyncMock()
    mock_client.post.return_value = submit_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("services.judge0.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AppError) as exc_info:
            await submit_and_poll("int main(){}")

    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_submit_service_unavailable():
    """Judge0 回傳 500+ 時拋出 503。"""
    submit_resp = _mock_response(500, {})

    mock_client = AsyncMock()
    mock_client.post.return_value = submit_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("services.judge0.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AppError) as exc_info:
            await submit_and_poll("int main(){}")

    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_submit_network_error_returns_503():
    """網路層例外（連線失敗 / timeout）應轉 503，不可冒泡成 500。"""
    import httpx

    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.ConnectError("connection refused")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("services.judge0.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AppError) as exc_info:
            await submit_and_poll("int main(){}")

    assert exc_info.value.status_code == 503
    assert exc_info.value.error == "JUDGE0_UNAVAILABLE"


@pytest.mark.asyncio
async def test_poll_network_error_retries_until_timeout():
    """polling 途中持續網路錯誤 → 重試耗盡後回 504。"""
    import httpx

    submit_resp = _mock_response(201, {"token": "abc-123"})

    mock_client = AsyncMock()
    mock_client.post.return_value = submit_resp
    mock_client.get.side_effect = httpx.ReadTimeout("timeout")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("services.judge0.httpx.AsyncClient", return_value=mock_client):
        with patch("services.judge0.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(AppError) as exc_info:
                await submit_and_poll("int main(){}")

    assert exc_info.value.status_code == 504
    assert exc_info.value.error == "EXECUTION_TIMEOUT"
