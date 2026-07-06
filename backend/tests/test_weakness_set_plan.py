"""6-3d 測試：弱項綜合測驗組藍圖與節點選擇（不呼叫 LLM）。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from models.concept import Concept, ConceptEdge, EdgeType
from models.mastery import StudentMastery
from models.quiz import QuestionType
from models.user import User
from services.quiz.weakness_set_plan import (
    MasterySnapshot,
    SetBlueprint,
    compute_blueprint,
    mastery_snapshot,
    plan_questions,
)
from tests.helpers import TestSessionFactory


# === compute_blueprint（純函式）===


def test_blueprint_coding_count_by_size():
    assert compute_blueprint(10, 0.0).coding == 1
    assert compute_blueprint(25, 0.0).coding == 2


def test_blueprint_total_matches_count():
    for count in (10, 25):
        for m in (0.0, 0.5, 1.0):
            assert compute_blueprint(count, m).total == count


def test_blueprint_multi_grows_with_mastery():
    low = compute_blueprint(25, 0.0)
    high = compute_blueprint(25, 1.0)
    assert high.multi_mc > low.multi_mc
    assert high.single_mc < low.single_mc


def test_blueprint_clamps_mastery():
    # 超界 mastery 不應爆量
    bp = compute_blueprint(10, 5.0)
    assert bp.total == 10
    assert bp.multi_mc <= bp.single_mc + bp.multi_mc


# === mastery_snapshot ===


async def _seed_user() -> uuid.UUID:
    async with TestSessionFactory() as db:
        u = User(google_id=f"g-{uuid.uuid4()}", email=f"{uuid.uuid4()}@t.com", name="x")
        db.add(u)
        await db.commit()
        return u.id


async def _seed_concept(tag: str, difficulty: int = 3) -> uuid.UUID:
    async with TestSessionFactory() as db:
        c = Concept(
            tag=tag, name_zh=tag, name_en=tag, description="",
            difficulty_level=difficulty, category="基礎",
        )
        db.add(c)
        await db.commit()
        return c.id


async def _seed_mastery(user_id: uuid.UUID, concept_id: uuid.UUID, confidence: float):
    async with TestSessionFactory() as db:
        db.add(StudentMastery(
            user_id=user_id, concept_id=concept_id, confidence=confidence,
            exposure_count=3, success_count=1,
            last_practiced_at=datetime.now(timezone.utc),
        ))
        await db.commit()


@pytest.mark.asyncio
async def test_snapshot_classifies_weak_and_mastered():
    uid = await _seed_user()
    weak_id = await _seed_concept("weak-c")
    strong_id = await _seed_concept("strong-c")
    await _seed_mastery(uid, weak_id, 0.2)   # < 0.4 → weak
    await _seed_mastery(uid, strong_id, 0.8)  # >= 0.6 → mastered

    async with TestSessionFactory() as db:
        snap = await mastery_snapshot(db, uid)

    assert [c.tag for c in snap.weak] == ["weak-c"]
    assert "strong-c" in snap.mastered_tags
    assert 0.0 < snap.overall < 1.0


@pytest.mark.asyncio
async def test_snapshot_empty_when_no_mastery():
    uid = await _seed_user()
    async with TestSessionFactory() as db:
        snap = await mastery_snapshot(db, uid)
    assert snap.overall == 0.0
    assert snap.weak == []
    assert snap.mastered_tags == set()


# === plan_questions ===


@pytest.mark.asyncio
async def test_plan_produces_single_multi_coding():
    uid = await _seed_user()
    # target 弱項 + 一個已掌握前置（當綜合/鷹架相關節點）
    tgt = await _seed_concept("target-c")
    pre = await _seed_concept("prereq-c")
    async with TestSessionFactory() as db:
        db.add(ConceptEdge(source_id=pre, target_id=tgt, edge_type=EdgeType.PREREQUISITE))
        await db.commit()

    snapshot = MasterySnapshot(
        overall=0.3,
        weak=[(await _load_concept("target-c"))],
        mastered_tags={"prereq-c"},
    )
    blueprint = SetBlueprint(single_mc=2, multi_mc=1, coding=1)

    async with TestSessionFactory() as db:
        plans = await plan_questions(db, snapshot, blueprint)

    by_type = [(p.question_type, p.target.tag, [e.tag for e in p.extra]) for p in plans]
    single = [p for p in by_type if p[0] == QuestionType.MULTIPLE_CHOICE and not p[2]]
    multi = [p for p in by_type if p[0] == QuestionType.MULTIPLE_CHOICE and p[2]]
    coding = [p for p in by_type if p[0] == QuestionType.CODING]

    assert len(single) == 2
    assert len(multi) == 1
    assert len(coding) == 1
    # 綜合 MC + coding 都應帶到前置概念
    assert "prereq-c" in multi[0][2]
    assert "prereq-c" in coding[0][2]


@pytest.mark.asyncio
async def test_plan_empty_when_no_weak():
    uid = await _seed_user()
    snapshot = MasterySnapshot(overall=0.9, weak=[], mastered_tags=set())
    blueprint = SetBlueprint(single_mc=3, multi_mc=2, coding=1)
    async with TestSessionFactory() as db:
        plans = await plan_questions(db, snapshot, blueprint)
    assert plans == []


async def _load_concept(tag: str) -> Concept:
    from sqlalchemy import select
    async with TestSessionFactory() as db:
        return (await db.execute(select(Concept).where(Concept.tag == tag))).scalar_one()
