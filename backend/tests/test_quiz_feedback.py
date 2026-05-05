"""Quiz Feedback service + HTTP 整合測試（roadmap 3-2c）。

涵蓋：
- _llm_suggestion fallback 五種路徑（no client / exception / invalid JSON / empty / success）
- generate_quiz_feedback：擁有權檢查 / mastery 含未練 (0) / 推薦 unit 限同 user 路徑且未完成
- HTTP 401 / 404 (cross-user) / 200 success
- submit response 含 answer_id（3-2c 新增）
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.errors import AppError
from models.concept import Concept
from models.learning import LearningPath, LearningUnit, LearningUnitStatus
from models.mastery import StudentMastery
from models.quiz import Question, StudentAnswer
from models.user import User
from services.quiz.feedback import (
    _llm_suggestion,
    generate_quiz_feedback,
)
from tests.helpers import TestSessionFactory, encrypt_test_token

USER = {
    "sub": "fb-user",
    "email": "fb@test.com",
    "name": "FB",
    "googleId": "g-fb-user",
}
OTHER = {
    "sub": "fb-other",
    "email": "fb-other@test.com",
    "name": "FB Other",
    "googleId": "g-fb-other",
}


def _llm_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


async def _ensure_user(payload: dict, client: AsyncClient) -> uuid.UUID:
    token = encrypt_test_token(payload)
    await client.get("/auth/me", cookies={"authjs.session-token": token})
    async with TestSessionFactory() as db:
        return (
            await db.execute(select(User).where(User.google_id == payload["googleId"]))
        ).scalar_one().id


async def _seed_answer_with_concepts(
    user_id: uuid.UUID, concept_tags: list[str], is_correct: bool = True
) -> tuple[uuid.UUID, list[uuid.UUID]]:
    """seed concepts + question + student_answer。回 (answer_id, [concept_ids])。"""
    async with TestSessionFactory() as db:
        concept_ids: list[uuid.UUID] = []
        for tag in concept_tags:
            c = Concept(
                tag=tag, name_zh=f"概念 {tag}", name_en=tag,
                description="", difficulty_level=2, category="基礎",
                video_order=4,
            )
            db.add(c)
            await db.flush()
            concept_ids.append(c.id)
        q = Question(
            type="multiple_choice",
            concept_tags=concept_tags,
            bloom_level=3,
            difficulty=2,
            content={"stem": "x", "options": ["a", "b"], "answer_index": 0},
            explanation="",
            source="generated",
            validated=True,
        )
        db.add(q)
        await db.flush()
        ans = StudentAnswer(
            user_id=user_id,
            question_id=q.id,
            answer={"selected": 0},
            is_correct=is_correct,
            time_spent_seconds=10,
            hint_level_used=0,
            feedback="",
        )
        db.add(ans)
        await db.commit()
        await db.refresh(ans)
        return ans.id, concept_ids


# === Service _llm_suggestion fallback paths ===


@pytest.mark.asyncio
async def test_llm_suggestion_no_client_uses_fallback_correct():
    with patch("services.quiz.feedback._get_client", return_value=None):
        s, fb = await _llm_suggestion(True, "x", [])
    assert fb is True
    assert "繼續挑戰" in s or "好" in s  # 含正向句意


@pytest.mark.asyncio
async def test_llm_suggestion_no_client_uses_fallback_wrong():
    with patch("services.quiz.feedback._get_client", return_value=None):
        s, fb = await _llm_suggestion(False, "x", [])
    assert fb is True
    assert "別氣餒" in s or "複習" in s


@pytest.mark.asyncio
async def test_llm_suggestion_exception_uses_fallback():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(side_effect=RuntimeError("down"))
    with patch("services.quiz.feedback._get_client", return_value=client):
        _, fb = await _llm_suggestion(True, "x", [])
    assert fb is True


@pytest.mark.asyncio
async def test_llm_suggestion_invalid_json_uses_fallback():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value=_llm_response("not json"))
    with patch("services.quiz.feedback._get_client", return_value=client):
        _, fb = await _llm_suggestion(True, "x", [])
    assert fb is True


@pytest.mark.asyncio
async def test_llm_suggestion_empty_uses_fallback():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"suggestion": "  "}))
    )
    with patch("services.quiz.feedback._get_client", return_value=client):
        _, fb = await _llm_suggestion(True, "x", [])
    assert fb is True


@pytest.mark.asyncio
async def test_llm_suggestion_success_returns_llm_text():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"suggestion": "繼續加油"}))
    )
    with patch("services.quiz.feedback._get_client", return_value=client):
        s, fb = await _llm_suggestion(True, "x", [])
    assert s == "繼續加油"
    assert fb is False


# === generate_quiz_feedback service ===


@pytest.mark.asyncio
async def test_generate_feedback_unowned_answer_raises_404(client: AsyncClient):
    owner_id = await _ensure_user(USER, client)
    other_id = await _ensure_user(OTHER, client)
    answer_id, _ = await _seed_answer_with_concepts(owner_id, ["t1"])

    async with TestSessionFactory() as db:
        with patch("services.quiz.feedback._get_client", return_value=None):
            with pytest.raises(AppError) as exc:
                await generate_quiz_feedback(db, other_id, answer_id)
    assert exc.value.status_code == 404
    assert exc.value.error == "STUDENT_ANSWER_NOT_FOUND"


@pytest.mark.asyncio
async def test_generate_feedback_includes_mastery_with_zero_for_unpracticed(
    client: AsyncClient,
):
    user_id = await _ensure_user(USER, client)
    answer_id, concept_ids = await _seed_answer_with_concepts(user_id, ["t1", "t2"])
    # t1 有 mastery 0.7；t2 無紀錄 → 回 0
    async with TestSessionFactory() as db:
        db.add(StudentMastery(
            user_id=user_id, concept_id=concept_ids[0], confidence=0.7,
            exposure_count=1, success_count=1, error_count=0,
        ))
        await db.commit()

    async with TestSessionFactory() as db:
        with patch("services.quiz.feedback._get_client", return_value=None):
            result = await generate_quiz_feedback(db, user_id, answer_id)

    by_tag = {m.concept_tag: m.confidence for m in result.concept_mastery}
    assert by_tag == {"t1": 0.7, "t2": 0.0}
    assert result.suggestion_fallback is True  # 因 _get_client 為 None


@pytest.mark.asyncio
async def test_generate_feedback_recommends_units_in_user_path(client: AsyncClient):
    """推薦 units 限同 user 路徑 + 未完成 + 概念匹配。"""
    user_id = await _ensure_user(USER, client)
    answer_id, concept_ids = await _seed_answer_with_concepts(user_id, ["t1"])

    async with TestSessionFactory() as db:
        path = LearningPath(user_id=user_id, title="P")
        db.add(path)
        await db.flush()
        # 與 t1 相關但已完成 → 不該被推薦
        db.add(LearningUnit(
            path_id=path.id, concept_id=concept_ids[0],
            order_index=0, content={},
            status=LearningUnitStatus.COMPLETED.value,
        ))
        # 另一個 t1 unit 但未完成 → 應推薦（測試會有兩個 unit 同 concept；不太實際但驗 query 邏輯）
        # 改：用另一個概念
        c2 = Concept(
            tag="t1-extra", name_zh="X", name_en="X",
            description="", difficulty_level=1, category="基礎",
        )
        db.add(c2)
        await db.flush()
        # 但 t1-extra 不在 question.concept_tags → 不該被推薦
        db.add(LearningUnit(
            path_id=path.id, concept_id=c2.id,
            order_index=1, content={},
            status=LearningUnitStatus.AVAILABLE.value,
        ))
        await db.commit()

    async with TestSessionFactory() as db:
        with patch("services.quiz.feedback._get_client", return_value=None):
            result = await generate_quiz_feedback(db, user_id, answer_id)

    # t1 unit 已完成 → 不推薦；t1-extra 不在 concept_tags → 不推薦
    assert result.recommended_units == []


@pytest.mark.asyncio
async def test_generate_feedback_recommends_unfinished_matching_unit(client: AsyncClient):
    user_id = await _ensure_user(USER, client)
    answer_id, concept_ids = await _seed_answer_with_concepts(user_id, ["t1"])

    async with TestSessionFactory() as db:
        path = LearningPath(user_id=user_id, title="P")
        db.add(path)
        await db.flush()
        db.add(LearningUnit(
            path_id=path.id, concept_id=concept_ids[0],
            order_index=0, content={},
            status=LearningUnitStatus.AVAILABLE.value,
        ))
        await db.commit()

    async with TestSessionFactory() as db:
        with patch("services.quiz.feedback._get_client", return_value=None):
            result = await generate_quiz_feedback(db, user_id, answer_id)

    assert len(result.recommended_units) == 1
    rec = result.recommended_units[0]
    assert rec.concept_tag == "t1"
    assert rec.status == "available"


# === HTTP integration ===


async def test_feedback_requires_auth(client: AsyncClient):
    resp = await client.get(f"/quiz/answers/{uuid.uuid4()}/feedback")
    assert resp.status_code == 401


async def test_feedback_cross_user_returns_404(client: AsyncClient):
    owner_id = await _ensure_user(USER, client)
    await _ensure_user(OTHER, client)
    answer_id, _ = await _seed_answer_with_concepts(owner_id, ["t1"])

    other_token = encrypt_test_token(OTHER)
    resp = await client.get(
        f"/quiz/answers/{answer_id}/feedback",
        cookies={"authjs.session-token": other_token},
    )
    assert resp.status_code == 404


async def test_feedback_success_returns_full_payload(client: AsyncClient):
    user_id = await _ensure_user(USER, client)
    answer_id, _ = await _seed_answer_with_concepts(user_id, ["t1"])
    token = encrypt_test_token(USER)

    llm = AsyncMock()
    llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"suggestion": "做得好"}))
    )
    with patch("services.quiz.feedback._get_client", return_value=llm):
        resp = await client.get(
            f"/quiz/answers/{answer_id}/feedback",
            cookies={"authjs.session-token": token},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["suggestion"] == "做得好"
    assert body["suggestion_fallback"] is False
    assert len(body["concept_mastery"]) == 1
    assert body["concept_mastery"][0]["concept_tag"] == "t1"
    assert body["recommended_units"] == []  # 無 path / unit


# === submit response answer_id (3-2c 新增) ===


async def test_submit_response_includes_answer_id(client: AsyncClient):
    """3-2c：SubmitResponse 加 answer_id 欄位（前端 fetch feedback 用）。"""
    user_id = await _ensure_user(USER, client)
    # seed concept 給 generate 用
    async with TestSessionFactory() as db:
        db.add(Concept(
            tag="syntax-basic", name_zh="X", name_en="X",
            description="", difficulty_level=1, category="基礎",
        ))
        await db.commit()

    # seed 一個 question 直接 (跳過 generate)
    async with TestSessionFactory() as db:
        q = Question(
            type="multiple_choice",
            concept_tags=["syntax-basic"],
            bloom_level=3,
            difficulty=1,
            content={"stem": "x", "options": ["a", "b"], "answer_index": 0},
            explanation="explanation text",
            source="generated",
            validated=True,
        )
        db.add(q)
        await db.commit()
        await db.refresh(q)
        qid = q.id

    token = encrypt_test_token(USER)
    resp = await client.post(
        "/quiz/submit",
        json={
            "question_id": str(qid),
            "answer": {"selected_index": 0},
            "time_spent_seconds": 5,
            "hint_level_used": 0,
        },
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "answer_id" in body
    assert body["is_correct"] is True

    # 確認 answer_id 在 DB 真實對應
    async with TestSessionFactory() as db:
        ans = (
            await db.execute(
                select(StudentAnswer).where(StudentAnswer.id == uuid.UUID(body["answer_id"]))
            )
        ).scalar_one()
        assert ans.user_id == user_id