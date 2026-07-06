"""使用者路由 — 當前使用者資訊（瀏覽器端入口）。

存在理由：`/auth/me` 經 Next.js proxy 會被 NextAuth 的 `/api/auth/*` catch-all
攔截，瀏覽器到不了後端。本路由提供不在 `/auth` 前綴下的等價端點 `/users/me`
供前端取得角色等資訊。
"""

from fastapi import APIRouter, Depends

from api.deps import get_current_db_user
from api.routes.auth import UserResponse, build_user_response
from models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def me(user: User = Depends(get_current_db_user)) -> UserResponse:
    """回傳當前登入使用者資訊（含 role）；供前端 role gating 使用。"""
    return build_user_response(user)
