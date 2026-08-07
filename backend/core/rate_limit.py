"""Per-user rate limiting — Redis 固定窗口計數。

設計原則：
- 只依賴 token（不進 DB），保持 core 層不反向依賴 api 層
- fail-open：Redis 不可用時記 warning 放行，限流是保護不是功能，
  不因快取故障讓整個教學服務停擺
- 用法：`@router.post(..., dependencies=[Depends(rate_limit("chat"))])`
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import Request

from core.auth import get_current_user
from core.config import settings
from core.dev_mode import is_dev_email
from core.errors import AppError
from core.redis import get_redis

logger = logging.getLogger(__name__)

_WINDOW_SECONDS = 60
# 每日配額窗口：固定 26 小時 TTL，涵蓋任何時區的一天並在隔日自然滾動
_DAY_TTL_SECONDS = 26 * 3600


async def _check_daily_quota(redis, user_key: str) -> None:
    """每人每日 LLM 互動上限 — 每分鐘限流擋不住整天持續呼叫，這裡設成本天花板。

    以 UTC 日期分 key，超額回 429 並提示明日恢復（配額每日重置，不會卡住整週）。
    """
    limit = settings.RATE_LIMIT_LLM_PER_DAY
    if limit <= 0:  # 0 或負值 = 停用每日配額
        return

    today = datetime.now(UTC).strftime("%Y%m%d")
    key = f"rl:daily:{user_key}:{today}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, _DAY_TTL_SECONDS)
    if count > limit:
        raise AppError(
            429,
            "DAILY_QUOTA_EXCEEDED",
            f"今日 AI 互動已達上限（{limit} 次），明天會重新計算。"
            "你仍可繼續寫程式、執行、以及閱讀教材。",
            detail={"limit": limit, "used": count - 1},
        )


def rate_limit(scope: str, limit_per_minute: int | None = None) -> Callable:
    """依賴工廠 — 對當前使用者在指定 scope 上做每分鐘請求數限制。

    Args:
        scope: 限流分組名（同組共用額度，如 "llm" / "execute"）
        limit_per_minute: 每分鐘上限；None 時用 settings.RATE_LIMIT_PER_MINUTE
    """

    async def _check(request: Request) -> None:
        token = get_current_user(request)  # 未登入在此即拋 401
        if is_dev_email(token.email):
            # 開發者帳號豁免限流（DEV 系列；密集測試 LLM 端點不受 10 次/分擋）
            return
        limit = limit_per_minute or settings.RATE_LIMIT_PER_MINUTE
        user_key = token.google_id or token.sub
        key = f"rl:{user_key}:{scope}"

        try:
            redis = get_redis()
            # LLM 端點另受每日配額約束（成本天花板）；其他 scope 只走每分鐘限流
            if scope == "llm":
                await _check_daily_quota(redis, user_key)
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
