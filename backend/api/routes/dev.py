"""開發者模式 API（DEV 系列）。

所有變更類端點必須掛 `require_dev_user`（後端防線，非 dev 一律 403）；
`/dev/status` 例外 — 任何已登入使用者可查自己是否為 dev，
供前端決定是否渲染 Settings 開發者區塊（不渲染 ≠ 防線，防線在各端點）。
"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.deps import get_current_db_user
from core.dev_mode import is_dev_email
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dev", tags=["dev"])


class DevStatusOut(BaseModel):
    """開發者模式狀態。"""

    is_dev: bool


@router.get("/status", response_model=DevStatusOut)
async def dev_status(
    user: User = Depends(get_current_db_user),
) -> DevStatusOut:
    """查詢當前使用者是否為生效中的開發者帳號。"""
    return DevStatusOut(is_dev=is_dev_email(user.email))
