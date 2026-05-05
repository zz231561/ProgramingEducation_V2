"""學習單元狀態管理 service — status transition + 解鎖（roadmap 3-1d）。

狀態機（與 LearningUnitStatus enum 對齊）：

    locked ──(rejected)──┐
       │                 │
       │  *(由前置完成    ▼
       │   自動解鎖)──→ available
       │                 │
       │                 │ student starts
       │                 ▼
       │            in_progress
       │                 │
       │                 │ student completes
       │                 ▼
       └─(rejected)── completed ──(rejected)──→ * (no further changes)

合法手動 transition（PATCH endpoint 接受）：
- available → in_progress
- in_progress → completed     ← 此 transition 同時解鎖下一個 unit
- in_progress → available     ← 學生重置（reopen for revisit）

非法 transition（一律 422）：
- 任何進入 locked 的（locked 是系統管理，非使用者意圖）
- locked 直接 → in_progress（必須先 available）
- completed → 任何狀態（已完成則固定，避免精熟度反覆波動）

擁有權檢查：透過 unit.path_id → path.user_id 比對。非本人 → 404。
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.learning import LearningPath, LearningUnit, LearningUnitStatus

_VALID_TRANSITIONS: dict[str, set[str]] = {
    LearningUnitStatus.AVAILABLE.value: {LearningUnitStatus.IN_PROGRESS.value},
    LearningUnitStatus.IN_PROGRESS.value: {
        LearningUnitStatus.COMPLETED.value,
        LearningUnitStatus.AVAILABLE.value,
    },
}


async def _get_owned_unit(
    db: AsyncSession, unit_id: UUID, user_id: UUID
) -> tuple[LearningUnit, LearningPath]:
    """取屬於 user_id 的 unit + 所屬 path；非本人 → 404。"""
    row = (
        await db.execute(
            select(LearningUnit, LearningPath)
            .join(LearningPath, LearningPath.id == LearningUnit.path_id)
            .where(LearningUnit.id == unit_id)
        )
    ).first()
    if row is None or row[1].user_id != user_id:
        raise AppError(
            404,
            "LEARNING_UNIT_NOT_FOUND",
            f"找不到學習單元：{unit_id}",
        )
    return row[0], row[1]


def _validate_transition(current: str, target: str) -> None:
    """檢查 status transition 是否合法；不合法 → 422。"""
    allowed = _VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise AppError(
            422,
            "LEARNING_UNIT_INVALID_TRANSITION",
            f"狀態 {current} 不可轉為 {target}（合法目標：{sorted(allowed) or '無'}）",
        )


async def _unlock_next_unit(
    db: AsyncSession, completed_unit: LearningUnit
) -> LearningUnit | None:
    """解鎖同 path 內 order_index = current+1 的 unit（若存在且為 locked）。"""
    next_unit = (
        await db.execute(
            select(LearningUnit)
            .where(LearningUnit.path_id == completed_unit.path_id)
            .where(LearningUnit.order_index == completed_unit.order_index + 1)
        )
    ).scalar_one_or_none()
    if next_unit is None:
        return None
    if next_unit.status == LearningUnitStatus.LOCKED.value:
        next_unit.status = LearningUnitStatus.AVAILABLE.value
    return next_unit


async def update_unit_status(
    db: AsyncSession,
    user_id: UUID,
    unit_id: UUID,
    new_status: LearningUnitStatus,
) -> tuple[LearningUnit, LearningUnit | None]:
    """更新 unit 狀態 + 視情況解鎖下一個。

    Returns:
        (updated_unit, next_unlocked_unit_or_None)

    Raises:
        AppError 404 LEARNING_UNIT_NOT_FOUND — 不存在或非本人擁有
        AppError 422 LEARNING_UNIT_INVALID_TRANSITION — 違法 transition
    """
    unit, _ = await _get_owned_unit(db, unit_id, user_id)
    _validate_transition(unit.status, new_status.value)

    unit.status = new_status.value
    next_unit: LearningUnit | None = None
    if new_status is LearningUnitStatus.COMPLETED:
        unit.completed_at = datetime.now(timezone.utc)
        next_unit = await _unlock_next_unit(db, unit)
    elif new_status is LearningUnitStatus.AVAILABLE:
        # 重新開啟（revisit）→ 清掉先前的 completed_at（若有）
        unit.completed_at = None

    await db.commit()
    await db.refresh(unit)
    if next_unit is not None:
        await db.refresh(next_unit)
    return unit, next_unit
