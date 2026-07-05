"""開發者模式 API（DEV 系列）。

所有變更類端點必須掛 `require_dev_user`（後端防線，非 dev 一律 403）；
`/dev/status` 例外 — 任何已登入使用者可查自己是否為 dev，
供前端決定是否渲染 Settings 開發者區塊（不渲染 ≠ 防線，防線在各端點）。
業務邏輯在 `services/dev_tools.py`，route 保持薄層。
"""

import logging
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db, require_dev_user
from core.dev_mode import is_dev_email
from models.user import User, UserRole
from services.dev_tools import reset_user_data, set_mastery, set_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dev", tags=["dev"])

ResetCategory = Literal["mastery", "progress", "quiz", "chat"]


class DevStatusOut(BaseModel):
    """開發者模式狀態。"""

    is_dev: bool


class ResetIn(BaseModel):
    """分類重置請求（至少一類）。"""

    categories: list[ResetCategory] = Field(min_length=1)


class ResetOut(BaseModel):
    """各類別刪除列數。"""

    deleted: dict[str, int]


class MasteryIn(BaseModel):
    """熟練度覆寫請求 — tags 或 category 恰好擇一。"""

    tags: list[str] | None = None
    category: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _exactly_one_target(self) -> "MasteryIn":
        if (self.tags is None) == (self.category is None):
            raise ValueError("tags 與 category 必須恰好提供一個")
        return self


class MasteryOut(BaseModel):
    """熟練度覆寫結果。"""

    updated: int


class RoleIn(BaseModel):
    """身分切換請求（dev 工具僅開放 student/teacher）。"""

    role: Literal["student", "teacher"]


class RoleOut(BaseModel):
    """切換後角色。"""

    role: str


@router.get("/status", response_model=DevStatusOut)
async def dev_status(
    user: User = Depends(get_current_db_user),
) -> DevStatusOut:
    """查詢當前使用者是否為生效中的開發者帳號。"""
    return DevStatusOut(is_dev=is_dev_email(user.email))


@router.post("/reset", response_model=ResetOut)
async def dev_reset(
    body: ResetIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_dev_user),
) -> ResetOut:
    """分類重置當前 dev 帳號的學習資料（DEV-3）。"""
    deleted = await reset_user_data(db, user.id, set(body.categories))
    return ResetOut(deleted=deleted)


@router.put("/mastery", response_model=MasteryOut)
async def dev_set_mastery(
    body: MasteryIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_dev_user),
) -> MasteryOut:
    """覆寫指定 concept / 整章的熟練度（DEV-5）。"""
    updated = await set_mastery(
        db, user.id, tags=body.tags, category=body.category, confidence=body.confidence,
    )
    return MasteryOut(updated=updated)


@router.put("/role", response_model=RoleOut)
async def dev_set_role(
    body: RoleIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_dev_user),
) -> RoleOut:
    """切換 student ⇄ teacher 身分（DEV-6；真改 users.role）。"""
    updated = await set_role(db, user, UserRole(body.role))
    return RoleOut(role=updated.role.value)
