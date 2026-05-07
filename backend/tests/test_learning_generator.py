"""學習路徑生成 integration tests（roadmap 3-1b）— DB 級別驗證。

涵蓋：
- 無概念 → 422 LEARNING_PATH_EMPTY
- 全部已熟練 → 422 LEARNING_PATH_EMPTY
- 拓撲順序 + 弱項優先 同層內弱項先排
- 第一個 unit 設為 'available'，其餘 'locked'
- 跳過已熟練的概念
- category filter 限制範圍
- 邊指向已熟練節點 → 過濾後不影響拓撲
"""

import uuid

import pytest
from sqlalchemy import select

from core.errors import AppError
from models.concept import Concept, ConceptEdge, EdgeType
from models.learning import LearningPath, LearningUnit, LearningUnitStatus
from models.mastery import StudentMastery
from models.user import User
from services.learning import generate_learning_path
from tests.helpers import TestSessionFactory


async def _seed_user() -> uuid.UUID:
    async with TestSessionFactory() as db:
        u = User(
            email=f"gen-{uuid.uuid4().hex[:8]}@test.com",
            name="Gen",
            google_id=f"g-{uuid.uuid4().hex[:8]}",
        )
        db.add(u)
        await db.commit()
        await db.refresh(u)
        return u.id


async def _seed_concepts(specs: list[dict]) -> dict[str, uuid.UUID]:
    """specs: [{"tag": "...", "category": "...", "difficulty": int}]; 回 {tag: id}。"""
    async with TestSessionFactory() as db:
        out: dict[str, uuid.UUID] = {}
        for s in specs:
            c = Concept(
                tag=s["tag"],
                name_zh=s["tag"],
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
    """edges: [(src_id, tgt_id)] 都建為 PREREQUISITE。"""
    async with TestSessionFactory() as db:
        for src, tgt in edges:
            db.add(ConceptEdge(
                source_id=src, target_id=tgt, edge_type=EdgeType.PREREQUISITE,
            ))
        await db.commit()


async def _seed_mastery(user_id: uuid.UUID, mastery: dict[uuid.UUID, float]) -> None:
    async with TestSessionFactory() as db:
        for cid, conf in mastery.items():
            db.add(StudentMastery(
                user_id=user_id, concept_id=cid, confidence=conf,
                exposure_count=1, success_count=1, error_count=0,
            ))
        await db.commit()


async def _read_units_in_order(path_id: uuid.UUID) -> list[LearningUnit]:
    async with TestSessionFactory() as db:
        return list(
            (
                await db.execute(
                    select(LearningUnit)
                    .where(LearningUnit.path_id == path_id)
                    .order_by(LearningUnit.order_index)
                )
            ).scalars().all()
        )


# === 422 邊界 ===


@pytest.mark.asyncio
async def test_generate_no_concepts_raises_422():
    user_id = await _seed_user()
    async with TestSessionFactory() as db:
        with pytest.raises(AppError) as exc:
            await generate_learning_path(db, user_id, title="X")
    assert exc.value.status_code == 422
    assert exc.value.error == "LEARNING_PATH_EMPTY"


@pytest.mark.asyncio
async def test_generate_all_mastered_raises_422():
    user_id = await _seed_user()
    ids = await _seed_concepts([{"tag": "a"}, {"tag": "b"}])
    await _seed_mastery(user_id, {ids["a"]: 0.9, ids["b"]: 0.95})

    async with TestSessionFactory() as db:
        with pytest.raises(AppError) as exc:
            await generate_learning_path(db, user_id, title="X")
    assert exc.value.error == "LEARNING_PATH_EMPTY"


@pytest.mark.asyncio
async def test_category_filter_with_no_match_raises_422():
    user_id = await _seed_user()
    await _seed_concepts([{"tag": "a", "category": "基礎"}])

    async with TestSessionFactory() as db:
        with pytest.raises(AppError):
            await generate_learning_path(db, user_id, title="X", category="進階")


# === 正向路徑生成 ===


@pytest.mark.asyncio
async def test_generate_linear_chain_path():
    """a → b → c；無 mastery → 排序 a, b, c；第一個 available 其餘 locked。"""
    user_id = await _seed_user()
    ids = await _seed_concepts([{"tag": "a"}, {"tag": "b"}, {"tag": "c"}])
    await _seed_edges([(ids["a"], ids["b"]), (ids["b"], ids["c"])])

    async with TestSessionFactory() as db:
        path = await generate_learning_path(db, user_id, title="C++ 基礎")
    assert path.title == "C++ 基礎"

    units = await _read_units_in_order(path.id)
    assert [u.concept_id for u in units] == [ids["a"], ids["b"], ids["c"]]
    assert units[0].status == LearningUnitStatus.AVAILABLE.value
    assert all(u.status == LearningUnitStatus.LOCKED.value for u in units[1:])


@pytest.mark.asyncio
async def test_generate_skips_mastered_but_keeps_others():
    """a (已熟練 0.9) → b (0.3) → c (0.0)；a 跳過，路徑 = [b, c]。"""
    user_id = await _seed_user()
    ids = await _seed_concepts([{"tag": "a"}, {"tag": "b"}, {"tag": "c"}])
    await _seed_edges([(ids["a"], ids["b"]), (ids["b"], ids["c"])])
    await _seed_mastery(user_id, {ids["a"]: 0.9, ids["b"]: 0.3})

    async with TestSessionFactory() as db:
        path = await generate_learning_path(db, user_id, title="X")

    units = await _read_units_in_order(path.id)
    assert [u.concept_id for u in units] == [ids["b"], ids["c"]]


@pytest.mark.asyncio
async def test_weak_concept_prioritized_within_topological_layer():
    """無依賴的 a/b/c；b 弱項 (0.1) → b 應排第一。"""
    user_id = await _seed_user()
    ids = await _seed_concepts([{"tag": "a"}, {"tag": "b"}, {"tag": "c"}])
    await _seed_mastery(user_id, {ids["a"]: 0.5, ids["b"]: 0.1, ids["c"]: 0.4})

    async with TestSessionFactory() as db:
        path = await generate_learning_path(db, user_id, title="X")

    units = await _read_units_in_order(path.id)
    # b (0.1) 最弱 → 第一；c (0.4) 次之；a (0.5) 最後
    assert [u.concept_id for u in units] == [ids["b"], ids["c"], ids["a"]]


@pytest.mark.asyncio
async def test_unit_content_initialized_with_empty_skeleton():
    user_id = await _seed_user()
    ids = await _seed_concepts([{"tag": "x"}])

    async with TestSessionFactory() as db:
        path = await generate_learning_path(db, user_id, title="X")

    units = await _read_units_in_order(path.id)
    assert units[0].content == {
        "summary": "", "examples": [], "exercise_question_ids": [],
    }


@pytest.mark.asyncio
async def test_category_filter_limits_concepts():
    user_id = await _seed_user()
    ids = await _seed_concepts([
        {"tag": "basic1", "category": "基礎"},
        {"tag": "basic2", "category": "基礎"},
        {"tag": "advanced1", "category": "進階"},
    ])

    async with TestSessionFactory() as db:
        path = await generate_learning_path(
            db, user_id, title="基礎篇", category="基礎"
        )

    units = await _read_units_in_order(path.id)
    unit_concept_ids = {u.concept_id for u in units}
    assert unit_concept_ids == {ids["basic1"], ids["basic2"]}


@pytest.mark.asyncio
async def test_edge_to_mastered_concept_does_not_break_topology():
    """a (已熟練) → b (新)；a 篩除後 b 應自由排第一。"""
    user_id = await _seed_user()
    ids = await _seed_concepts([{"tag": "a"}, {"tag": "b"}])
    await _seed_edges([(ids["a"], ids["b"])])
    await _seed_mastery(user_id, {ids["a"]: 0.9})  # a 熟練

    async with TestSessionFactory() as db:
        path = await generate_learning_path(db, user_id, title="X")

    units = await _read_units_in_order(path.id)
    assert [u.concept_id for u in units] == [ids["b"]]
    assert units[0].status == LearningUnitStatus.AVAILABLE.value


# === Phase 6-1c：課程介紹 category 排除 ===


@pytest.mark.asyncio
async def test_intro_category_concepts_excluded_from_path():
    """category='課程介紹'（如 video 1-3）即使在 DB 也不進路徑。"""
    user_id = await _seed_user()
    ids = await _seed_concepts([
        {"tag": "intro1", "category": "課程介紹"},
        {"tag": "intro2", "category": "課程介紹"},
        {"tag": "real1", "category": "基礎"},
    ])

    async with TestSessionFactory() as db:
        path = await generate_learning_path(db, user_id, title="X")

    units = await _read_units_in_order(path.id)
    unit_concept_ids = {u.concept_id for u in units}
    assert unit_concept_ids == {ids["real1"]}
    assert ids["intro1"] not in unit_concept_ids
    assert ids["intro2"] not in unit_concept_ids


@pytest.mark.asyncio
async def test_all_intro_category_raises_422():
    """全部 concept 都是課程介紹 → filter 後空集合 → 422。"""
    user_id = await _seed_user()
    await _seed_concepts([
        {"tag": "intro1", "category": "課程介紹"},
        {"tag": "intro2", "category": "課程介紹"},
    ])

    async with TestSessionFactory() as db:
        with pytest.raises(AppError) as exc:
            await generate_learning_path(db, user_id, title="X")
    assert exc.value.error == "LEARNING_PATH_EMPTY"
