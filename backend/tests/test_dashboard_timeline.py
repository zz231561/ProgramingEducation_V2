"""Dashboard 時間線 service + HTTP 整合測試（roadmap 3-3b）。

涵蓋：
- 401
- 空狀態回 []
- 3 種事件 type 都正確
- 合併排序（最近在前）
- limit clamp（每類各取 limit、merge 後再取 limit）
- quiz is_correct 欄位 / reflection 品質分數呈現 / unit completed 鎖在已完成
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from models.concept import Concept
from models.learning import LearningPath, LearningUnit, LearningUnitStatus
from models.quiz import Question, StudentAnswer
from models.reflection import Reflection
from models.user import User
from services.dashboard import list_recent_activities
from tests.helpers import TestSessionFactory, encrypt_test_token

USER = {
    "sub": "tl-user",
    "email": "tl@test.com",
    "name": "TL",
    "googleId": "g-tl-user",
}


async def _ensure_user(client: AsyncClient) -> uuid.UUID:
    token = encrypt_test_token(USER)
    await client.get("/auth/me", cookies={"authjs.session-token": token})
    async with TestSessionFactory() as db:
        return (
            await db.execute(select(User).where(User.google_id == USER["googleId"]))
        ).scalar_one().id


# === HTTP auth ===


async def test_timeline_requires_auth(client: AsyncClient):
    resp = await client.get("/dashboard/timeline")
    assert resp.status_code == 401


# === 空狀態 ===


async def test_timeline_empty(client: AsyncClient):
    user_id = await _ensure_user(client)
    async with TestSessionFactory() as db:
        items = await list_recent_activities(db, user_id, limit=10)
    assert items == []


# === 三種事件 ===


async def test_timeline_includes_three_event_types(client: AsyncClient):
    user_id = await _ensure_user(client)
    now = datetime.now(timezone.utc)

    async with TestSessionFactory() as db:
        # 1. quiz
        q = Question(
            type="multiple_choice", concept_tags=["t"],
            bloom_level=3, difficulty=2,
            content={"stem": "選 int", "options": ["a", "b"], "answer_index": 0},
            explanation="", source="generated", validated=True,
        )
        db.add(q)
        await db.flush()
        db.add(StudentAnswer(
            user_id=user_id, question_id=q.id,
            answer={"selected": 0}, is_correct=True,
            time_spent_seconds=5, hint_level_used=1, feedback="",
            answered_at=now - timedelta(hours=1),
        ))
        # 2. reflection
        db.add(Reflection(
            user_id=user_id, source_type="quiz", source_id=q.id,
            problem_understanding="x", planned_steps=["a", "b"],
            expected_concepts="x", quality_score=0.85,
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(hours=2),
        ))
        # 3. unit_completed — 需 path + concept
        c = Concept(
            tag="cpp-04-x", name_zh="撰寫第一個 C++ 程式", name_en="X",
            description="", difficulty_level=1, category="入門",
            video_order=4,
        )
        db.add(c)
        path = LearningPath(user_id=user_id, title="P")
        db.add_all([c, path])
        await db.flush()
        db.add(LearningUnit(
            path_id=path.id, concept_id=c.id,
            order_index=0, content={},
            status=LearningUnitStatus.COMPLETED.value,
            completed_at=now - timedelta(hours=3),
        ))
        await db.commit()

    async with TestSessionFactory() as db:
        items = await list_recent_activities(db, user_id, limit=10)

    types = [i.type for i in items]
    assert set(types) == {"quiz", "reflection", "unit_completed"}
    # 排序：最近在前 → quiz (hour 1) > reflection (hour 2) > unit_completed (hour 3)
    assert types == ["quiz", "reflection", "unit_completed"]


async def test_timeline_quiz_event_includes_is_correct(client: AsyncClient):
    user_id = await _ensure_user(client)
    async with TestSessionFactory() as db:
        q = Question(
            type="multiple_choice", concept_tags=["t"],
            bloom_level=3, difficulty=2,
            content={"stem": "x", "options": ["a"], "answer_index": 0},
            explanation="", source="generated", validated=True,
        )
        db.add(q)
        await db.flush()
        db.add(StudentAnswer(
            user_id=user_id, question_id=q.id,
            answer={"selected": 0}, is_correct=False,
            time_spent_seconds=5, hint_level_used=2, feedback="",
        ))
        await db.commit()

    async with TestSessionFactory() as db:
        items = await list_recent_activities(db, user_id, limit=10)
    assert len(items) == 1
    assert items[0].type == "quiz"
    assert items[0].is_correct is False
    assert "答錯" in items[0].title
    assert "提示用了 2/5" in items[0].detail


async def test_timeline_reflection_quality_score_in_detail(client: AsyncClient):
    user_id = await _ensure_user(client)
    async with TestSessionFactory() as db:
        db.add(Reflection(
            user_id=user_id, source_type="quiz", source_id=uuid.uuid4(),
            problem_understanding="x", planned_steps=["a"],
            expected_concepts="x", quality_score=0.7,
        ))
        await db.commit()

    async with TestSessionFactory() as db:
        items = await list_recent_activities(db, user_id, limit=10)
    assert items[0].type == "reflection"
    assert "70%" in items[0].detail


async def test_timeline_unit_only_when_completed(client: AsyncClient):
    """status != completed 不出現在 timeline。"""
    user_id = await _ensure_user(client)
    async with TestSessionFactory() as db:
        c = Concept(
            tag="t", name_zh="X", name_en="X",
            description="", difficulty_level=1, category="基礎",
        )
        path = LearningPath(user_id=user_id, title="P")
        db.add_all([c, path])
        await db.flush()
        db.add(LearningUnit(
            path_id=path.id, concept_id=c.id,
            order_index=0, content={},
            status=LearningUnitStatus.IN_PROGRESS.value,
            completed_at=None,
        ))
        await db.commit()

    async with TestSessionFactory() as db:
        items = await list_recent_activities(db, user_id, limit=10)
    assert items == []  # in_progress 不算


# === limit ===


async def test_timeline_respects_limit(client: AsyncClient):
    user_id = await _ensure_user(client)
    async with TestSessionFactory() as db:
        q = Question(
            type="multiple_choice", concept_tags=["t"],
            bloom_level=3, difficulty=2,
            content={"stem": "x", "options": ["a"], "answer_index": 0},
            explanation="", source="generated", validated=True,
        )
        db.add(q)
        await db.flush()
        # 5 個 quiz answer
        for i in range(5):
            db.add(StudentAnswer(
                user_id=user_id, question_id=q.id,
                answer={"selected": 0}, is_correct=True,
                time_spent_seconds=5, hint_level_used=0, feedback="",
                answered_at=datetime.now(timezone.utc) - timedelta(minutes=i),
            ))
        await db.commit()

    async with TestSessionFactory() as db:
        items = await list_recent_activities(db, user_id, limit=3)
    assert len(items) == 3


# === HTTP integration ===


async def test_timeline_http_returns_iso_timestamps(client: AsyncClient):
    user_id = await _ensure_user(client)
    async with TestSessionFactory() as db:
        q = Question(
            type="multiple_choice", concept_tags=["t"],
            bloom_level=3, difficulty=2,
            content={"stem": "x", "options": ["a"], "answer_index": 0},
            explanation="", source="generated", validated=True,
        )
        db.add(q)
        await db.flush()
        db.add(StudentAnswer(
            user_id=user_id, question_id=q.id,
            answer={"selected": 0}, is_correct=True,
            time_spent_seconds=5, hint_level_used=0, feedback="",
        ))
        await db.commit()

    token = encrypt_test_token(USER)
    resp = await client.get(
        "/dashboard/timeline?limit=5",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["type"] == "quiz"
    assert "T" in item["timestamp"]  # ISO format with T separator
    assert item["is_correct"] is True


async def test_timeline_http_invalid_limit(client: AsyncClient):
    """Pydantic Query 範圍 ge=1 le=100。"""
    await _ensure_user(client)
    token = encrypt_test_token(USER)
    for invalid in (0, 101, -1):
        resp = await client.get(
            f"/dashboard/timeline?limit={invalid}",
            cookies={"authjs.session-token": token},
        )
        assert resp.status_code == 422
