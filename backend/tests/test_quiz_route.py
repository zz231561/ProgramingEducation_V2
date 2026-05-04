"""Quiz API route 整合測試（mock LLM + RAG）。

涵蓋：
- POST /quiz/generate：mask 答案、寫入 questions / validated=True
- POST /quiz/submit：MC 答對 → is_correct=True、mastery 更新、回傳完整 content
- POST /quiz/submit：題目不存在 → 404
- POST /quiz/submit：未審查 (validated=False) → 400
- GET /quiz/history：登入後回作答列表
"""

import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from models.concept import Concept
from models.quiz import Question, StudentAnswer
from tests.helpers import TestSessionFactory, encrypt_test_token

STUDENT_PAYLOAD = {
    "sub": "quiz-user",
    "email": "quiz@test.com",
    "name": "Quiz Tester",
    "googleId": "g-quiz-user",
}


def _mock_completion(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@contextmanager
def patched_quiz_llms(generate_json: str, validator_pass: bool = True):
    """同時 mock generate / validate 兩個 LLM 客戶端與 retrieve_chunks。"""
    gen_client = AsyncMock()
    gen_client.chat.completions.create = AsyncMock(
        return_value=_mock_completion(generate_json)
    )
    validator_response = json.dumps({
        "answer_correct": validator_pass,
        "answer_reason": "ok",
        "concept_fits": validator_pass,
        "concept_reason": "ok",
        "bloom_appropriate": validator_pass,
        "bloom_reason": "ok",
    })
    val_client = AsyncMock()
    val_client.chat.completions.create = AsyncMock(
        return_value=_mock_completion(validator_response)
    )
    with (
        patch("services.quiz.generate._get_client", return_value=gen_client),
        patch("services.quiz.generate.retrieve_chunks", AsyncMock(return_value=[])),
        patch("services.quiz.validate._get_client", return_value=val_client),
    ):
        yield


async def _seed_starter_concept() -> Concept:
    async with TestSessionFactory() as db:
        c = Concept(
            tag="syntax-basic",
            name_zh="基礎語法",
            name_en="Basic Syntax",
            description="C++ 變數、型別、運算子。",
            difficulty_level=1,
            category="基礎語法",
        )
        db.add(c)
        await db.commit()
        await db.refresh(c)
        return c


_VALID_MC_JSON = json.dumps({
    "stem": "下列何者用來宣告整數變數？",
    "options": ["int x;", "var x;", "let x;", "x: int;"],
    "answer_index": 0,
    "explanation": "C++ 用 type-name 順序宣告。",
})


# === generate ===


async def test_generate_requires_auth(client: AsyncClient):
    resp = await client.post("/quiz/generate", json={})
    assert resp.status_code == 401


async def test_generate_returns_masked_question(client: AsyncClient):
    """Cold-start：學生無 mastery → 用 syntax-basic fallback；mask 答案不外洩。"""
    await _seed_starter_concept()
    token = encrypt_test_token(STUDENT_PAYLOAD)

    with patched_quiz_llms(_VALID_MC_JSON):
        resp = await client.post(
            "/quiz/generate",
            json={"type": "multiple_choice", "bloom_level": 3},
            cookies={"authjs.session-token": token},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "multiple_choice"
    assert "options" in body["content"]
    assert "answer_index" not in body["content"]  # 答案被 mask
    assert "id" in body

    # DB 該題已 validated=True
    async with TestSessionFactory() as db:
        q = (await db.execute(select(Question))).scalar_one()
        assert q.validated is True


# === submit ===


async def test_submit_correct_answer_persists_and_grades(client: AsyncClient):
    await _seed_starter_concept()
    token = encrypt_test_token(STUDENT_PAYLOAD)

    with patched_quiz_llms(_VALID_MC_JSON):
        gen_resp = await client.post(
            "/quiz/generate",
            json={"type": "multiple_choice", "bloom_level": 3},
            cookies={"authjs.session-token": token},
        )
    qid = gen_resp.json()["id"]

    sub_resp = await client.post(
        "/quiz/submit",
        json={"question_id": qid, "answer": {"selected_index": 0}},
        cookies={"authjs.session-token": token},
    )
    assert sub_resp.status_code == 200
    body = sub_resp.json()
    assert body["is_correct"] is True
    assert body["correct_content"]["answer_index"] == 0  # 提交後才回完整答案
    assert body["explanation"]

    # student_answers 寫入
    async with TestSessionFactory() as db:
        rows = (await db.execute(select(StudentAnswer))).scalars().all()
        assert len(rows) == 1
        assert rows[0].is_correct is True


async def test_submit_wrong_answer_marks_incorrect(client: AsyncClient):
    await _seed_starter_concept()
    token = encrypt_test_token(STUDENT_PAYLOAD)

    with patched_quiz_llms(_VALID_MC_JSON):
        gen_resp = await client.post(
            "/quiz/generate",
            json={"type": "multiple_choice", "bloom_level": 3},
            cookies={"authjs.session-token": token},
        )
    qid = gen_resp.json()["id"]

    sub_resp = await client.post(
        "/quiz/submit",
        json={"question_id": qid, "answer": {"selected_index": 2}},  # 錯選項
        cookies={"authjs.session-token": token},
    )
    assert sub_resp.status_code == 200
    assert sub_resp.json()["is_correct"] is False


async def test_submit_unknown_question_404(client: AsyncClient):
    token = encrypt_test_token(STUDENT_PAYLOAD)
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.post(
        "/quiz/submit",
        json={"question_id": fake_id, "answer": {"selected_index": 0}},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "QUESTION_NOT_FOUND"


async def test_submit_unvalidated_question_400(client: AsyncClient):
    """直接塞入 validated=False 的題目嘗試作答 → 400。"""
    await _seed_starter_concept()
    token = encrypt_test_token(STUDENT_PAYLOAD)

    async with TestSessionFactory() as db:
        q = Question(
            type="multiple_choice",
            concept_tags=["syntax-basic"],
            bloom_level=3,
            difficulty=1,
            content={"stem": "...", "options": ["a"], "answer_index": 0},
            explanation="",
            source="generated",
            validated=False,
        )
        db.add(q)
        await db.commit()
        await db.refresh(q)
        qid = str(q.id)

    resp = await client.post(
        "/quiz/submit",
        json={"question_id": qid, "answer": {"selected_index": 0}},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "QUESTION_NOT_VALIDATED"


# === history ===


async def test_history_returns_user_answers(client: AsyncClient):
    await _seed_starter_concept()
    token = encrypt_test_token(STUDENT_PAYLOAD)

    with patched_quiz_llms(_VALID_MC_JSON):
        gen_resp = await client.post(
            "/quiz/generate",
            json={"type": "multiple_choice", "bloom_level": 3},
            cookies={"authjs.session-token": token},
        )
    qid = gen_resp.json()["id"]

    await client.post(
        "/quiz/submit",
        json={"question_id": qid, "answer": {"selected_index": 0}},
        cookies={"authjs.session-token": token},
    )

    hist_resp = await client.get(
        "/quiz/history",
        cookies={"authjs.session-token": token},
    )
    assert hist_resp.status_code == 200
    body = hist_resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["is_correct"] is True
