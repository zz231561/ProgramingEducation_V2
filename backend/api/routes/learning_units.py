"""學習單元狀態 API（roadmap 3-1d）— PATCH 觸發 transition + 自動解鎖下一單元。

獨立檔避免 learning.py 超過 250 行硬性限制。

API：
- PATCH /learning/units/{unit_id} body `{ status: ... }`
  → 合法 transition：available → in_progress、in_progress → completed、in_progress → available
  → completed 同時連動解鎖下一個 unit（locked → available）
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from core.errors import AppError
from models.learning import LearningUnit, LearningUnitStatus
from models.user import User
from services.learning import update_unit_status

router = APIRouter(prefix="/learning", tags=["learning"])


class PatchUnitRequest(BaseModel):
    status: str = Field(..., description="available | in_progress | completed")


class UnitBasicOut(BaseModel):
    """單元 status update 的精簡 response（不含 concept join；前端需要可重 fetch path detail）。"""

    id: uuid.UUID
    order_index: int
    status: str
    completed_at: str | None


class UnitTransitionOut(BaseModel):
    unit: UnitBasicOut
    next_unlocked_unit: UnitBasicOut | None


def _to_basic(u: LearningUnit) -> UnitBasicOut:
    return UnitBasicOut(
        id=u.id,
        order_index=u.order_index,
        status=u.status,
        completed_at=u.completed_at.isoformat() if u.completed_at else None,
    )


@router.patch("/units/{unit_id}", response_model=UnitTransitionOut)
async def patch_unit(
    unit_id: uuid.UUID,
    body: PatchUnitRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> UnitTransitionOut:
    """更新單元狀態。完成會自動解鎖下一個 unit。"""
    target = _parse_status(body.status)
    updated, next_unit = await update_unit_status(db, user.id, unit_id, target)
    return UnitTransitionOut(
        unit=_to_basic(updated),
        next_unlocked_unit=_to_basic(next_unit) if next_unit is not None else None,
    )


def _parse_status(value: str) -> LearningUnitStatus:
    """422 if invalid（locked 不可由使用者直接設定）。"""
    try:
        parsed = LearningUnitStatus(value)
    except ValueError as exc:
        raise AppError(
            422,
            "INVALID_UNIT_STATUS",
            f"status 必須為 available / in_progress / completed，收到：{value}",
        ) from exc
    if parsed is LearningUnitStatus.LOCKED:
        raise AppError(
            422,
            "INVALID_UNIT_STATUS",
            "locked 為系統管理狀態，不可由使用者直接設定",
        )
    return parsed
