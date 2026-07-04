"""錯誤處理測試 — 確認 AppError 被正確攔截並回傳標準 JSON。"""

import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from core.errors import AppError, app_error_handler, ErrorResponse


@pytest.fixture
def error_app():
    """建立含 AppError handler 的測試 app。"""
    _app = FastAPI()
    _app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]

    @_app.get("/raise-app-error")
    async def _raise():
        raise AppError(
            status_code=429,
            error="RATE_LIMIT_EXCEEDED",
            message="已超過每分鐘請求上限",
            detail={"retry_after_seconds": 42},
        )

    return _app


@pytest.fixture
def error_client(error_app: FastAPI):
    transport = ASGITransport(app=error_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_app_error_returns_standard_json(error_client: AsyncClient):
    """AppError 應轉為標準 ErrorResponse JSON。"""
    resp = await error_client.get("/raise-app-error")
    assert resp.status_code == 429
    body = resp.json()
    assert body["error"] == "RATE_LIMIT_EXCEEDED"
    assert body["message"] == "已超過每分鐘請求上限"
    assert body["detail"]["retry_after_seconds"] == 42


def test_error_response_model():
    """ErrorResponse model 應正確序列化。"""
    err = ErrorResponse(error="TEST", message="test msg")
    data = err.model_dump(exclude_none=True)
    assert "detail" not in data
    assert data["error"] == "TEST"


async def test_unhandled_error_logs_traceback(caplog):
    """未處理例外應記錄 traceback（生產環境 500 唯一的 debug 線索）。"""
    import logging
    from unittest.mock import MagicMock

    from core.errors import unhandled_error_handler

    request = MagicMock()
    request.method = "POST"
    request.url.path = "/chat/interact"

    with caplog.at_level(logging.ERROR, logger="core.errors"):
        resp = await unhandled_error_handler(request, RuntimeError("boom"))

    assert resp.status_code == 500
    assert any("boom" in r.message for r in caplog.records)
    assert any(r.exc_info or "Unhandled error" in r.message for r in caplog.records)


async def test_validation_error_returns_standard_format():
    """422 請求驗證錯誤應轉為與 ErrorResponse 一致的格式（前端統一攔截依賴此格式）。"""
    from fastapi.exceptions import RequestValidationError
    from pydantic import BaseModel

    from core.errors import validation_error_handler

    _app = FastAPI()
    _app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]

    class _Body(BaseModel):
        question: str

    @_app.post("/needs-body")
    async def _endpoint(body: _Body):
        return {"ok": True}

    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post("/needs-body", json={})

    assert resp.status_code == 422
    body = resp.json()
    assert body["error"] == "VALIDATION_ERROR"
    assert "message" in body
    assert "errors" in body["detail"]
