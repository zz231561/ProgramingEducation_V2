"""標準錯誤回應模型與例外類別。"""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """標準 API 錯誤回應格式。"""

    error: str
    message: str
    detail: dict[str, Any] | None = None


class AppError(Exception):
    """應用層自訂例外，會被全域 handler 攔截並轉為 ErrorResponse。"""

    def __init__(
        self,
        status_code: int,
        error: str,
        message: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.error = error
        self.message = message
        self.detail = detail


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    """將 AppError 轉為標準 JSON 回應。"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error,
            message=exc.message,
            detail=exc.detail,
        ).model_dump(exclude_none=True),
    )


async def unhandled_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
    """攔截未處理的例外，回傳通用 500 錯誤。"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="伺服器內部錯誤，請稍後再試",
        ).model_dump(exclude_none=True),
    )
