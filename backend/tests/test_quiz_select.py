"""出題 Select 階段測試。

涵蓋：
- 學生無 mastery → []
- 只有強項（confidence >= 0.4）→ []
- 未互動（exposure_count = 0）即使 confidence 低也不入選
- 純弱項排序：confidence 越低越前面
- 中心度加權：被多個概念依賴的弱項排前面
- top_k 截斷
"""

import uuid

import pytest

from models.concept import Concept, ConceptEdge, EdgeType
from models.mastery import StudentMastery
from services.quiz import (
    CENTRALITY_BONUS,
    WEAK_THRESHOLD,
    select_weak_concepts,
)
from tests.helpers import TestSessionFactory


def _make_concept(tag: str, difficulty: int = 1) -> Concept:
    return Concept(
        tag=tag,
        name_zh=tag,
        name_en=tag,
        description="",
        difficulty_level=difficulty,
        category="基礎語法",
    )


async def _seed(
    weak: list[tuple[str, float, int]] | None = None,
    strong: list[tuple[str, float, int]] | None = None,
    edges: list[tuple[str, str]] | None = None,
) -> tuple[uuid.UUID, dict[str, uuid.UUID]]:
    """建立 user + concepts + 指定 mastery 與 prerequisite edges。

    weak/strong: list of (tag, confidence, exposure_count)
    edges: list of (source_tag, target_tag) — prerequisite 邊
    """
    user_id = uuid.uuid4()
    weak = weak or []
    strong = strong or []
    edges = edges or []

    all_tags = {tag for tag, _, _ in weak} | {tag for tag, _, _ in strong}
    all_tags |= {s for s, _ in edges} | {t for _, t in edges}

    tag_to_id: dict[str, uuid.UUID] = {}
    async with TestSessionFactory() as db:
        for tag in all_tags:
            c = _make_concept(tag)
            db.add(c)
            await db.flush()
            tag_to_id[tag] = c.id

        for tag, conf, exposure in weak + strong:
            db.add(
                StudentMastery(
                    user_id=user_id,
                    concept_id=tag_to_id[tag],
                    confidence=conf,
                    exposure_count=exposure,
                    success_count=0,
                    error_count=0,
                )
            )
        for src_tag, tgt_tag in edges:
            db.add(
                ConceptEdge(
                    source_id=tag_to_id[src_tag],
                    target_id=tag_to_id[tgt_tag],
                    edge_type=EdgeType.PREREQUISITE,
                    weight=1.0,
                )
            )
        await db.commit()
    return user_id, tag_to_id


# === 邊界條件 ===


@pytest.mark.asyncio
async def test_no_mastery_returns_empty():
    user_id, _ = await _seed()
    async with TestSessionFactory() as db:
        result = await select_weak_concepts(db, user_id)
    assert result == []


@pytest.mark.asyncio
async def test_only_strong_returns_empty():
    """所有 mastery confidence >= threshold → 沒有弱項。"""
    user_id, _ = await _seed(
        strong=[("a", 0.9, 5), ("b", 0.5, 3), ("c", 0.4, 2)],
    )
    async with TestSessionFactory() as db:
        result = await select_weak_concepts(db, user_id)
    assert result == []


@pytest.mark.asyncio
async def test_unexposed_low_confidence_not_selected():
    """confidence 雖低但 exposure_count = 0 → 視為未接觸不入選。"""
    user_id, _ = await _seed(weak=[("a", 0.1, 0)])
    async with TestSessionFactory() as db:
        result = await select_weak_concepts(db, user_id)
    assert result == []


# === 主要邏輯 ===


@pytest.mark.asyncio
async def test_pure_weak_ordering_by_confidence():
    """無圖邊時，越弱越前面。"""
    user_id, _ = await _seed(
        weak=[("low", 0.1, 2), ("mid", 0.3, 2), ("high", 0.39, 2)],
    )
    async with TestSessionFactory() as db:
        result = await select_weak_concepts(db, user_id)
    tags = [c.tag for c in result]
    assert tags == ["low", "mid", "high"]


@pytest.mark.asyncio
async def test_centrality_bonus_promotes_hub_concepts():
    """foundation 弱項（被很多依賴）應排在獨立弱項前面。

    foundation 有 3 個出邊（被 dep1/dep2/dep3 依賴），confidence 0.3
    independent 沒有出邊，confidence 0.2（看起來更弱）

    score(foundation) = (1-0.3) * (1 + 0.2*3) = 0.7 * 1.6 = 1.12
    score(independent) = (1-0.2) * 1 = 0.8
    → foundation 排前面
    """
    user_id, _ = await _seed(
        weak=[("foundation", 0.3, 5), ("independent", 0.2, 5)],
        strong=[("dep1", 0.9, 2), ("dep2", 0.9, 2), ("dep3", 0.9, 2)],
        edges=[
            ("foundation", "dep1"),
            ("foundation", "dep2"),
            ("foundation", "dep3"),
        ],
    )
    async with TestSessionFactory() as db:
        result = await select_weak_concepts(db, user_id)
    tags = [c.tag for c in result]
    assert tags[0] == "foundation"
    assert tags[1] == "independent"


@pytest.mark.asyncio
async def test_top_k_limits_result():
    """top_k=2 → 最多 2 筆。"""
    user_id, _ = await _seed(
        weak=[
            ("a", 0.1, 2),
            ("b", 0.2, 2),
            ("c", 0.3, 2),
            ("d", 0.39, 2),
        ],
    )
    async with TestSessionFactory() as db:
        result = await select_weak_concepts(db, user_id, top_k=2)
    assert len(result) == 2
    assert [c.tag for c in result] == ["a", "b"]


@pytest.mark.asyncio
async def test_threshold_constant_sane():
    assert 0 < WEAK_THRESHOLD < 1
    assert 0 < CENTRALITY_BONUS < 1
