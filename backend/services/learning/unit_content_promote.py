"""Phase 6-2b：staging → learning_units.content promote helper。

當 6-4 教授抽查通過後，把 `unit_content_staging.content` 寫入該 concept 對應的所有
`learning_units.content`（多 user 共享）。

設計取捨：
- 與 batch_generator 拆檔：promote 是 6-4 觸發的後段流程，避免與 batch generation 邏輯
  耦合，也讓單一檔案保持小於 250 行硬限。
- 強制 status='approved' 才執行：避免誤把 pending/rejected 內容推到正式 schema。
"""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.learning import LearningUnit
from models.unit_content_staging import StagingStatus, UnitContentStaging


async def promote_concept(db: AsyncSession, concept_id: UUID) -> int:
    """把 staging.content 寫入該 concept 對應的所有 learning_units.content。

    僅當 staging.status='approved' 才執行；否則 raise。

    Returns:
        受影響的 learning_units 行數

    Raises:
        AppError 404 STAGING_NOT_FOUND — 該 concept 無 staging row
        AppError 422 STAGING_NOT_APPROVED — staging 尚未 approved
    """
    staging = (
        await db.execute(
            select(UnitContentStaging).where(
                UnitContentStaging.concept_id == concept_id
            )
        )
    ).scalar_one_or_none()
    if staging is None:
        raise AppError(
            404, "STAGING_NOT_FOUND", f"concept {concept_id} 無 staging row"
        )
    if staging.status != StagingStatus.APPROVED.value:
        raise AppError(
            422,
            "STAGING_NOT_APPROVED",
            f"staging status={staging.status}，僅 approved 可 promote",
        )

    result = await db.execute(
        update(LearningUnit)
        .where(LearningUnit.concept_id == concept_id)
        .values(content=staging.content)
    )
    await db.commit()
    return result.rowcount or 0
