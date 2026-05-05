"""Dashboard 精熟度總覽 service + HTTP 整合測試（roadmap 3-3c）。

涵蓋：
- 401
- 空狀態（無 concepts）
- 多 category 分群 + summary 計算
- concept 排序：video_order ASC（None 排尾）+ tag 穩定
- category 排序：依 earliest video_order ASC
- mastered = confidence >= 0.8；started = confidence > 0
- 未練 concept confidence = 0
"""

import uuid

from httpx import AsyncClient
from sqlalchemy import select

from models.concept import Concept
from models.mastery import StudentMastery
from models.user import User
from services.dashboard import get_mastery_breakdown
from tests.helpers import TestSessionFactory, encrypt_test_token

USER = {
    "sub": "mst-user",
    "email": "mst@test.com",
    "name": "MST",
    "googleId": "g-mst-user",
}


async def _ensure_user(client: AsyncClient) -> uuid.UUID:
    token = encrypt_test_token(USER)
    await client.get("/auth/me", cookies={"authjs.session-token": token})
    async with TestSessionFactory() as db:
        return (
            await db.execute(select(User).where(User.google_id == USER["googleId"]))
        ).scalar_one().id


# === auth ===


async def test_mastery_overview_requires_auth(client: AsyncClient):
    resp = await client.get("/dashboard/mastery-overview")
    assert resp.status_code == 401


# === 空狀態 ===


async def test_mastery_overview_empty(client: AsyncClient):
    user_id = await _ensure_user(client)
    async with TestSessionFactory() as db:
        result = await get_mastery_breakdown(db, user_id)
    assert result.categories == []


# === 分群 + summary ===


async def test_mastery_overview_groups_and_summarizes(client: AsyncClient):
    user_id = await _ensure_user(client)
    async with TestSessionFactory() as db:
        # 入門 (video 4-6) 3 concepts；變數型別 (video 8-9) 2 concepts
        for spec in [
            ("cpp-04-x", "概念 A", 4, "入門"),
            ("cpp-05-y", "概念 B", 5, "入門"),
            ("cpp-06-z", "概念 C", 6, "入門"),
            ("cpp-08-p", "概念 D", 8, "變數與型別"),
            ("cpp-09-q", "概念 E", 9, "變數與型別"),
        ]:
            tag, name, order, cat = spec
            db.add(Concept(
                tag=tag, name_zh=name, name_en=tag,
                description="", difficulty_level=1, category=cat, video_order=order,
            ))
        await db.flush()
        # 給 cpp-04 0.9（mastered）；cpp-05 0.5（started not mastered）；cpp-06 無 mastery（0）
        cpp04 = (
            await db.execute(select(Concept).where(Concept.tag == "cpp-04-x"))
        ).scalar_one()
        cpp05 = (
            await db.execute(select(Concept).where(Concept.tag == "cpp-05-y"))
        ).scalar_one()
        for cid, conf in [(cpp04.id, 0.9), (cpp05.id, 0.5)]:
            db.add(StudentMastery(
                user_id=user_id, concept_id=cid, confidence=conf,
                exposure_count=1, success_count=1, error_count=0,
            ))
        await db.commit()

    async with TestSessionFactory() as db:
        result = await get_mastery_breakdown(db, user_id)

    assert len(result.categories) == 2
    intro = next(c for c in result.categories if c.name == "入門")
    assert intro.total == 3
    assert intro.started == 2  # 04 + 05
    assert intro.mastered == 1  # 只有 04 (0.9)
    # concept 排序依 video_order
    assert [c.concept_tag for c in intro.concepts] == ["cpp-04-x", "cpp-05-y", "cpp-06-z"]
    # cpp-06 confidence = 0
    assert intro.concepts[2].confidence == 0.0

    types = next(c for c in result.categories if c.name == "變數與型別")
    assert types.total == 2
    assert types.started == 0  # 都沒練
    assert types.mastered == 0


async def test_mastery_overview_category_order_by_earliest_video(client: AsyncClient):
    """category 排序：依 earliest video_order ASC（早出現主題在前）。"""
    user_id = await _ensure_user(client)
    async with TestSessionFactory() as db:
        # 故意亂插入順序
        for spec in [
            ("cpp-15-x", "x", 15, "運算子"),
            ("cpp-04-x", "x", 4, "入門"),
            ("cpp-29-x", "x", 29, "迴圈"),
            ("cpp-08-x", "x", 8, "變數與型別"),
        ]:
            tag, name, order, cat = spec
            db.add(Concept(
                tag=tag, name_zh=name, name_en=tag,
                description="", difficulty_level=1, category=cat, video_order=order,
            ))
        await db.commit()

    async with TestSessionFactory() as db:
        result = await get_mastery_breakdown(db, user_id)

    # 期望順序：入門(4) < 變數與型別(8) < 運算子(15) < 迴圈(29)
    assert [c.name for c in result.categories] == ["入門", "變數與型別", "運算子", "迴圈"]


async def test_mastery_overview_concept_no_video_order_sorts_last(client: AsyncClient):
    user_id = await _ensure_user(client)
    async with TestSessionFactory() as db:
        for spec in [
            ("z-no-video", "Z", None, "其他"),
            ("a-with-video", "A", 1, "其他"),
            ("b-with-video", "B", 2, "其他"),
        ]:
            tag, name, order, cat = spec
            db.add(Concept(
                tag=tag, name_zh=name, name_en=tag,
                description="", difficulty_level=1, category=cat, video_order=order,
            ))
        await db.commit()

    async with TestSessionFactory() as db:
        result = await get_mastery_breakdown(db, user_id)

    cat = result.categories[0]
    assert [c.concept_tag for c in cat.concepts] == ["a-with-video", "b-with-video", "z-no-video"]


async def test_mastery_overview_unpracticed_confidence_is_zero(client: AsyncClient):
    user_id = await _ensure_user(client)
    async with TestSessionFactory() as db:
        db.add(Concept(
            tag="t", name_zh="X", name_en="X",
            description="", difficulty_level=1, category="基礎", video_order=1,
        ))
        await db.commit()

    async with TestSessionFactory() as db:
        result = await get_mastery_breakdown(db, user_id)
    assert result.categories[0].concepts[0].confidence == 0.0
    assert result.categories[0].started == 0


async def test_mastery_threshold_exactly_08_counts_as_mastered(client: AsyncClient):
    """confidence == 0.8 應算 mastered（>= 不是 >）。"""
    user_id = await _ensure_user(client)
    async with TestSessionFactory() as db:
        c = Concept(
            tag="t", name_zh="X", name_en="X",
            description="", difficulty_level=1, category="基礎", video_order=1,
        )
        db.add(c)
        await db.flush()
        db.add(StudentMastery(
            user_id=user_id, concept_id=c.id, confidence=0.8,
            exposure_count=1, success_count=1, error_count=0,
        ))
        await db.commit()

    async with TestSessionFactory() as db:
        result = await get_mastery_breakdown(db, user_id)
    assert result.categories[0].mastered == 1


# === HTTP integration ===


async def test_mastery_overview_http_returns_complete_payload(client: AsyncClient):
    await _ensure_user(client)
    async with TestSessionFactory() as db:
        db.add(Concept(
            tag="t", name_zh="概念", name_en="X",
            description="", difficulty_level=2, category="基礎", video_order=1,
        ))
        await db.commit()

    token = encrypt_test_token(USER)
    resp = await client.get(
        "/dashboard/mastery-overview",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "categories" in body
    assert len(body["categories"]) == 1
    cat = body["categories"][0]
    assert cat["name"] == "基礎"
    assert cat["total"] == 1
    assert cat["concepts"][0]["concept_name_zh"] == "概念"
    assert cat["concepts"][0]["confidence"] == 0.0
