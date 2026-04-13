"""共用依賴注入（DB session、Redis、當前使用者、角色檢查）。"""

from collections.abc import Callable

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user, get_token_from_request, decode_nextauth_token, TokenPayload
from core.database import get_db
from core.errors import AppError
from core.redis import get_redis
from models.user import User, UserRole
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


def require_roles(*roles: UserRole) -> Callable:
    """依賴工廠 — 檢查當前使用者是否具有指定角色。

    用法：
        @router.get("/admin-only")
        async def admin_panel(user: User = Depends(require_roles(UserRole.ADMIN))):
            ...
    """
    async def _check_role(user: User = Depends(get_current_db_user)) -> User:
        if user.role not in roles:
            allowed = ", ".join(r.value for r in roles)
            raise AppError(403, "FORBIDDEN", f"需要 {allowed} 權限")
        return user

    return _check_role


__all__ = [
    "get_db",
    "get_redis",
    "get_current_user",
    "get_current_db_user",
    "require_roles",
    "TokenPayload",
    "User",
]
