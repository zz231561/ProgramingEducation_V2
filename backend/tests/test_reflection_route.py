"""Reflection API route 整合測試（roadmap 2-5a + 2-5b）。

涵蓋：
- 401 未登入
- POST 建立成功 + 422 source_type 非法
- POST 重複建立 → 409
- GET 自己的反思 / 他人反思 → 404
- PATCH 更新與權限隔離
- 2-5b：HTTP 層 quality_score / followup_question 回傳
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from models.quiz import Question
from services.reflection.evaluate import ReflectionEvaluation
from tests.helpers import TestSessionFactory, encrypt_test_token


def _eval(quality: float | None = None, followup: str | None = None) -> ReflectionEvaluation:
    return ReflectionEvaluation(
        quality_score=quality,
        understanding_score=quality,
        plan_quality_score=quality,
        concept_recall_score=quality,
        followup_question=followup,
    )


@pytest.fixture(autouse=True)
def _mock_evaluate():
    """預設 fallback 評估，避免 HTTP 整合測試打 OpenAI。"""
    with patch(
        "services.reflection.crud.evaluate_reflection",
        new=AsyncMock(return_value=_eval()),
    ) as m:
        yield m

STUDENT_PAYLOAD = {
    "sub": "reflection-user",
    "email": "reflection@test.com",
    "name": "Reflection Tester",
    "googleId": "g-reflection-user",
}

OTHER_PAYLOAD = {
    "sub": "reflection-other",
    "email": "other@test.com",
    "name": "Other",
    "googleId": "g-other-user",
}


async def _seed_question() -> uuid.UUID:
    async with TestSessionFactory() as db:
        q = Question(
            type="multiple_choice",
            concept_tags=["syntax-basic"],
            bloom_level=3,
            difficulty=1,
            content={"stem": "...", "options": ["a", "b"], "answer_index": 0},
            explanation="",
            source="generated",
            validated=True,
        )
        db.add(q)
        await db.commit()
        await db.refresh(q)
        return q.id


# === auth ===


async def test_create_requires_auth(client: AsyncClient):
    resp = await client.post("/reflection", json={
        "source_type": "quiz",
        "source_id": str(uuid.uuid4()),
    })
    assert resp.status_code == 401


# === create ===


async def test_create_reflection_persists(client: AsyncClient):
    qid = await _seed_question()
    token = encrypt_test_token(STUDENT_PAYLOAD)

    resp = await client.post(
        "/reflection",
        json={
            "source_type": "quiz",
            "source_id": str(qid),
            "problem_understanding": "判斷 C++ 整數宣告語法",
            "planned_steps": ["看選項", "比對語法"],
            "expected_concepts": "syntax-basic",
        },
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["source_type"] == "quiz"
    assert body["planned_steps"] == ["看選項", "比對語法"]
    assert body["is_modified"] is False
    assert body["quality_score"] is None


async def test_create_reflection_invalid_source_type_422(client: AsyncClient):
    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.post(
        "/reflection",
        json={
            "source_type": "homework",  # 非 quiz / learning_unit
            "source_id": str(uuid.uuid4()),
        },
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "INVALID_SOURCE_TYPE"


async def test_create_reflection_unknown_quiz_source_404(client: AsyncClient):
    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.post(
        "/reflection",
        json={
            "source_type": "quiz",
            "source_id": str(uuid.uuid4()),
        },
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "REFLECTION_SOURCE_NOT_FOUND"


async def test_create_reflection_duplicate_409(client: AsyncClient):
    qid = await _seed_question()
    token = encrypt_test_token(STUDENT_PAYLOAD)

    first = await client.post(
        "/reflection",
        json={
            "source_type": "quiz",
            "source_id": str(qid),
            "planned_steps": ["a"],
        },
        cookies={"authjs.session-token": token},
    )
    assert first.status_code == 201

    dup = await client.post(
        "/reflection",
        json={
            "source_type": "quiz",
            "source_id": str(qid),
            "planned_steps": ["b"],
        },
        cookies={"authjs.session-token": token},
    )
    assert dup.status_code == 409
    assert dup.json()["error"] == "REFLECTION_ALREADY_EXISTS"


# === get ===


async def test_get_reflection_by_owner(client: AsyncClient):
    qid = await _seed_question()
    token = encrypt_test_token(STUDENT_PAYLOAD)

    created = await client.post(
        "/reflection",
        json={
            "source_type": "quiz",
            "source_id": str(qid),
            "planned_steps": ["a"],
        },
        cookies={"authjs.session-token": token},
    )
    rid = created.json()["id"]

    fetched = await client.get(
        f"/reflection/{rid}",
        cookies={"authjs.session-token": token},
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == rid


async def test_get_reflection_other_user_404(client: AsyncClient):
    qid = await _seed_question()
    owner_token = encrypt_test_token(STUDENT_PAYLOAD)
    other_token = encrypt_test_token(OTHER_PAYLOAD)

    created = await client.post(
        "/reflection",
        json={
            "source_type": "quiz",
            "source_id": str(qid),
            "planned_steps": ["a"],
        },
        cookies={"authjs.session-token": owner_token},
    )
    rid = created.json()["id"]

    resp = await client.get(
        f"/reflection/{rid}",
        cookies={"authjs.session-token": other_token},
    )
    assert resp.status_code == 404


# === patch ===


async def test_patch_reflection_marks_modified(client: AsyncClient):
    qid = await _seed_question()
    token = encrypt_test_token(STUDENT_PAYLOAD)

    created = await client.post(
        "/reflection",
        json={
            "source_type": "quiz",
            "source_id": str(qid),
            "planned_steps": ["a"],
        },
        cookies={"authjs.session-token": token},
    )
    rid = created.json()["id"]

    patched = await client.patch(
        f"/reflection/{rid}",
        json={
            "planned_steps": ["a", "b"],
            "followup_answer": "想再多列一步",
        },
        cookies={"authjs.session-token": token},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["planned_steps"] == ["a", "b"]
    assert body["followup_answer"] == "想再多列一步"
    assert body["is_modified"] is True


async def test_patch_reflection_other_user_404(client: AsyncClient):
    qid = await _seed_question()
    owner_token = encrypt_test_token(STUDENT_PAYLOAD)
    other_token = encrypt_test_token(OTHER_PAYLOAD)

    created = await client.post(
        "/reflection",
        json={
            "source_type": "quiz",
            "source_id": str(qid),
            "planned_steps": ["a"],
        },
        cookies={"authjs.session-token": owner_token},
    )
    rid = created.json()["id"]

    resp = await client.patch(
        f"/reflection/{rid}",
        json={"planned_steps": ["x"]},
        cookies={"authjs.session-token": other_token},
    )
    assert resp.status_code == 404


# === 2-5b LLM evaluation 整合（HTTP 層） ===


async def test_post_returns_quality_score_and_followup(client: AsyncClient):
    """POST /reflection 應回傳 LLM 評分結果（低分時帶追問）。"""
    qid = await _seed_question()
    token = encrypt_test_token(STUDENT_PAYLOAD)

    with patch(
        "services.reflection.crud.evaluate_reflection",
        new=AsyncMock(return_value=_eval(quality=0.4, followup="可否說明你的步驟？")),
    ):
        resp = await client.post(
            "/reflection",
            json={
                "source_type": "quiz",
                "source_id": str(qid),
                "problem_understanding": "短答",
                "planned_steps": ["先想"],
                "expected_concepts": "",
            },
            cookies={"authjs.session-token": token},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["quality_score"] == 0.4
    assert body["followup_question"] == "可否說明你的步驟？"


async def test_patch_re_evaluates_and_clears_followup(client: AsyncClient):
    """PATCH 補充 followup_answer 後 LLM 重新評分；高分清空追問。"""
    qid = await _seed_question()
    token = encrypt_test_token(STUDENT_PAYLOAD)

    with patch(
        "services.reflection.crud.evaluate_reflection",
        new=AsyncMock(return_value=_eval(quality=0.3, followup="再具體點")),
    ):
        created = await client.post(
            "/reflection",
            json={
                "source_type": "quiz",
                "source_id": str(qid),
                "planned_steps": ["想"],
            },
            cookies={"authjs.session-token": token},
        )
    rid = created.json()["id"]
    assert created.json()["followup_question"] == "再具體點"

    with patch(
        "services.reflection.crud.evaluate_reflection",
        new=AsyncMock(return_value=_eval(quality=0.9, followup=None)),
    ):
        patched = await client.patch(
            f"/reflection/{rid}",
            json={"followup_answer": "1.讀輸入 2.排序 3.輸出"},
            cookies={"authjs.session-token": token},
        )
    body = patched.json()
    assert body["quality_score"] == 0.9
    assert body["followup_question"] is None
