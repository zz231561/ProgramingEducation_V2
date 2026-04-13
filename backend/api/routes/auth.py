"""Auth 路由 — 驗證 JWT token、取得當前使用者資訊。"""

from fastapi import APIRouter, Depends

from api.deps import get_current_user, TokenPayload

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def me(user: TokenPayload = Depends(get_current_user)) -> dict:
    """回傳當前登入使用者的 token 資訊（測試用）。"""
    return user.model_dump()
