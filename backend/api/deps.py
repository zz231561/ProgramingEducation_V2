"""共用依賴注入（DB session、Redis、當前使用者等）。"""

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user, get_token_from_request, decode_nextauth_token, TokenPayload
from core.database import get_db
from core.redis import get_redis
from models.user import User
from services.user import get_or_create_user


async def get_current_db_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """依賴注入 — 解析 token 並確保使用者存在於 DB。

    首次登入時自動建立記錄，後續登入更新 last_login_at。
    """
    token = get_current_user(request)
    return await get_or_create_user(db, token)


__all__ = [
    "get_db",
    "get_redis",
    "get_current_user",
    "get_current_db_user",
    "TokenPayload",
    "User",
]
