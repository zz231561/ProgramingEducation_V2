"""精熟度查詢 — 給前端 Knowledge Graph 著色用。"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.concept import Concept
from models.mastery import StudentMastery


@dataclass(frozen=True)
class MasterySummaryEntry:
    """單一 (concept) 的精熟度摘要。"""

    tag: str
    confidence: float
    exposure_count: int
    success_count: int
    error_count: int
    bloom_level: int | None


async def get_user_mastery_summary(
    db: AsyncSession, user_id: UUID
) -> list[MasterySummaryEntry]:
    """回傳該使用者所有 student_mastery rows + 對應 concept tag。

    沒有 row 的 concept 不會出現在回傳中（前端視為「尚未互動」灰色）。
    """
    stmt = (
        select(
            Concept.tag,
            StudentMastery.confidence,
            StudentMastery.exposure_count,
            StudentMastery.success_count,
            StudentMastery.error_count,
            StudentMastery.bloom_level,
        )
        .join(StudentMastery, StudentMastery.concept_id == Concept.id)
        .where(StudentMastery.user_id == user_id)
    )
    rows = (await db.execute(stmt)).all()
    return [
        MasterySummaryEntry(
            tag=r.tag,
            confidence=r.confidence,
            exposure_count=r.exposure_count,
            success_count=r.success_count,
            error_count=r.error_count,
            bloom_level=r.bloom_level,
        )
        for r in rows
    ]
