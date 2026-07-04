"""Prerequisite 回溯走訪測試（roadmap K1b）。

測試圖（菱形 + 跨層依賴，模擬多對多 DAG）：

    vars(1) ──→ funcs(3) ──┐
      │  └──→ cond(2) ──→ recursion(4)
      └────→ arrays(5)      ↑
                └───────────┘（arrays 也是 recursion 前置 — 模擬跨章依賴）
"""

import pytest

from models.concept import Concept, ConceptEdge, EdgeType
from services.graph import get_prerequisite_closure
from tests.helpers import TestSessionFactory


def _concept(tag: str, order: int, difficulty: int = 1) -> Concept:
    return Concept(
        tag=tag, name_zh=tag, name_en=tag,
        description="", difficulty_level=difficulty,
        category="test", video_order=order,
    )


async def _seed_dag() -> None:
    """建 5 節點多對多 DAG：recursion 依賴 funcs + cond + arrays，全部溯源至 vars。"""
    async with TestSessionFactory() as db:
        nodes = {
            "vars": _concept("vars", 1),
            "cond": _concept("cond", 2),
            "funcs": _concept("funcs", 3),
            "recursion": _concept("recursion", 4, difficulty=4),
            "arrays": _concept("arrays", 5),
        }
        db.add_all(nodes.values())
        await db.flush()

        def edge(src: str, tgt: str) -> ConceptEdge:
            return ConceptEdge(
                source_id=nodes[src].id, target_id=nodes[tgt].id,
                edge_type=EdgeType.PREREQUISITE, weight=1.0,
            )

        db.add_all([
            edge("vars", "cond"),
            edge("vars", "funcs"),
            edge("vars", "arrays"),
            edge("funcs", "recursion"),
            edge("cond", "recursion"),
            edge("arrays", "recursion"),
        ])
        await db.commit()


@pytest.mark.asyncio
async def test_closure_unknown_tag_returns_none():
    result = await _run_closure("no-such-tag")
    assert result is None


@pytest.mark.asyncio
async def test_closure_root_has_no_ancestors():
    await _seed_dag()
    result = await _run_closure("vars")
    assert result is not None
    assert result.ancestors == []


@pytest.mark.asyncio
async def test_closure_multi_parent_full_depth():
    """recursion 的閉包應含全部 4 個先備節點，且 depth 正確。"""
    await _seed_dag()
    result = await _run_closure("recursion")
    assert result is not None

    depth_by_tag = {c.tag: d for c, d in result.ancestors}
    assert depth_by_tag == {"funcs": 1, "cond": 1, "arrays": 1, "vars": 2}

    # 排序：depth 升序（診斷先看最近的前置），同層依 video_order
    tags_in_order = [c.tag for c, _ in result.ancestors]
    assert tags_in_order == ["cond", "funcs", "arrays", "vars"]


@pytest.mark.asyncio
async def test_closure_respects_max_depth():
    """max_depth=1 只回直接前置，不含 vars（depth 2）。"""
    await _seed_dag()
    result = await _run_closure("recursion", max_depth=1)
    assert result is not None
    depth_by_tag = {c.tag: d for c, d in result.ancestors}
    assert depth_by_tag == {"funcs": 1, "cond": 1, "arrays": 1}


@pytest.mark.asyncio
async def test_closure_diamond_no_duplicate():
    """菱形結構（vars 經 cond/funcs 兩路到 recursion）不可重複出現。"""
    await _seed_dag()
    result = await _run_closure("recursion")
    assert result is not None
    tags = [c.tag for c, _ in result.ancestors]
    assert len(tags) == len(set(tags))
    # vars 取最短路徑 depth（BFS 保證）
    assert dict((c.tag, d) for c, d in result.ancestors)["vars"] == 2


async def _run_closure(tag: str, max_depth: int | None = None):
    async with TestSessionFactory() as db:
        return await get_prerequisite_closure(db, tag, max_depth=max_depth)
