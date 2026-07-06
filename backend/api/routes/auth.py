"""Auth 路由 — 驗證 JWT token、取得當前使用者資訊。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.deps import get_current_db_user
from models.user import User


router = APIRouter(prefix="/auth", tags=["auth"])


class UserResponse(BaseModel):
    """使用者資訊回應。"""

    id: str
    email: str
    name: str
    avatar_url: str | None
    role: str
    role_selected: bool

    model_config = {"from_attributes": True}


def build_user_response(user: User) -> UserResponse:
    """由 User model 組出 UserResponse（供 /auth/me 與 /users/me 共用）。"""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        role=user.role.value,
        role_selected=user.role_selected,
    )


@router.get("/me")
async def me(user: User = Depends(get_current_db_user)) -> UserResponse:
    """回傳當前登入使用者的 DB 資訊（首次登入自動建立記錄）。

    注意：前端經 Next.js proxy 呼叫時，`/api/auth/*` 會被 NextAuth catch-all
    攔截而到不了此端點；瀏覽器端請改用等價的 `/users/me`。此路由保留供後端
    整合測試（直打 ASGI）與非瀏覽器 client 使用。
    """
    return build_user_response(user)
