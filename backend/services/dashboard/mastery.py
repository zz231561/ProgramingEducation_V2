"""Dashboard 精熟度詳細總覽（roadmap 3-3c）。

依 concept.category 分組，每組含 summary（total/started/mastered）+ concept 列表
（含該 user 的 BKT confidence；未練 = 0）。

設計：
- 一次 outerjoin 取所有 (concept, mastery_for_user)，application 層分群（避免多次 query）
- mastered threshold = 0.8（與 dashboard.queries / generator 一致）
- concept 排序：先 video_order ASC（教學順序），再 tag（穩定 fallback）
- category 排序：依 video_order 最小的 concept 為基準（早出現的主題在前）
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.concept import Concept
from models.mastery import StudentMastery

MASTERED_THRESHOLD = 0.8


@dataclass(frozen=True)
class ConceptMasteryDetail:
    concept_tag: str
    concept_name_zh: str
    video_order: int | None
    difficulty: int
    confidence: float  # 0.0-1.0；未練 = 0


@dataclass(frozen=True)
class CategoryBreakdown:
    name: str
    total: int
    started: int      # 至少有一筆 mastery row
    mastered: int     # confidence >= MASTERED_THRESHOLD
    concepts: list[ConceptMasteryDetail]


@dataclass(frozen=True)
class MasteryBreakdown:
    categories: list[CategoryBreakdown]


def _classify(items: list[ConceptMasteryDetail]) -> tuple[int, int]:
    started = sum(1 for c in items if c.confidence > 0.0)
    mastered = sum(1 for c in items if c.confidence >= MASTERED_THRESHOLD)
    return started, mastered


async def get_mastery_breakdown(
    db: AsyncSession, user_id: UUID
) -> MasteryBreakdown:
    """一次取所有 concepts + outerjoin mastery；application 層分群 + 排序。"""
    rows = (
        await db.execute(
            select(Concept, StudentMastery.confidence)
            .outerjoin(
                StudentMastery,
                (StudentMastery.concept_id == Concept.id)
                & (StudentMastery.user_id == user_id),
            )
        )
    ).all()

    # 分群
    by_category: dict[str, list[ConceptMasteryDetail]] = {}
    earliest_order: dict[str, int] = {}  # 用於 category 排序
    for concept, confidence in rows:
        item = ConceptMasteryDetail(
            concept_tag=concept.tag,
            concept_name_zh=concept.name_zh,
            video_order=concept.video_order,
            difficulty=concept.difficulty_level,
            confidence=float(confidence or 0.0),
        )
        by_category.setdefault(concept.category, []).append(item)
        if concept.video_order is not None:
            current_min = earliest_order.get(concept.category, concept.video_order)
            earliest_order[concept.category] = min(current_min, concept.video_order)

    # 每組內依 video_order ASC（None 排尾），再 tag 穩定排序
    for items in by_category.values():
        items.sort(key=lambda c: (c.video_order is None, c.video_order or 0, c.concept_tag))

    # category 順序：依 earliest_order ASC（無 video_order 的 category 排尾）
    sorted_categories = sorted(
        by_category.keys(),
        key=lambda name: (
            name not in earliest_order,
            earliest_order.get(name, 0),
            name,
        ),
    )

    breakdowns: list[CategoryBreakdown] = []
    for name in sorted_categories:
        items = by_category[name]
        started, mastered = _classify(items)
        breakdowns.append(CategoryBreakdown(
            name=name,
            total=len(items),
            started=started,
            mastered=mastered,
            concepts=items,
        ))

    return MasteryBreakdown(categories=breakdowns)
