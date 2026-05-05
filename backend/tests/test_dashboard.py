"""Dashboard service + HTTP 整合測試（roadmap 3-3a）。

涵蓋：
- 401 未登入
- 空狀態（無 path / 無 quiz / 無 mastery / 無 reflection）
- path_progress 計算（completed/total/percent）
- week_quiz 限近 7 天 + 8 天前資料不算
- mastery_overview 三欄計數
- reflection_count
- today_suggestion 4 種規則：in_progress / available / 全完成 / 無 path
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from models.concept import Concept
from models.learning import LearningPath, LearningUnit, LearningUnitStatus
from models.mastery import StudentMastery
from models.quiz import Question, StudentAnswer
from models.reflection import Reflection
from models.user import User
from services.dashboard import get_dashboard_stats
from tests.helpers import TestSessionFactory, encrypt_test_token

USER = {
    "sub": "dash-user",
    "email": "dash@test.com",
    "name": "Dash",
    "googleId": "g-dash-user",
}


async def _ensure_user(client: AsyncClient) -> uuid.UUID:
    token = encrypt_test_token(USER)
    await client.get("/auth/me", cookies={"authjs.session-token": token})
    async with TestSessionFactory() as db:
        return (
            await db.execute(select(User).where(User.google_id == USER["googleId"]))
        ).scalar_one().id


async def _seed_concepts(tags: list[str]) -> list[uuid.UUID]:
    async with TestSessionFactory() as db:
        ids: list[uuid.UUID] = []
        for tag in tags:
            c = Concept(
                tag=tag, name_zh=f"概念 {tag}", name_en=tag,
                description="", difficulty_level=1, category="基礎",
            )
            db.add(c)
            await db.flush()
            ids.append(c.id)
        await db.commit()
        return ids


async def _seed_path_with_units(
    user_id: uuid.UUID, statuses: list[str], concept_ids: list[uuid.UUID]
) -> uuid.UUID:
    async with TestSessionFactory() as db:
        path = LearningPath(user_id=user_id, title="P")
        db.add(path)
        await db.flush()
        for i, st in enumerate(statuses):
            db.add(LearningUnit(
                path_id=path.id, concept_id=concept_ids[i],
                order_index=i, content={}, status=st,
            ))
        await db.commit()
        await db.refresh(path)
        return path.id


# === HTTP auth ===


async def test_dashboard_requires_auth(client: AsyncClient):
    resp = await client.get("/dashboard/stats")
    assert resp.status_code == 401


# === 空狀態 ===


async def test_dashboard_empty_state(client: AsyncClient):
    user_id = await _ensure_user(client)

    async with TestSessionFactory() as db:
        s = await get_dashboard_stats(db, user_id)
    assert s.path_progress is None
    assert s.week_quiz.total_attempts == 0
    assert s.week_quiz.accuracy_percent == 0
    assert s.mastery.total_concepts == 0
    assert s.mastery.started_count == 0
    assert s.mastery.mastered_count == 0
    assert s.reflection_count == 0
    assert s.today_suggestion.link == "/learn"
    assert "進入 Learn" in s.today_suggestion.title


# === path_progress ===


async def test_dashboard_path_progress_computes_percent(client: AsyncClient):
    user_id = await _ensure_user(client)
    cids = await _seed_concepts(["a", "b", "c", "d"])
    # 4 unit：1 completed, 1 in_progress, 2 locked → 25%
    await _seed_path_with_units(
        user_id,
        [
            LearningUnitStatus.COMPLETED.value,
            LearningUnitStatus.IN_PROGRESS.value,
            LearningUnitStatus.LOCKED.value,
            LearningUnitStatus.LOCKED.value,
        ],
        cids,
    )

    async with TestSessionFactory() as db:
        s = await get_dashboard_stats(db, user_id)
    assert s.path_progress is not None
    assert s.path_progress.total_units == 4
    assert s.path_progress.completed_units == 1
    assert s.path_progress.percent == 25


# === week_quiz ===


async def test_dashboard_week_quiz_excludes_old_attempts(client: AsyncClient):
    user_id = await _ensure_user(client)
    cids = await _seed_concepts(["a"])
    async with TestSessionFactory() as db:
        q = Question(
            type="multiple_choice", concept_tags=["a"],
            bloom_level=3, difficulty=1,
            content={"stem": "x", "options": ["1"], "answer_index": 0},
            explanation="", source="generated", validated=True,
        )
        db.add(q)
        await db.flush()
        # 2 個近期（近 7 天內）：1 對 1 錯
        now = datetime.now(timezone.utc)
        for is_correct, days_ago in [(True, 0), (False, 3), (True, 8), (False, 30)]:
            db.add(StudentAnswer(
                user_id=user_id, question_id=q.id,
                answer={"selected": 0}, is_correct=is_correct,
                time_spent_seconds=5, hint_level_used=0, feedback="",
                answered_at=now - timedelta(days=days_ago),
            ))
        await db.commit()

    async with TestSessionFactory() as db:
        s = await get_dashboard_stats(db, user_id)
    # 只有 days_ago=0,3 算近 7 天 → 2 attempt, 1 correct → 50%
    assert s.week_quiz.total_attempts == 2
    assert s.week_quiz.correct_count == 1
    assert s.week_quiz.accuracy_percent == 50

    # 概念被當題目用過 → mastery 不會自動更新（測試簡化）；reflection 也 0
    _ = cids  # satisfy linter


# === mastery_overview ===


async def test_dashboard_mastery_counts(client: AsyncClient):
    user_id = await _ensure_user(client)
    cids = await _seed_concepts(["a", "b", "c", "d"])  # 4 concepts total

    async with TestSessionFactory() as db:
        # 3 started: 1 mastered (>=0.8), 1 mid, 1 weak
        for concept_id, conf in [(cids[0], 0.9), (cids[1], 0.5), (cids[2], 0.1)]:
            db.add(StudentMastery(
                user_id=user_id, concept_id=concept_id,
                confidence=conf, exposure_count=1,
                success_count=1, error_count=0,
            ))
        await db.commit()

    async with TestSessionFactory() as db:
        s = await get_dashboard_stats(db, user_id)
    assert s.mastery.total_concepts == 4
    assert s.mastery.started_count == 3
    assert s.mastery.mastered_count == 1


# === reflection_count ===


async def test_dashboard_reflection_count(client: AsyncClient):
    user_id = await _ensure_user(client)
    async with TestSessionFactory() as db:
        for _ in range(3):
            db.add(Reflection(
                user_id=user_id, source_type="quiz", source_id=uuid.uuid4(),
                problem_understanding="x", planned_steps=["s"], expected_concepts="x",
            ))
        await db.commit()

    async with TestSessionFactory() as db:
        s = await get_dashboard_stats(db, user_id)
    assert s.reflection_count == 3


# === today_suggestion 規則 ===


async def test_today_suggestion_in_progress_priority(client: AsyncClient):
    """有 in_progress unit 優先於 available。"""
    user_id = await _ensure_user(client)
    cids = await _seed_concepts(["learn-a", "learn-b"])
    await _seed_path_with_units(
        user_id,
        [LearningUnitStatus.AVAILABLE.value, LearningUnitStatus.IN_PROGRESS.value],
        cids,
    )

    async with TestSessionFactory() as db:
        s = await get_dashboard_stats(db, user_id)
    assert "繼續學習" in s.today_suggestion.title
    assert "概念 learn-b" in s.today_suggestion.title  # in_progress 是 b
    assert s.today_suggestion.link == "/learn"


async def test_today_suggestion_only_available(client: AsyncClient):
    user_id = await _ensure_user(client)
    cids = await _seed_concepts(["next-a"])
    await _seed_path_with_units(
        user_id, [LearningUnitStatus.AVAILABLE.value], cids
    )

    async with TestSessionFactory() as db:
        s = await get_dashboard_stats(db, user_id)
    assert "開始下一單元" in s.today_suggestion.title
    assert "概念 next-a" in s.today_suggestion.title


async def test_today_suggestion_all_completed(client: AsyncClient):
    user_id = await _ensure_user(client)
    cids = await _seed_concepts(["done-a", "done-b"])
    await _seed_path_with_units(
        user_id,
        [LearningUnitStatus.COMPLETED.value, LearningUnitStatus.COMPLETED.value],
        cids,
    )

    async with TestSessionFactory() as db:
        s = await get_dashboard_stats(db, user_id)
    assert "課程完成" in s.today_suggestion.title
    assert s.today_suggestion.link == "/quiz"


# === HTTP 整合 ===


async def test_dashboard_http_returns_complete_payload(client: AsyncClient):
    await _ensure_user(client)
    await _seed_concepts(["x"])
    token = encrypt_test_token(USER)
    resp = await client.get(
        "/dashboard/stats",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    # 結構檢查
    assert "path_progress" in body
    assert "week_quiz" in body
    assert "mastery" in body
    assert "reflection_count" in body
    assert "today_suggestion" in body
    # 細欄位檢查
    assert body["mastery"]["total_concepts"] == 1
    assert body["today_suggestion"]["link"] == "/learn"
    assert body["reflection_count"] == 0
