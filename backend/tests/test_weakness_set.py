"""6-3d 測試：弱項綜合測驗組組裝（題庫優先 + 並行生成）。

_generate_one 內用 production async_session（parallel），測試以兩種方式覆蓋：
- build_weakness_set：mock _generate_one（隔離 LLM / session），驗題庫優先 + 重用上限
- _generate_one：patch async_session=TestSessionFactory + mock LLM，驗真實生成路徑
"""

from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.concept import Concept
from models.mastery import StudentMastery
from models.quiz import Question, QuestionSource, QuestionType
from models.user import User
from services.quiz import weakness_set
from services.quiz.weakness_set import build_weakness_set
from services.quiz.weakness_set_plan import QuestionPlan
from tests.helpers import TestSessionFactory


async def _seed_user() -> uuid.UUID:
    async with TestSessionFactory() as db:
        u = User(google_id=f"g-{uuid.uuid4()}", email=f"{uuid.uuid4()}@t.com", name="x")
        db.add(u)
        await db.commit()
        return u.id


async def _seed_concept(tag: str) -> uuid.UUID:
    async with TestSessionFactory() as db:
        c = Concept(
            tag=tag, name_zh=tag, name_en=tag, description="",
            difficulty_level=2, category="基礎",
        )
        db.add(c)
        await db.commit()
        return c.id


async def _seed_weak_mastery(user_id: uuid.UUID, concept_id: uuid.UUID):
    async with TestSessionFactory() as db:
        db.add(StudentMastery(
            user_id=user_id, concept_id=concept_id, confidence=0.15,
            exposure_count=3, success_count=0,
            last_practiced_at=datetime.now(timezone.utc),
        ))
        await db.commit()


async def _seed_bank_mc(concept_tag: str, n: int) -> None:
    async with TestSessionFactory() as db:
        for _ in range(n):
            db.add(Question(
                type="multiple_choice", concept_tags=[concept_tag], bloom_level=3,
                difficulty=2,
                content={"stem": "BANK", "options": ["a", "b"], "answer_index": 0},
                explanation="", source=QuestionSource.GENERATED.value, validated=True,
            ))
        await db.commit()


async def _fake_generate_one(plan: QuestionPlan):
    """模擬生成：在 test DB 建一題 validated 並回傳 id。"""
    async with TestSessionFactory() as db:
        tags = [plan.target.tag] + [e.tag for e in plan.extra]
        q = Question(
            type=plan.question_type.value, concept_tags=tags, bloom_level=3,
            difficulty=2, content={"stem": "gen", "options": ["a", "b"], "answer_index": 0},
            explanation="", source=QuestionSource.GENERATED.value, validated=True,
        )
        db.add(q)
        await db.commit()
        return q.id


@pytest.mark.asyncio
async def test_build_empty_when_no_weak():
    uid = await _seed_user()
    async with TestSessionFactory() as db:
        result = await build_weakness_set(db, uid, 10)
    assert result == []


@pytest.mark.asyncio
async def test_build_reuse_capped_at_30_percent():
    """題庫充足時，重用題數 ≤ 30% × count，其餘現生。"""
    uid = await _seed_user()
    cid = await _seed_concept("weak-c")
    await _seed_weak_mastery(uid, cid)
    await _seed_bank_mc("weak-c", 20)  # 題庫充足

    with patch.object(weakness_set, "_generate_one", new=_fake_generate_one):
        async with TestSessionFactory() as db:
            result = await build_weakness_set(db, uid, 10)

    assert len(result) == 10
    # bank 題 stem="BANK"、現生題 stem="gen"——重用上限 int(10*0.3)=3
    reused = [q for q in result if q.content.get("stem") == "BANK"]
    assert len(reused) <= 3
    assert len(reused) >= 1  # 題庫充足時應有重用


@pytest.mark.asyncio
async def test_build_generates_when_bank_empty():
    """題庫無題 → 全部現生（mock），數量符合 count。"""
    uid = await _seed_user()
    cid = await _seed_concept("weak-c")
    await _seed_weak_mastery(uid, cid)

    with patch.object(weakness_set, "_generate_one", new=_fake_generate_one):
        async with TestSessionFactory() as db:
            result = await build_weakness_set(db, uid, 10)

    assert len(result) == 10


# === _generate_one 真實路徑（patch async_session + mock LLM）===


def _mock_completion(content: str) -> MagicMock:
    msg = MagicMock(); msg.content = content
    choice = MagicMock(); choice.message = msg
    resp = MagicMock(); resp.choices = [choice]
    return resp


_MC_JSON = json.dumps({
    "stem": "下列何者正確？", "options": ["a", "b"], "answer_index": 0,
    "explanation": "因為 a",
})
_VALIDATOR_JSON = json.dumps({
    "answer_correct": True, "answer_reason": "ok", "concept_fits": True,
    "concept_reason": "ok", "bloom_appropriate": True, "bloom_reason": "ok",
    "point_meaningful": True, "point_reason": "ok",
})


@contextmanager
def _patched_gen_pipeline():
    gen_client = AsyncMock()
    gen_client.chat.completions.create = AsyncMock(return_value=_mock_completion(_MC_JSON))
    val_client = AsyncMock()
    val_client.chat.completions.create = AsyncMock(return_value=_mock_completion(_VALIDATOR_JSON))
    with (
        patch.object(weakness_set, "async_session", TestSessionFactory),
        patch("services.quiz.generate._get_client", return_value=gen_client),
        patch("services.quiz.validate._get_client", return_value=val_client),
        patch("services.quiz.generate.retrieve_chunks", AsyncMock(return_value=[])),
        patch("services.quiz.generate.get_chunks_by_video_order", AsyncMock(return_value=[])),
    ):
        yield


@pytest.mark.asyncio
async def test_generate_one_persists_validated_question():
    await _seed_concept("weak-c")
    async with TestSessionFactory() as db:
        from sqlalchemy import select
        target = (await db.execute(
            select(Concept).where(Concept.tag == "weak-c")
        )).scalar_one()

    plan = QuestionPlan(QuestionType.MULTIPLE_CHOICE, target)
    with _patched_gen_pipeline():
        qid = await weakness_set._generate_one(plan)

    assert qid is not None
    async with TestSessionFactory() as db:
        q = await db.get(Question, qid)
        assert q is not None and q.validated is True
