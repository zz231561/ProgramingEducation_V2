"""Variation Challenge HTTP 整合測試（roadmap 2-6d）。

涵蓋：
- 401 未登入
- generate 成功 → 持久化（露 stem/starter/test_cases）+ 清空舊 answer/passed
- generate 非 coding → 422 VARIATION_NOT_APPLICABLE
- generate LLM 失敗 → 503 VARIATION_GENERATION_FAILED
- generate 跨使用者 → 404
- grade 未先 generate → 400 VARIATION_NOT_STARTED
- grade 通過 → passed=True + feedback 持久化
- grade LLM 失敗 → passed=False fallback（不擋學生）
- grade 跨使用者 → 404
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from models.quiz import Question, StudentAnswer
from tests.helpers import TestSessionFactory, encrypt_test_token

OWNER_PAYLOAD = {
    "sub": "var-owner",
    "email": "var-owner@test.com",
    "name": "Var Owner",
    "googleId": "g-var-owner",
}

OTHER_PAYLOAD = {
    "sub": "var-other",
    "email": "var-other@test.com",
    "name": "Var Other",
    "googleId": "g-var-other",
}


def _llm_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


async def _seed_coding_answer(user_payload: dict, client: AsyncClient) -> uuid.UUID:
    token = encrypt_test_token(user_payload)
    await client.get("/auth/me", cookies={"authjs.session-token": token})

    from sqlalchemy import select

    from models.user import User

    async with TestSessionFactory() as db:
        user = (
            await db.execute(select(User).where(User.google_id == user_payload["googleId"]))
        ).scalar_one()
        q = Question(
            type="coding",
            concept_tags=["arrays-strings"],
            bloom_level=3,
            difficulty=2,
            content={"stem": "找最大值", "starter_code": "", "test_cases": []},
            explanation="",
            source="generated",
            validated=True,
        )
        db.add(q)
        await db.flush()
        ans = StudentAnswer(
            user_id=user.id,
            question_id=q.id,
            answer={"code": "for(...)cout<<max;"},
            is_correct=True,
            time_spent_seconds=30,
            hint_level_used=0,
            feedback="",
        )
        db.add(ans)
        await db.commit()
        await db.refresh(ans)
        return ans.id


async def _seed_mc_answer(user_payload: dict, client: AsyncClient) -> uuid.UUID:
    token = encrypt_test_token(user_payload)
    await client.get("/auth/me", cookies={"authjs.session-token": token})

    from sqlalchemy import select

    from models.user import User

    async with TestSessionFactory() as db:
        user = (
            await db.execute(select(User).where(User.google_id == user_payload["googleId"]))
        ).scalar_one()
        q = Question(
            type="multiple_choice",
            concept_tags=["syntax-basic"],
            bloom_level=2,
            difficulty=1,
            content={"stem": "x", "options": ["a", "b"], "answer_index": 0},
            explanation="",
            source="generated",
            validated=True,
        )
        db.add(q)
        await db.flush()
        ans = StudentAnswer(
            user_id=user.id,
            question_id=q.id,
            answer={"selected": 0},
            is_correct=True,
            time_spent_seconds=5,
            hint_level_used=0,
            feedback="",
        )
        db.add(ans)
        await db.commit()
        await db.refresh(ans)
        return ans.id


async def _read_answer_state(answer_id: uuid.UUID) -> StudentAnswer:
    from sqlalchemy import select

    async with TestSessionFactory() as db:
        return (
            await db.execute(select(StudentAnswer).where(StudentAnswer.id == answer_id))
        ).scalar_one()


# === auth ===


async def test_variation_generate_requires_auth(client: AsyncClient):
    resp = await client.post(f"/comprehension/{uuid.uuid4()}/variation/generate")
    assert resp.status_code == 401


async def test_variation_grade_requires_auth(client: AsyncClient):
    resp = await client.post(
        f"/comprehension/{uuid.uuid4()}/variation/grade",
        json={"student_code": "x"},
    )
    assert resp.status_code == 401


# === generate ===


async def test_variation_generate_persists_full_payload(client: AsyncClient):
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    payload = {
        "stem": "找最小值",
        "starter_code": "int main(){}",
        "test_cases": [{"input": "3 1 4", "expected": "1"}],
        "concept_focus": "反向應用",
    }
    llm = AsyncMock()
    llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps(payload))
    )
    with patch("services.comprehension.variation._get_client", return_value=llm):
        resp = await client.post(
            f"/comprehension/{answer_id}/variation/generate",
            cookies={"authjs.session-token": token},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["comprehension_type"] == "variation"
    assert body["stem"] == "找最小值"
    assert body["concept_focus"] == "反向應用"
    assert body["test_cases"] == [{"input": "3 1 4", "expected": "1"}]

    persisted = await _read_answer_state(answer_id)
    stored = json.loads(persisted.comprehension_prompt or "{}")
    assert stored["stem"] == "找最小值"


async def test_variation_generate_clears_old_answer_and_passed(client: AsyncClient):
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    from sqlalchemy import update

    async with TestSessionFactory() as db:
        await db.execute(
            update(StudentAnswer)
            .where(StudentAnswer.id == answer_id)
            .values(
                comprehension_type="variation",
                comprehension_prompt=json.dumps({"stem": "old"}),
                comprehension_answer="舊解",
                comprehension_passed=True,
            )
        )
        await db.commit()

    llm = AsyncMock()
    llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({"stem": "new", "starter_code": "", "test_cases": [], "concept_focus": ""})
        )
    )
    with patch("services.comprehension.variation._get_client", return_value=llm):
        await client.post(
            f"/comprehension/{answer_id}/variation/generate",
            cookies={"authjs.session-token": token},
        )

    persisted = await _read_answer_state(answer_id)
    assert persisted.comprehension_answer is None
    assert persisted.comprehension_passed is None


async def test_variation_generate_non_coding_returns_422(client: AsyncClient):
    answer_id = await _seed_mc_answer(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    resp = await client.post(
        f"/comprehension/{answer_id}/variation/generate",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "VARIATION_NOT_APPLICABLE"


async def test_variation_generate_llm_failure_returns_503(client: AsyncClient):
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    with patch("services.comprehension.variation._get_client", return_value=None):
        resp = await client.post(
            f"/comprehension/{answer_id}/variation/generate",
            cookies={"authjs.session-token": token},
        )
    assert resp.status_code == 503
    assert resp.json()["error"] == "VARIATION_GENERATION_FAILED"


async def test_variation_generate_other_user_returns_404(client: AsyncClient):
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    other_token = encrypt_test_token(OTHER_PAYLOAD)
    await client.get("/auth/me", cookies={"authjs.session-token": other_token})

    llm = AsyncMock()
    llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({"stem": "x", "starter_code": "", "test_cases": [], "concept_focus": ""})
        )
    )
    with patch("services.comprehension.variation._get_client", return_value=llm):
        resp = await client.post(
            f"/comprehension/{answer_id}/variation/generate",
            cookies={"authjs.session-token": other_token},
        )
    assert resp.status_code == 404


# === grade ===


async def test_variation_grade_without_generate_returns_400(client: AsyncClient):
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    resp = await client.post(
        f"/comprehension/{answer_id}/variation/grade",
        json={"student_code": "code"},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "VARIATION_NOT_STARTED"


async def test_variation_grade_passed_persists(client: AsyncClient):
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    gen_llm = AsyncMock()
    gen_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({
                "stem": "找最小",
                "starter_code": "",
                "test_cases": [{"input": "3 1", "expected": "1"}],
                "concept_focus": "反向",
            })
        )
    )
    with patch("services.comprehension.variation._get_client", return_value=gen_llm):
        await client.post(
            f"/comprehension/{answer_id}/variation/generate",
            cookies={"authjs.session-token": token},
        )

    grade_llm = AsyncMock()
    grade_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"passed": True, "feedback": "邏輯對"}))
    )
    with patch("services.comprehension.variation._get_client", return_value=grade_llm):
        resp = await client.post(
            f"/comprehension/{answer_id}/variation/grade",
            json={"student_code": "for(int i...) cout<<min;"},
            cookies={"authjs.session-token": token},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["comprehension_passed"] is True
    assert body["feedback"] == "邏輯對"

    persisted = await _read_answer_state(answer_id)
    assert persisted.comprehension_answer == "for(int i...) cout<<min;"
    assert persisted.comprehension_passed is True


async def test_variation_grade_llm_failure_returns_failed_fallback(client: AsyncClient):
    """LLM 評分失敗 → passed=False 保守 fallback；學生答案仍持久化。"""
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    gen_llm = AsyncMock()
    gen_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({"stem": "x", "starter_code": "", "test_cases": [], "concept_focus": ""})
        )
    )
    with patch("services.comprehension.variation._get_client", return_value=gen_llm):
        await client.post(
            f"/comprehension/{answer_id}/variation/generate",
            cookies={"authjs.session-token": token},
        )

    with patch("services.comprehension.variation._get_client", return_value=None):
        resp = await client.post(
            f"/comprehension/{answer_id}/variation/grade",
            json={"student_code": "(短答)"},
            cookies={"authjs.session-token": token},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["comprehension_passed"] is False
    assert body["feedback"] is None

    persisted = await _read_answer_state(answer_id)
    assert persisted.comprehension_answer == "(短答)"
    assert persisted.comprehension_passed is False


async def test_variation_grade_other_user_returns_404(client: AsyncClient):
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    owner_token = encrypt_test_token(OWNER_PAYLOAD)
    other_token = encrypt_test_token(OTHER_PAYLOAD)
    await client.get("/auth/me", cookies={"authjs.session-token": other_token})

    gen_llm = AsyncMock()
    gen_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({"stem": "x", "starter_code": "", "test_cases": [], "concept_focus": ""})
        )
    )
    with patch("services.comprehension.variation._get_client", return_value=gen_llm):
        await client.post(
            f"/comprehension/{answer_id}/variation/generate",
            cookies={"authjs.session-token": owner_token},
        )

    resp = await client.post(
        f"/comprehension/{answer_id}/variation/grade",
        json={"student_code": "x"},
        cookies={"authjs.session-token": other_token},
    )
    assert resp.status_code == 404
