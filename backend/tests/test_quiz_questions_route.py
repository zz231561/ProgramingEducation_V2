"""GET /quiz/questions/{id} route 測試（roadmap K3e 微測驗取題）。

涵蓋：
- 未登入 → 401
- validated 題 → 200 + 答案已 mask
- 未審查題 → 404 QUESTION_NOT_FOUND
- 不存在 id → 404 QUESTION_NOT_FOUND
"""

import uuid

import pytest
from httpx import AsyncClient

from models.quiz import Question, QuestionSource
from tests.helpers import TestSessionFactory, encrypt_test_token

pytestmark = pytest.mark.asyncio

STUDENT_PAYLOAD = {
    "sub": "qq-user",
    "email": "qq@test.com",
    "name": "QQ Tester",
    "googleId": "g-qq-user",
}


async def _seed_question(validated: bool) -> Question:
    async with TestSessionFactory() as db:
        q = Question(
            type="multiple_choice",
            concept_tags=["syntax-basic"],
            bloom_level=3,
            difficulty=2,
            content={
                "stem": "診斷題：下列何者正確？",
                "options": ["A", "B", "C", "D"],
                "answer_index": 2,
            },
            explanation="C is correct.",
            source=QuestionSource.GENERATED.value,
            validated=validated,
        )
        db.add(q)
        await db.commit()
        await db.refresh(q)
        return q


async def test_get_question_requires_auth(client: AsyncClient):
    resp = await client.get(f"/quiz/questions/{uuid.uuid4()}")
    assert resp.status_code == 401


async def test_get_question_returns_masked_content(client: AsyncClient):
    q = await _seed_question(validated=True)
    token = encrypt_test_token(STUDENT_PAYLOAD)

    resp = await client.get(
        f"/quiz/questions/{q.id}",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(q.id)
    assert body["type"] == "multiple_choice"
    assert "options" in body["content"]
    assert "answer_index" not in body["content"]  # 答案 mask


async def test_get_question_unvalidated_returns_404(client: AsyncClient):
    q = await _seed_question(validated=False)
    token = encrypt_test_token(STUDENT_PAYLOAD)

    resp = await client.get(
        f"/quiz/questions/{q.id}",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "QUESTION_NOT_FOUND"


async def test_get_question_missing_returns_404(client: AsyncClient):
    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.get(
        f"/quiz/questions/{uuid.uuid4()}",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "QUESTION_NOT_FOUND"
