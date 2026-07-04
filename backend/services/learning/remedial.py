"""補救路徑 — K3 診斷結果 → 重新開放前置概念單元（roadmap K4c）。

設計：
- 62 個 concept 在學生路徑中都已有對應 unit → 「插入補救單元」實作為
  **重新開放既有 unit**（completed / locked → available），不新建 row、
  不打亂 (path_id, order_index) 唯一約束
- completed → available 是系統級動作（手動 transition 禁止）：
  診斷已證明該概念沒學牢，重開有教學依據；一併清 completed_at
- available / in_progress 的 unit 不動，但仍列入回傳供前端呈現完整補救清單
- 補救順序 = order_index 升冪（路徑順序即拓撲序，最基礎的先學）
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.concept import Concept
from models.learning import LearningUnit, LearningUnitStatus
from services.learning.queries import ensure_default_path_exists

# 這兩個狀態的 unit 會被重新開放
_REOPENABLE = {
    LearningUnitStatus.LOCKED.value,
    LearningUnitStatus.COMPLETED.value,
}


@dataclass(frozen=True)
class RemedialUnit:
    """單一補救單元的開放結果。"""

    unit_id: UUID
    concept_tag: str
    name_zh: str
    order_index: int
    previous_status: str
    status: str  # 開放後狀態（available / 原狀態）


async def open_remedial_units(
    db: AsyncSession,
    user_id: UUID,
    suspect_concept_ids: list[UUID],
) -> list[RemedialUnit]:
    """把嫌疑概念在學生預設路徑中的 units 重新開放為 available。

    Args:
        db: SQLAlchemy async session
        user_id: 學生
        suspect_concept_ids: K3 診斷產出的嫌疑 concept ids

    Returns:
        補救單元列表（order_index 升冪 = 建議學習順序）；
        路徑中無對應 unit 的 concept 直接略過。
        本函式自行 commit（與 units.py service 慣例一致）。
    """
    if not suspect_concept_ids:
        return []

    path = await ensure_default_path_exists(db, user_id)

    rows = (
        await db.execute(
            select(LearningUnit, Concept)
            .join(Concept, Concept.id == LearningUnit.concept_id)
            .where(
                LearningUnit.path_id == path.id,
                LearningUnit.concept_id.in_(suspect_concept_ids),
            )
            .order_by(LearningUnit.order_index)
        )
    ).all()

    results: list[RemedialUnit] = []
    for unit, concept in rows:
        previous = unit.status
        if previous in _REOPENABLE:
            unit.status = LearningUnitStatus.AVAILABLE.value
            unit.completed_at = None
        results.append(
            RemedialUnit(
                unit_id=unit.id,
                concept_tag=concept.tag,
                name_zh=concept.name_zh,
                order_index=unit.order_index,
                previous_status=previous,
                status=unit.status,
            )
        )

    await db.commit()
    return results
