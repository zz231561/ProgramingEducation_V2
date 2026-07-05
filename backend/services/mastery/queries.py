"""精熟度查詢 — 前端 Knowledge Graph 著色 + Coddy K-Graph state（K2b）。

K6b（2026-07-06）：confidence 欄位改回傳「衰減後 effective 值」——所有讀取端
（圖譜著色 / K4 鷹架 / 前端顯示）一致拿到記憶衰減後的狀態；DB 原值放
raw_confidence 供 K6c 前端解釋「因久未練習而下降」。
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.concept import Concept
from models.mastery import StudentMastery
from services.mastery.decay import days_since, effective_confidence, is_due_for_review


@dataclass(frozen=True)
class MasterySummaryEntry:
    """單一 (concept) 的精熟度摘要。

    confidence = 衰減後 effective 值；raw_confidence = DB 儲存值（BKT prior）。
    """

    tag: str
    confidence: float
    exposure_count: int
    success_count: int
    error_count: int
    bloom_level: int | None
    last_practiced_at: datetime | None = None
    # K6b/K6c 衍生欄位
    raw_confidence: float = 0.0
    days_since_practiced: float | None = None
    due_for_review: bool = False


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
            StudentMastery.last_practiced_at,
        )
        .join(StudentMastery, StudentMastery.concept_id == Concept.id)
        .where(StudentMastery.user_id == user_id)
    )
    rows = (await db.execute(stmt)).all()
    return [
        MasterySummaryEntry(
            tag=r.tag,
            confidence=effective_confidence(
                r.confidence, r.last_practiced_at, r.success_count
            ),
            exposure_count=r.exposure_count,
            success_count=r.success_count,
            error_count=r.error_count,
            bloom_level=r.bloom_level,
            last_practiced_at=r.last_practiced_at,
            raw_confidence=r.confidence,
            days_since_practiced=days_since(r.last_practiced_at),
            due_for_review=is_due_for_review(
                r.confidence, r.last_practiced_at, r.success_count
            ),
        )
        for r in rows
    ]
