"""學習路徑 HTTP 整合測試（roadmap 3-1c）。

涵蓋：
- 401 未登入
- POST 生成 → 201 + 完整 detail（含 units）
- POST 無概念 → 422
- GET list → 進度概覽
- GET detail → units 按 order_index 排序 + 含 concept 資訊
- GET / DELETE 跨使用者 → 404
- DELETE → 204 + CASCADE units
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from models.concept import Concept, ConceptEdge, EdgeType
from models.learning import LearningPath, LearningUnit
from models.user import User
from tests.helpers import TestSessionFactory, encrypt_test_token

OWNER_PAYLOAD = {
    "sub": "learn-owner",
    "email": "learn-owner@test.com",
    "name": "Learn Owner",
    "googleId": "g-learn-owner",
}

OTHER_PAYLOAD = {
    "sub": "learn-other",
    "email": "learn-other@test.com",
    "name": "Learn Other",
    "googleId": "g-learn-other",
}


async def _ensure_user(payload: dict, client: AsyncClient) -> uuid.UUID:
    token = encrypt_test_token(payload)
    await client.get("/auth/me", cookies={"authjs.session-token": token})
    async with TestSessionFactory() as db:
        return (
            await db.execute(select(User).where(User.google_id == payload["googleId"]))
        ).scalar_one().id


async def _seed_concepts(specs: list[dict]) -> dict[str, uuid.UUID]:
    async with TestSessionFactory() as db:
        out: dict[str, uuid.UUID] = {}
        for s in specs:
            c = Concept(
                tag=s["tag"],
                name_zh=s.get("name_zh", s["tag"]),
                name_en=s["tag"],
                description="",
                difficulty_level=s.get("difficulty", 1),
                category=s.get("category", "基礎"),
            )
            db.add(c)
            await db.flush()
            out[s["tag"]] = c.id
        await db.commit()
        return out


async def _seed_edges(edges: list[tuple[uuid.UUID, uuid.UUID]]) -> None:
    async with TestSessionFactory() as db:
        for src, tgt in edges:
            db.add(ConceptEdge(
                source_id=src, target_id=tgt, edge_type=EdgeType.PREREQUISITE,
            ))
        await db.commit()


# === auth ===


async def test_create_path_requires_auth(client: AsyncClient):
    resp = await client.post("/learning/paths", json={"title": "X"})
    assert resp.status_code == 401


async def test_list_paths_requires_auth(client: AsyncClient):
    resp = await client.get("/learning/paths")
    assert resp.status_code == 401


async def test_get_path_requires_auth(client: AsyncClient):
    resp = await client.get(f"/learning/paths/{uuid.uuid4()}")
    assert resp.status_code == 401


async def test_delete_path_requires_auth(client: AsyncClient):
    resp = await client.delete(f"/learning/paths/{uuid.uuid4()}")
    assert resp.status_code == 401


# === POST /learning/paths ===


async def test_create_path_returns_full_detail(client: AsyncClient):
    await _ensure_user(OWNER_PAYLOAD, client)
    ids = await _seed_concepts([
        {"tag": "a", "name_zh": "A 概念"},
        {"tag": "b", "name_zh": "B 概念"},
    ])
    await _seed_edges([(ids["a"], ids["b"])])

    token = encrypt_test_token(OWNER_PAYLOAD)
    resp = await client.post(
        "/learning/paths",
        json={"title": "C++ 入門"},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "C++ 入門"
    assert len(body["units"]) == 2
    assert body["units"][0]["concept_tag"] == "a"
    assert body["units"][0]["status"] == "available"
    assert body["units"][1]["concept_tag"] == "b"
    assert body["units"][1]["status"] == "locked"


async def test_create_path_no_concepts_returns_422(client: AsyncClient):
    await _ensure_user(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)
    resp = await client.post(
        "/learning/paths",
        json={"title": "X"},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "LEARNING_PATH_EMPTY"


# === GET /learning/paths ===


async def test_list_paths_empty(client: AsyncClient):
    await _ensure_user(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)
    resp = await client.get(
        "/learning/paths",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    assert resp.json() == {"paths": []}


async def test_list_paths_with_progress_summary(client: AsyncClient):
    await _ensure_user(OWNER_PAYLOAD, client)
    ids = await _seed_concepts([{"tag": "a"}, {"tag": "b"}, {"tag": "c"}])
    await _seed_edges([(ids["a"], ids["b"]), (ids["b"], ids["c"])])
    token = encrypt_test_token(OWNER_PAYLOAD)

    # 生成一條
    await client.post(
        "/learning/paths",
        json={"title": "P1"},
        cookies={"authjs.session-token": token},
    )

    resp = await client.get(
        "/learning/paths",
        cookies={"authjs.session-token": token},
    )
    body = resp.json()
    assert len(body["paths"]) == 1
    summary = body["paths"][0]
    assert summary["title"] == "P1"
    assert summary["total_units"] == 3
    assert summary["available_units"] == 1  # 第一個 unit
    assert summary["completed_units"] == 0


# === GET /learning/paths/{id} ===


async def test_get_path_returns_units_in_order(client: AsyncClient):
    user_id = await _ensure_user(OWNER_PAYLOAD, client)
    ids = await _seed_concepts([
        {"tag": "first", "difficulty": 1},
        {"tag": "second", "difficulty": 2},
    ])
    await _seed_edges([(ids["first"], ids["second"])])
    token = encrypt_test_token(OWNER_PAYLOAD)

    created = await client.post(
        "/learning/paths",
        json={"title": "P"},
        cookies={"authjs.session-token": token},
    )
    path_id = created.json()["id"]

    resp = await client.get(
        f"/learning/paths/{path_id}",
        cookies={"authjs.session-token": token},
    )
    body = resp.json()
    assert body["id"] == path_id
    assert [u["concept_tag"] for u in body["units"]] == ["first", "second"]
    assert body["units"][0]["concept_difficulty"] == 1
    assert body["units"][0]["order_index"] == 0


async def test_get_path_other_user_returns_404(client: AsyncClient):
    await _ensure_user(OWNER_PAYLOAD, client)
    await _ensure_user(OTHER_PAYLOAD, client)
    await _seed_concepts([{"tag": "a"}])
    owner_token = encrypt_test_token(OWNER_PAYLOAD)
    other_token = encrypt_test_token(OTHER_PAYLOAD)

    created = await client.post(
        "/learning/paths",
        json={"title": "P"},
        cookies={"authjs.session-token": owner_token},
    )
    path_id = created.json()["id"]

    resp = await client.get(
        f"/learning/paths/{path_id}",
        cookies={"authjs.session-token": other_token},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "LEARNING_PATH_NOT_FOUND"


async def test_get_nonexistent_path_returns_404(client: AsyncClient):
    await _ensure_user(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)
    resp = await client.get(
        f"/learning/paths/{uuid.uuid4()}",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404


# === DELETE /learning/paths/{id} ===


async def test_delete_path_removes_path(client: AsyncClient):
    await _ensure_user(OWNER_PAYLOAD, client)
    await _seed_concepts([{"tag": "a"}])
    token = encrypt_test_token(OWNER_PAYLOAD)
    created = await client.post(
        "/learning/paths",
        json={"title": "P"},
        cookies={"authjs.session-token": token},
    )
    path_id = created.json()["id"]

    resp = await client.delete(
        f"/learning/paths/{path_id}",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 204

    # 驗證不再存在
    async with TestSessionFactory() as db:
        path = (
            await db.execute(
                select(LearningPath).where(LearningPath.id == uuid.UUID(path_id))
            )
        ).scalar_one_or_none()
        assert path is None


async def test_delete_other_user_path_returns_404(client: AsyncClient):
    await _ensure_user(OWNER_PAYLOAD, client)
    await _ensure_user(OTHER_PAYLOAD, client)
    await _seed_concepts([{"tag": "a"}])
    owner_token = encrypt_test_token(OWNER_PAYLOAD)
    other_token = encrypt_test_token(OTHER_PAYLOAD)

    created = await client.post(
        "/learning/paths",
        json={"title": "P"},
        cookies={"authjs.session-token": owner_token},
    )
    path_id = created.json()["id"]

    resp = await client.delete(
        f"/learning/paths/{path_id}",
        cookies={"authjs.session-token": other_token},
    )
    assert resp.status_code == 404
