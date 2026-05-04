"""知識圖譜 service + API route 測試。

涵蓋：
- queries.get_full_graph：空圖 / 有資料
- queries.get_concept_neighborhood：tag 不存在 / 無鄰居 / 多向鄰居
- API GET /concepts/graph：未登入 401 / 登入回傳完整圖
- API GET /concepts/{tag}：未登入 401 / 不存在 404 / 鄰居方向正確
"""

import uuid

import pytest
from httpx import AsyncClient

from models.concept import Concept, ConceptEdge, EdgeType
from services.graph import get_concept_neighborhood, get_full_graph
from tests.helpers import TestSessionFactory, encrypt_test_token

STUDENT_PAYLOAD = {
    "sub": "graph-test-user",
    "email": "graph@test.com",
    "name": "Graph Tester",
}


async def _seed_graph() -> dict[str, uuid.UUID]:
    """建立 3 節點 (a→b, a→c) 的小圖，回傳 {tag: id} 對照表。"""
    async with TestSessionFactory() as db:
        a = Concept(
            tag="syntax-basic", name_zh="基礎語法", name_en="Basic Syntax",
            description="", difficulty_level=1, category="基礎語法",
        )
        b = Concept(
            tag="control-flow", name_zh="流程控制", name_en="Control Flow",
            description="", difficulty_level=1, category="基礎語法",
        )
        c = Concept(
            tag="recursion", name_zh="遞迴", name_en="Recursion",
            description="", difficulty_level=3, category="演算法",
        )
        db.add_all([a, b, c])
        await db.flush()
        ab = ConceptEdge(source_id=a.id, target_id=b.id, edge_type=EdgeType.PREREQUISITE, weight=1.0)
        ac = ConceptEdge(source_id=a.id, target_id=c.id, edge_type=EdgeType.RELATED, weight=0.5)
        db.add_all([ab, ac])
        await db.commit()
        return {a.tag: a.id, b.tag: b.id, c.tag: c.id}


# === Service 層 ===

@pytest.mark.asyncio
async def test_get_full_graph_empty():
    async with TestSessionFactory() as db:
        snapshot = await get_full_graph(db)
        assert snapshot.concepts == []
        assert snapshot.edges == []


@pytest.mark.asyncio
async def test_get_full_graph_returns_all():
    await _seed_graph()
    async with TestSessionFactory() as db:
        snapshot = await get_full_graph(db)
        assert len(snapshot.concepts) == 3
        assert len(snapshot.edges) == 2
        # 排序穩定（依 tag）
        tags = [c.tag for c in snapshot.concepts]
        assert tags == sorted(tags)


@pytest.mark.asyncio
async def test_neighborhood_returns_none_for_unknown_tag():
    async with TestSessionFactory() as db:
        result = await get_concept_neighborhood(db, "no-such-tag")
        assert result is None


@pytest.mark.asyncio
async def test_neighborhood_isolated_node_has_no_neighbors():
    """節點存在但沒有任何邊 → edges 與 neighbors 都空。"""
    async with TestSessionFactory() as db:
        c = Concept(
            tag="lonely", name_zh="孤立", name_en="Lonely",
            description="", difficulty_level=1, category="基礎語法",
        )
        db.add(c)
        await db.commit()

    async with TestSessionFactory() as db:
        nbhd = await get_concept_neighborhood(db, "lonely")
        assert nbhd is not None
        assert nbhd.center.tag == "lonely"
        assert nbhd.edges == []
        assert nbhd.neighbors_by_id == {}


@pytest.mark.asyncio
async def test_neighborhood_returns_both_directions():
    """center=control-flow 應同時看到 incoming (syntax-basic→control-flow)。"""
    await _seed_graph()
    async with TestSessionFactory() as db:
        nbhd = await get_concept_neighborhood(db, "control-flow")
        assert nbhd is not None
        assert nbhd.center.tag == "control-flow"
        assert len(nbhd.edges) == 1  # 只有 a→b 一條邊觸碰 b
        assert len(nbhd.neighbors_by_id) == 1
        # 鄰居應為 syntax-basic（邊的起點）
        neighbor = next(iter(nbhd.neighbors_by_id.values()))
        assert neighbor.tag == "syntax-basic"


# === API route ===

async def test_graph_route_requires_auth(client: AsyncClient):
    resp = await client.get("/concepts/graph")
    assert resp.status_code == 401


async def test_graph_route_returns_cytoscape_format(client: AsyncClient):
    await _seed_graph()
    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.get(
        "/concepts/graph",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["nodes"]) == 3
    assert len(body["edges"]) == 2
    # 邊欄位用 source/target（Cytoscape 慣例），非 source_id/target_id
    edge = body["edges"][0]
    assert "source" in edge and "target" in edge
    assert "edge_type" in edge


async def test_concept_detail_route_404(client: AsyncClient):
    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.get(
        "/concepts/no-such-tag",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "CONCEPT_NOT_FOUND"


async def test_concept_detail_route_returns_directed_neighbors(client: AsyncClient):
    """syntax-basic 應有 2 個 outgoing 鄰居（→control-flow, →recursion），無 incoming。"""
    await _seed_graph()
    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.get(
        "/concepts/syntax-basic",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["concept"]["tag"] == "syntax-basic"
    assert len(body["neighbors"]) == 2
    directions = {n["direction"] for n in body["neighbors"]}
    assert directions == {"outgoing"}
    neighbor_tags = {n["concept"]["tag"] for n in body["neighbors"]}
    assert neighbor_tags == {"control-flow", "recursion"}
