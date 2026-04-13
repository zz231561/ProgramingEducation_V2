"""FastAPI 應用程式進入點。"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import engine
from core.redis import init_redis, close_redis
from core.errors import AppError, app_error_handler, unhandled_error_handler
from api.routes.health import router as health_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """管理應用程式啟動/關閉時的資源。"""
    # 啟動：初始化 Redis
    await init_redis()
    yield
    # 關閉：釋放連線
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# === CORS — 僅允許前端 origin ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 全域錯誤處理 ===
app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_error_handler)  # type: ignore[arg-type]

# === 路由註冊 ===
app.include_router(health_router)
