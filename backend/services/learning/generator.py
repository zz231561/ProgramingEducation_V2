"""學習路徑生成 service — 拓撲排序 + 弱項補強（roadmap 3-1b）。

流程：
1. 取概念集（可依 category filter）+ PREREQUISITE 邊 + 學生 mastery
2. 已熟練 (confidence >= skip_mastered_threshold) 概念剔除
3. priority Kahn's 拓撲排序（弱項先排）
4. 寫入 LearningPath + LearningUnit；第一個 unit 設為 'available'，其餘 'locked'

設計取捨：
- **不採 RL**（守則 #7：禁用 OATutor RL；演算法用純 Python 拓撲 + 弱項補強已足夠）
- **未練概念 confidence=0**：StudentMastery row 不存在時視為 0，弱項優先邏輯天然涵蓋 cold start
- **不重複生成**：caller 應自行管理（一個學生可有多條路徑，schema 不限制）
- **content 預留 shape**：3-1b 寫入 `{"summary": "", "examples": [], "exercise_question_ids": []}`
  空骨架；實際 content 由 3-1d 學習單元頁或 LLM 生成 service 後續填入
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.concept import Concept, ConceptEdge, EdgeType
from models.learning import LearningPath, LearningUnit, LearningUnitStatus
from models.mastery import StudentMastery
from services.learning.topology import topological_sort_with_priority

DEFAULT_SKIP_MASTERED_THRESHOLD = 0.8

# Phase 6-1c：標記為這些 category 的 concept 不進學習路徑
# （video_order 1-3 課程簡介 / 環境安裝 / 語言簡介；roadmap.md Phase 6-1c）
EXCLUDED_FROM_PATH_CATEGORIES: tuple[str, ...] = ("課程介紹",)


async def _fetch_concepts(db: AsyncSession, category: str | None) -> list[Concept]:
    stmt = select(Concept).where(
        Concept.category.notin_(EXCLUDED_FROM_PATH_CATEGORIES)
    )
    if category is not None:
        stmt = stmt.where(Concept.category == category)
    return list((await db.execute(stmt)).scalars().all())


async def _fetch_prerequisite_edges(
    db: AsyncSession, concept_ids: set[UUID]
) -> list[tuple[UUID, UUID]]:
    """取與 concept_ids 相關的 PREREQUISITE 邊（src/tgt 都在集合內）。"""
    if not concept_ids:
        return []
    rows = (
        await db.execute(
            select(ConceptEdge.source_id, ConceptEdge.target_id)
            .where(ConceptEdge.edge_type == EdgeType.PREREQUISITE)
            .where(ConceptEdge.source_id.in_(concept_ids))
            .where(ConceptEdge.target_id.in_(concept_ids))
        )
    ).all()
    return [(r[0], r[1]) for r in rows]


async def _fetch_user_confidence(
    db: AsyncSession, user_id: UUID, concept_ids: set[UUID]
) -> dict[UUID, float]:
    """{concept_id: confidence}；未在 mastery 表中的 concept 不會出現（caller 預設 0）。"""
    if not concept_ids:
        return {}
    rows = (
        await db.execute(
            select(StudentMastery.concept_id, StudentMastery.confidence)
            .where(StudentMastery.user_id == user_id)
            .where(StudentMastery.concept_id.in_(concept_ids))
        )
    ).all()
    return {r[0]: r[1] for r in rows}


def _empty_unit_content() -> dict:
    """LearningUnit.content 初始骨架；後續 service 填入實際教學內容。"""
    return {"summary": "", "examples": [], "exercise_question_ids": []}


async def generate_learning_path(
    db: AsyncSession,
    user_id: UUID,
    title: str,
    description: str = "",
    category: str | None = None,
    skip_mastered_threshold: float = DEFAULT_SKIP_MASTERED_THRESHOLD,
) -> LearningPath:
    """生成學習路徑 — 拓撲排序 + 弱項補強。

    Args:
        db: SQLAlchemy async session
        user_id: 學生 UUID
        title: 路徑標題（必填）
        description: 路徑描述（可選）
        category: 限制概念分類（None = 全部 concepts）
        skip_mastered_threshold: confidence ≥ 此值 → 跳過該概念

    Returns:
        建立完成的 LearningPath（含 units 已 commit）

    Raises:
        AppError 422 LEARNING_PATH_EMPTY — 篩選後無概念可組成路徑
    """
    concepts = await _fetch_concepts(db, category)
    if not concepts:
        raise AppError(
            422,
            "LEARNING_PATH_EMPTY",
            f"找不到符合條件的概念（category={category}）",
        )

    concept_ids = {c.id for c in concepts}
    edges = await _fetch_prerequisite_edges(db, concept_ids)
    confidence_map = await _fetch_user_confidence(db, user_id, concept_ids)

    # 篩除已熟練的概念
    selectable = [
        c for c in concepts
        if confidence_map.get(c.id, 0.0) < skip_mastered_threshold
    ]
    if not selectable:
        raise AppError(
            422,
            "LEARNING_PATH_EMPTY",
            "所有相關概念已達熟練門檻，無需新建路徑",
        )

    # 篩除後重算可用 edges（剔除指向已熟練節點的邊）
    selectable_ids = {c.id for c in selectable}
    filtered_edges = [
        (s, t) for s, t in edges if s in selectable_ids and t in selectable_ids
    ]

    # priority Kahn's：弱項優先（confidence 越小越前）
    sorted_ids = topological_sort_with_priority(
        nodes=[c.id for c in selectable],
        edges=filtered_edges,
        priority=confidence_map,
        default_priority=0.0,  # 未練的概念視為最弱項，排前面
    )

    # 寫入 LearningPath
    path = LearningPath(user_id=user_id, title=title, description=description)
    db.add(path)
    await db.flush()  # 取 path.id

    # 寫入 LearningUnits — 第一個 'available'，其餘 'locked'
    for order_index, concept_id in enumerate(sorted_ids):
        unit_status = (
            LearningUnitStatus.AVAILABLE.value
            if order_index == 0
            else LearningUnitStatus.LOCKED.value
        )
        db.add(LearningUnit(
            path_id=path.id,
            concept_id=concept_id,
            order_index=order_index,
            content=_empty_unit_content(),
            status=unit_status,
        ))

    await db.commit()
    await db.refresh(path)
    return path
