"""Health check 端點。"""

from fastapi import APIRouter
from sqlalchemy import text

from core.database import async_session
from core.redis import redis_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """檢查 API、DB、Redis 是否存活。"""
    db_ok = await _check_db()
    redis_ok = await _check_redis()

    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "services": {
            "database": "connected" if db_ok else "disconnected",
            "redis": "connected" if redis_ok else "disconnected",
        },
    }


async def _check_db() -> bool:
    """嘗試執行 SELECT 1 確認 DB 連線。"""
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _check_redis() -> bool:
    """嘗試 PING 確認 Redis 連線。"""
    try:
        if redis_client is None:
            return False
        return await redis_client.ping()
    except Exception:
        return False
