"""使用者路由 — 當前使用者資訊 + 身分自選（瀏覽器端入口）。

存在理由：`/auth/me` 經 Next.js proxy 會被 NextAuth 的 `/api/auth/*` catch-all
攔截，瀏覽器到不了後端。本路由提供不在 `/auth` 前綴下的等價端點 `/users/me`
供前端取得角色等資訊，並提供 `/users/role` 供 onboarding 自選 / 設定頁切換身分。
"""

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from api.routes.auth import UserResponse, build_user_response
from models.user import User, UserRole
from services.identity import select_role

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def me(user: User = Depends(get_current_db_user)) -> UserResponse:
    """回傳當前登入使用者資訊（含 role / role_selected）；供前端 gating 使用。"""
    return build_user_response(user)


class SelectRoleRequest(BaseModel):
    # 自選身分僅限學生 / 教師，不得自選 admin
    role: Literal["student", "teacher"]


class SelectRoleResponse(BaseModel):
    role: str
    role_selected: bool
    did_reset: bool


@router.post("/role", response_model=SelectRoleResponse)
async def choose_role(
    body: SelectRoleRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> SelectRoleResponse:
    """自選 / 切換身分。首次選擇僅設定；已選過再改視為重置（全清學習資料）。"""
    updated, did_reset = await select_role(db, user, UserRole(body.role))
    return SelectRoleResponse(
        role=updated.role.value,
        role_selected=updated.role_selected,
        did_reset=did_reset,
    )
