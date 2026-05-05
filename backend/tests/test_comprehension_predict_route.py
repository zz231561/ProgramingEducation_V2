"""Predict-Output HTTP 整合測試（roadmap 2-6c）。

涵蓋：
- 401 未登入
- generate 成功 → 持久化（不洩漏 expected）+ 清空舊 answer/passed
- generate 非 coding 題型 → 422 PREDICT_OUTPUT_NOT_APPLICABLE
- generate LLM 失敗 → 503
- generate 跨使用者 → 404
- grade 未先 generate → 400 PREDICT_NOT_STARTED
- grade exact 通過 → passed=True + match_method=exact
- grade 不符 + LLM 不可用 → passed=False + match_method=mismatch
- grade 跨使用者 → 404
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from models.quiz import Question, StudentAnswer
from tests.helpers import TestSessionFactory, encrypt_test_token

OWNER_PAYLOAD = {
    "sub": "predict-owner",
    "email": "predict-owner@test.com",
    "name": "Predict Owner",
    "googleId": "g-predict-owner",
}

OTHER_PAYLOAD = {
    "sub": "predict-other",
    "email": "predict-other@test.com",
    "name": "Predict Other",
    "googleId": "g-predict-other",
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
            concept_tags=["control-flow"],
            bloom_level=3,
            difficulty=2,
            content={"stem": "讀 N 輸出 1..N", "starter_code": "", "test_cases": []},
            explanation="",
            source="generated",
            validated=True,
        )
        db.add(q)
        await db.flush()
        ans = StudentAnswer(
            user_id=user.id,
            question_id=q.id,
            answer={"code": "for(int i=1;i<=n;++i) cout<<i<<endl;"},
            is_correct=True,
            time_spent_seconds=20,
            hint_level_used=0,
            feedback="",
        )
        db.add(ans)
        await db.commit()
        await db.refresh(ans)
        return ans.id


async def _seed_mc_answer(user_payload: dict, client: AsyncClient) -> uuid.UUID:
    """非 coding 題型，用於 422 測試。"""
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
            content={"stem": "選 int", "options": ["a", "b"], "answer_index": 0},
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


async def test_predict_generate_requires_auth(client: AsyncClient):
    resp = await client.post(f"/comprehension/{uuid.uuid4()}/predict_output/generate")
    assert resp.status_code == 401


async def test_predict_grade_requires_auth(client: AsyncClient):
    resp = await client.post(
        f"/comprehension/{uuid.uuid4()}/predict_output/grade",
        json={"predicted_output": "x"},
    )
    assert resp.status_code == 401


# === generate ===


async def test_predict_generate_persists_and_hides_expected(client: AsyncClient):
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    llm = AsyncMock()
    llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({"input": "5\n", "expected": "1\n2\n3\n4\n5\n"})
        )
    )
    with patch("services.comprehension.predict_output._get_client", return_value=llm):
        resp = await client.post(
            f"/comprehension/{answer_id}/predict_output/generate",
            cookies={"authjs.session-token": token},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["comprehension_type"] == "predict_output"
    assert body["test_input"] == "5\n"
    # response 不應洩漏 expected
    assert "expected" not in body
    assert "expected_output" not in body

    # DB 內 expected 已存（在 prompt JSON 中）
    persisted = await _read_answer_state(answer_id)
    prompt_data = json.loads(persisted.comprehension_prompt or "{}")
    assert prompt_data["input"] == "5\n"
    assert prompt_data["expected"] == "1\n2\n3\n4\n5\n"


async def test_predict_generate_clears_old_answer_and_passed(client: AsyncClient):
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    # 先寫舊 state
    from sqlalchemy import update

    async with TestSessionFactory() as db:
        await db.execute(
            update(StudentAnswer)
            .where(StudentAnswer.id == answer_id)
            .values(
                comprehension_type="predict_output",
                comprehension_prompt=json.dumps({"input": "old", "expected": "old"}),
                comprehension_answer="舊預測",
                comprehension_passed=False,
            )
        )
        await db.commit()

    llm = AsyncMock()
    llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"input": "new\n", "expected": "out\n"}))
    )
    with patch("services.comprehension.predict_output._get_client", return_value=llm):
        await client.post(
            f"/comprehension/{answer_id}/predict_output/generate",
            cookies={"authjs.session-token": token},
        )

    persisted = await _read_answer_state(answer_id)
    assert persisted.comprehension_answer is None
    assert persisted.comprehension_passed is None


async def test_predict_generate_non_coding_returns_422(client: AsyncClient):
    answer_id = await _seed_mc_answer(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    resp = await client.post(
        f"/comprehension/{answer_id}/predict_output/generate",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "PREDICT_OUTPUT_NOT_APPLICABLE"


async def test_predict_generate_llm_failure_returns_503(client: AsyncClient):
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    with patch("services.comprehension.predict_output._get_client", return_value=None):
        resp = await client.post(
            f"/comprehension/{answer_id}/predict_output/generate",
            cookies={"authjs.session-token": token},
        )
    assert resp.status_code == 503
    assert resp.json()["error"] == "PREDICT_GENERATION_FAILED"


async def test_predict_generate_other_user_returns_404(client: AsyncClient):
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    other_token = encrypt_test_token(OTHER_PAYLOAD)
    await client.get("/auth/me", cookies={"authjs.session-token": other_token})

    llm = AsyncMock()
    llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"input": "x", "expected": "y"}))
    )
    with patch("services.comprehension.predict_output._get_client", return_value=llm):
        resp = await client.post(
            f"/comprehension/{answer_id}/predict_output/generate",
            cookies={"authjs.session-token": other_token},
        )
    assert resp.status_code == 404


# === grade ===


async def test_predict_grade_without_generate_returns_400(client: AsyncClient):
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    resp = await client.post(
        f"/comprehension/{answer_id}/predict_output/grade",
        json={"predicted_output": "1\n2\n3"},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "PREDICT_NOT_STARTED"


async def test_predict_grade_exact_match_passes(client: AsyncClient):
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    gen_llm = AsyncMock()
    gen_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({"input": "3\n", "expected": "1\n2\n3"})
        )
    )
    with patch("services.comprehension.predict_output._get_client", return_value=gen_llm):
        await client.post(
            f"/comprehension/{answer_id}/predict_output/generate",
            cookies={"authjs.session-token": token},
        )

    # exact 通過 — 不該呼叫 LLM；但保險用 patch 確保不洩漏
    with patch(
        "services.comprehension.predict_output._get_client", new=lambda: None
    ):
        resp = await client.post(
            f"/comprehension/{answer_id}/predict_output/grade",
            json={"predicted_output": "1\n2\n3"},
            cookies={"authjs.session-token": token},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["comprehension_passed"] is True
    assert body["match_method"] == "exact"
    assert body["expected_output"] == "1\n2\n3"

    persisted = await _read_answer_state(answer_id)
    assert persisted.comprehension_answer == "1\n2\n3"
    assert persisted.comprehension_passed is True


async def test_predict_grade_mismatch_with_llm_unavailable(client: AsyncClient):
    """嚴格不符 + LLM 不可用 → mismatch（passed=False）。"""
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    gen_llm = AsyncMock()
    gen_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({"input": "3\n", "expected": "1\n2\n3"})
        )
    )
    with patch("services.comprehension.predict_output._get_client", return_value=gen_llm):
        await client.post(
            f"/comprehension/{answer_id}/predict_output/generate",
            cookies={"authjs.session-token": token},
        )

    with patch("services.comprehension.predict_output._get_client", return_value=None):
        resp = await client.post(
            f"/comprehension/{answer_id}/predict_output/grade",
            json={"predicted_output": "完全不同的東西"},
            cookies={"authjs.session-token": token},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["comprehension_passed"] is False
    assert body["match_method"] == "mismatch"
    assert body["expected_output"] == "1\n2\n3"

    persisted = await _read_answer_state(answer_id)
    assert persisted.comprehension_passed is False


async def test_predict_grade_other_user_returns_404(client: AsyncClient):
    answer_id = await _seed_coding_answer(OWNER_PAYLOAD, client)
    owner_token = encrypt_test_token(OWNER_PAYLOAD)
    other_token = encrypt_test_token(OTHER_PAYLOAD)
    await client.get("/auth/me", cookies={"authjs.session-token": other_token})

    gen_llm = AsyncMock()
    gen_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"input": "3\n", "expected": "1\n2\n3"}))
    )
    with patch("services.comprehension.predict_output._get_client", return_value=gen_llm):
        await client.post(
            f"/comprehension/{answer_id}/predict_output/generate",
            cookies={"authjs.session-token": owner_token},
        )

    resp = await client.post(
        f"/comprehension/{answer_id}/predict_output/grade",
        json={"predicted_output": "1\n2\n3"},
        cookies={"authjs.session-token": other_token},
    )
    assert resp.status_code == 404
