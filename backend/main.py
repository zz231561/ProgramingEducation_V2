"""FastAPI 應用程式進入點。"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import engine
from core.redis import init_redis, close_redis
from core.errors import (
    AppError,
    app_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from api.routes.assignments import (
    attachments_router,
    router as assignments_router,
)
from api.routes.auth import router as auth_router
from api.routes.chat import router as chat_router
from api.routes.classes import router as classes_router
from api.routes.code import router as code_router
from api.routes.comprehension import router as comprehension_router
from api.routes.comprehension_trigger import router as comprehension_trigger_router
from api.routes.comprehension_variation import router as comprehension_variation_router
from api.routes.concepts import router as concepts_router
from api.routes.dashboard import router as dashboard_router
from api.routes.dev import router as dev_router
from api.routes.dev_quiz import router as dev_quiz_router
from api.routes.diagnosis import router as diagnosis_router
from api.routes.health import router as health_router
from api.routes.learning import router as learning_router
from api.routes.learning_units import router as learning_units_router
from api.routes.profile import router as profile_router
from api.routes.quiz import router as quiz_router
from api.routes.quiz_feedback import router as quiz_feedback_router
from api.routes.quiz_questions import router as quiz_questions_router
from api.routes.reflection import router as reflection_router
from api.routes.users import router as users_router


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
app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_error_handler)  # type: ignore[arg-type]

# === 路由註冊 ===
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(code_router)
app.include_router(chat_router)
app.include_router(concepts_router)
app.include_router(classes_router)
app.include_router(assignments_router)
app.include_router(attachments_router)
app.include_router(profile_router)
app.include_router(diagnosis_router)
app.include_router(dashboard_router)
app.include_router(dev_router)
app.include_router(dev_quiz_router)
app.include_router(quiz_router)
app.include_router(quiz_feedback_router)
app.include_router(quiz_questions_router)
app.include_router(reflection_router)
app.include_router(comprehension_router)
app.include_router(comprehension_variation_router)
app.include_router(comprehension_trigger_router)
app.include_router(learning_router)
app.include_router(learning_units_router)
