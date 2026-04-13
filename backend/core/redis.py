"""Redis 連線管理。"""

from redis.asyncio import Redis

from core.config import settings

redis_client: Redis | None = None


async def init_redis() -> None:
    """啟動時建立 Redis 連線。"""
    global redis_client  # noqa: PLW0603
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


async def close_redis() -> None:
    """關閉 Redis 連線。"""
    if redis_client is not None:
        await redis_client.aclose()


def get_redis() -> Redis:
    """依賴注入 — 取得 Redis client。"""
    if redis_client is None:
        raise RuntimeError("Redis 尚未初始化")
    return redis_client
