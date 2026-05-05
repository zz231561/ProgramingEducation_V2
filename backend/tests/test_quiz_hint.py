"""Quiz Hint service unit + HTTP 整合測試（roadmap 3-2b）。

涵蓋：
- generate_hint：成功 / fallback (no client / exception / invalid JSON / empty hint)
- prompt 含 ladder 描述 + question 內容
- HTTP /quiz/hint：401 / 422 (level 範圍) / 404 (question) / 200 success / 200 fallback
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from models.quiz import Question
from services.quiz.hint import _build_prompt, generate_hint
from tests.helpers import TestSessionFactory, encrypt_test_token

USER = {
    "sub": "hint-user",
    "email": "hint@test.com",
    "name": "Hint Tester",
    "googleId": "g-hint",
}


def _llm_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _make_question(qtype: str = "coding") -> Question:
    content = {
        "coding": {"stem": "找最大值", "starter_code": ""},
        "multiple_choice": {
            "stem": "選 int 大小",
            "options": ["2", "4", "8"],
            "answer_index": 1,
        },
    }[qtype]
    return Question(
        type=qtype,
        concept_tags=["arrays-strings"],
        bloom_level=3,
        difficulty=2,
        content=content,
        explanation="",
        source="generated",
        validated=True,
    )


# === Service unit tests ===


def test_prompt_includes_ladder_description():
    s = _build_prompt(_make_question("coding"), hint_level=2, student_attempt="x")
    assert "Hint Level 2" in s
    assert "具體位置" in s  # ladder L2 描述含「指出具體位置」
    assert "找最大值" in s
    assert "x" in s  # 學生作答含入


def test_prompt_for_mc_includes_options():
    s = _build_prompt(_make_question("multiple_choice"), hint_level=1, student_attempt="")
    assert '"2"' in s
    assert "選擇題" in s


@pytest.mark.asyncio
async def test_generate_hint_returns_llm_content():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"hint": "想想迴圈如何找最大值"}))
    )
    with patch("services.quiz.hint._get_client", return_value=client):
        result = await generate_hint(_make_question(), hint_level=1)
    assert result.hint == "想想迴圈如何找最大值"
    assert result.level == 1
    assert result.fallback is False


@pytest.mark.asyncio
async def test_generate_hint_no_client_uses_fallback():
    with patch("services.quiz.hint._get_client", return_value=None):
        result = await generate_hint(_make_question(), hint_level=3)
    assert result.fallback is True
    assert result.level == 3
    assert result.hint  # 非空 fallback 句


@pytest.mark.asyncio
async def test_generate_hint_llm_exception_uses_fallback():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(side_effect=RuntimeError("openai down"))
    with patch("services.quiz.hint._get_client", return_value=client):
        result = await generate_hint(_make_question(), hint_level=2)
    assert result.fallback is True


@pytest.mark.asyncio
async def test_generate_hint_invalid_json_uses_fallback():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value=_llm_response("not json"))
    with patch("services.quiz.hint._get_client", return_value=client):
        result = await generate_hint(_make_question(), hint_level=4)
    assert result.fallback is True


@pytest.mark.asyncio
async def test_generate_hint_empty_hint_uses_fallback():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"hint": "  "}))
    )
    with patch("services.quiz.hint._get_client", return_value=client):
        result = await generate_hint(_make_question(), hint_level=5)
    assert result.fallback is True


# === HTTP integration ===


async def _seed_question_in_db(validated: bool = True) -> uuid.UUID:
    async with TestSessionFactory() as db:
        q = Question(
            type="coding",
            concept_tags=["control-flow"],
            bloom_level=3,
            difficulty=2,
            content={"stem": "找最大值", "starter_code": ""},
            explanation="",
            source="generated",
            validated=validated,
        )
        db.add(q)
        await db.commit()
        await db.refresh(q)
        return q.id


async def test_hint_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/quiz/hint",
        json={"question_id": str(uuid.uuid4()), "hint_level": 1},
    )
    assert resp.status_code == 401


async def test_hint_level_out_of_range_returns_422(client: AsyncClient):
    qid = await _seed_question_in_db()
    token = encrypt_test_token(USER)
    # 觸發 user upsert
    await client.get("/auth/me", cookies={"authjs.session-token": token})

    for invalid_level in (0, 6, -1, 100):
        resp = await client.post(
            "/quiz/hint",
            json={"question_id": str(qid), "hint_level": invalid_level},
            cookies={"authjs.session-token": token},
        )
        assert resp.status_code == 422


async def test_hint_unknown_question_returns_404(client: AsyncClient):
    token = encrypt_test_token(USER)
    await client.get("/auth/me", cookies={"authjs.session-token": token})
    resp = await client.post(
        "/quiz/hint",
        json={"question_id": str(uuid.uuid4()), "hint_level": 1},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "QUESTION_NOT_FOUND"


async def test_hint_unvalidated_question_returns_400(client: AsyncClient):
    qid = await _seed_question_in_db(validated=False)
    token = encrypt_test_token(USER)
    await client.get("/auth/me", cookies={"authjs.session-token": token})
    resp = await client.post(
        "/quiz/hint",
        json={"question_id": str(qid), "hint_level": 1},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "QUESTION_NOT_VALIDATED"


async def test_hint_success_returns_llm_content(client: AsyncClient):
    qid = await _seed_question_in_db()
    token = encrypt_test_token(USER)
    await client.get("/auth/me", cookies={"authjs.session-token": token})

    llm = AsyncMock()
    llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"hint": "從輸入長度開始想"}))
    )
    with patch("services.quiz.hint._get_client", return_value=llm):
        resp = await client.post(
            "/quiz/hint",
            json={"question_id": str(qid), "hint_level": 2, "student_attempt": "for(...)"},
            cookies={"authjs.session-token": token},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["level"] == 2
    assert body["hint"] == "從輸入長度開始想"
    assert body["fallback"] is False


async def test_hint_llm_failure_returns_fallback(client: AsyncClient):
    """LLM 不可用 → 200 + fallback=True，不擋學生。"""
    qid = await _seed_question_in_db()
    token = encrypt_test_token(USER)
    await client.get("/auth/me", cookies={"authjs.session-token": token})

    with patch("services.quiz.hint._get_client", return_value=None):
        resp = await client.post(
            "/quiz/hint",
            json={"question_id": str(qid), "hint_level": 3},
            cookies={"authjs.session-token": token},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["fallback"] is True
    assert body["level"] == 3
    assert body["hint"]
