"""Per-user rate limiting — Redis 固定窗口計數。

設計原則：
- 只依賴 token（不進 DB），保持 core 層不反向依賴 api 層
- fail-open：Redis 不可用時記 warning 放行，限流是保護不是功能，
  不因快取故障讓整個教學服務停擺
- 用法：`@router.post(..., dependencies=[Depends(rate_limit("chat"))])`
"""

import logging
from collections.abc import Callable

from fastapi import Request

from core.auth import get_current_user
from core.config import settings
from core.errors import AppError
from core.redis import get_redis

logger = logging.getLogger(__name__)

_WINDOW_SECONDS = 60


def rate_limit(scope: str, limit_per_minute: int | None = None) -> Callable:
    """依賴工廠 — 對當前使用者在指定 scope 上做每分鐘請求數限制。

    Args:
        scope: 限流分組名（同組共用額度，如 "llm" / "execute"）
        limit_per_minute: 每分鐘上限；None 時用 settings.RATE_LIMIT_PER_MINUTE
    """

    async def _check(request: Request) -> None:
        token = get_current_user(request)  # 未登入在此即拋 401
        limit = limit_per_minute or settings.RATE_LIMIT_PER_MINUTE
        key = f"rl:{token.google_id or token.sub}:{scope}"

        try:
            redis = get_redis()
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, _WINDOW_SECONDS)
            if count > limit:
                ttl = await redis.ttl(key)
                retry_after = ttl if ttl > 0 else _WINDOW_SECONDS
                raise AppError(
                    429,
                    "RATE_LIMITED",
                    f"請求過於頻繁，請於 {retry_after} 秒後再試",
                    detail={"retry_after_seconds": retry_after},
                )
        except AppError:
            raise
        except Exception as e:
            logger.warning("Rate limit check failed (fail-open): %r", e)

    return _check
