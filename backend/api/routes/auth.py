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

    model_config = {"from_attributes": True}


@router.get("/me")
async def me(user: User = Depends(get_current_db_user)) -> UserResponse:
    """回傳當前登入使用者的 DB 資訊（首次登入自動建立記錄）。"""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        role=user.role.value,
    )
