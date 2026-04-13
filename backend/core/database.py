"""SQLAlchemy async engine + session 管理。"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """所有 SQLAlchemy Model 的基底類別。"""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """依賴注入 — 提供一個 request-scoped 的 DB session。"""
    async with async_session() as session:
        yield session
