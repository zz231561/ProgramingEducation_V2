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
                video_youtube_id=s.get("video_youtube_id"),
                video_duration_seconds=s.get("video_duration_seconds"),
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
        {
            "tag": "first",
            "difficulty": 1,
            "video_youtube_id": "abc123XYZab",
            "video_duration_seconds": 600,
        },
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
    # 6-2c：video metadata 直通到 UnitOut
    assert body["units"][0]["video_youtube_id"] == "abc123XYZab"
    assert body["units"][0]["video_duration_seconds"] == 600
    assert body["units"][1]["video_youtube_id"] is None
    assert body["units"][1]["video_duration_seconds"] is None
    # U2c：concept category 直通（前端據此隱藏課程介紹單元的範例 tab）
    assert body["units"][0]["concept_category"] == "基礎"
    # 6-3c：無 batch 題 → 兩 tab flag 皆 False（資料驅動隱藏 tab）
    assert body["units"][0]["has_concept_quiz"] is False
    assert body["units"][0]["has_coding_exercise"] is False


async def test_unit_tab_flags_reflect_batch_questions(client: AsyncClient):
    """有 batch MC → has_concept_quiz=True；有 batch coding → has_coding_exercise=True。"""
    from models.quiz import Question, QuestionSource

    await _ensure_user(OWNER_PAYLOAD, client)
    await _seed_concepts([{"tag": "with-quiz"}, {"tag": "no-quiz"}])
    async with TestSessionFactory() as db:
        db.add(Question(
            type="multiple_choice", concept_tags=["with-quiz"], bloom_level=3,
            difficulty=2, content={"stem": "x", "options": ["a", "b"], "answer_index": 0},
            explanation="", source=QuestionSource.BATCH.value, validated=True,
        ))
        db.add(Question(
            type="coding", concept_tags=["with-quiz"], bloom_level=3, difficulty=2,
            content={"stem": "impl", "starter_code": ""}, explanation="",
            source=QuestionSource.BATCH.value, validated=True,
        ))
        await db.commit()
    token = encrypt_test_token(OWNER_PAYLOAD)

    created = await client.post(
        "/learning/paths", json={"title": "P"},
        cookies={"authjs.session-token": token},
    )
    resp = await client.get(
        f"/learning/paths/{created.json()['id']}",
        cookies={"authjs.session-token": token},
    )
    units = {u["concept_tag"]: u for u in resp.json()["units"]}
    assert units["with-quiz"]["has_concept_quiz"] is True
    assert units["with-quiz"]["has_coding_exercise"] is True
    assert units["no-quiz"]["has_concept_quiz"] is False
    assert units["no-quiz"]["has_coding_exercise"] is False


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


# === GET /learning/paths/default (3-1c+) ===


async def test_get_default_path_requires_auth(client: AsyncClient):
    resp = await client.get("/learning/paths/default")
    assert resp.status_code == 401


async def test_get_default_path_lazy_seeds_when_none(client: AsyncClient):
    """首次呼叫 → 自動建立預設路徑（標題為 DEFAULT_PATH_TITLE）+ 含 units。"""
    await _ensure_user(OWNER_PAYLOAD, client)
    await _seed_concepts([{"tag": "a"}, {"tag": "b"}])
    token = encrypt_test_token(OWNER_PAYLOAD)

    resp = await client.get(
        "/learning/paths/default",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "C++ 完整課程"
    assert len(body["units"]) == 2
    assert body["units"][0]["status"] == "available"


async def test_get_default_path_returns_existing_when_present(client: AsyncClient):
    """已有路徑 → 回最早建立的那條（不重複 seed）。"""
    await _ensure_user(OWNER_PAYLOAD, client)
    await _seed_concepts([{"tag": "a"}])
    token = encrypt_test_token(OWNER_PAYLOAD)

    # 先手動建一條（非預設標題）
    first = await client.post(
        "/learning/paths",
        json={"title": "我的自訂路徑"},
        cookies={"authjs.session-token": token},
    )
    first_id = first.json()["id"]

    # 呼叫 default → 應回該手動建立的，不另建
    resp = await client.get(
        "/learning/paths/default",
        cookies={"authjs.session-token": token},
    )
    body = resp.json()
    assert body["id"] == first_id
    assert body["title"] == "我的自訂路徑"

    # 確認資料庫只有 1 條
    listing = await client.get(
        "/learning/paths",
        cookies={"authjs.session-token": token},
    )
    assert len(listing.json()["paths"]) == 1


async def test_get_default_path_no_concepts_returns_422(client: AsyncClient):
    """無任何 concept → seed 失敗 → 422 LEARNING_PATH_EMPTY。"""
    await _ensure_user(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)
    resp = await client.get(
        "/learning/paths/default",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 422
