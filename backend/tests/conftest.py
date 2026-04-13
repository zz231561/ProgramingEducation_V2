"""共用測試 fixtures — DB 初始化、清理、app dependency override。"""

import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import Base, get_db
from main import app
from tests.helpers import test_engine, TestSessionFactory, DB_PATH, TEST_SECRET


# === 覆蓋 app DB 依賴 ===

async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionFactory() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


# === DB 生命週期 ===

def pytest_configure(config):
    """pytest 啟動時重建全部表（確保 schema 最新）。"""
    async def _create():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())


def pytest_unconfigure(config):
    """pytest 結束時刪除暫存 DB 檔。"""
    try:
        os.unlink(DB_PATH)
    except OSError:
        pass


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables():
    """每個測試後清空資料表。"""
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"DELETE FROM {table.name}"))


# === 共用 fixtures ===

@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture(autouse=True)
def _set_test_secret():
    """統一設定 NEXTAUTH_SECRET。"""
    import core.auth
    original = settings.NEXTAUTH_SECRET
    settings.NEXTAUTH_SECRET = TEST_SECRET
    core.auth._encryption_key = None
    yield
    settings.NEXTAUTH_SECRET = original
    core.auth._encryption_key = None
