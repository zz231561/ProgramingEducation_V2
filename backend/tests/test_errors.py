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
