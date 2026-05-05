"""Trigger-suggestion HTTP 整合測試（roadmap 2-6e）。

涵蓋：
- 401 未登入
- 跨使用者 → 404
- cold start（無歷史）→ EPL
- 高通過率 → 不觸發
- 中通過率 + coding → predict_output
- 中高通過率 + 非 coding → fallback EPL
- 低通過率 → EPL
"""

import uuid

from httpx import AsyncClient

from models.quiz import Question, StudentAnswer
from tests.helpers import TestSessionFactory, encrypt_test_token

OWNER_PAYLOAD = {
    "sub": "trig-owner",
    "email": "trig-owner@test.com",
    "name": "Trig Owner",
    "googleId": "g-trig-owner",
}

OTHER_PAYLOAD = {
    "sub": "trig-other",
    "email": "trig-other@test.com",
    "name": "Trig Other",
    "googleId": "g-trig-other",
}


async def _seed_answer(
    user_payload: dict,
    client: AsyncClient,
    *,
    qtype: str = "coding",
    history_passed: list[bool] | None = None,
) -> uuid.UUID:
    """建立 user + 一批帶 comprehension_passed 的歷史 + 1 筆當前作答。回當前 answer.id。"""
    token = encrypt_test_token(user_payload)
    await client.get("/auth/me", cookies={"authjs.session-token": token})

    from sqlalchemy import select

    from models.user import User

    async with TestSessionFactory() as db:
        user = (
            await db.execute(select(User).where(User.google_id == user_payload["googleId"]))
        ).scalar_one()

        if qtype == "coding":
            content = {"stem": "x", "starter_code": "", "test_cases": []}
        else:
            content = {"stem": "x", "options": ["a", "b"], "answer_index": 0}

        q = Question(
            type=qtype,
            concept_tags=["syntax-basic"],
            bloom_level=3,
            difficulty=2,
            content=content,
            explanation="",
            source="generated",
            validated=True,
        )
        db.add(q)
        await db.flush()

        # 歷史紀錄
        for i, passed in enumerate(history_passed or []):
            hist = StudentAnswer(
                user_id=user.id,
                question_id=q.id,
                answer={"x": i},
                is_correct=True,
                time_spent_seconds=10,
                hint_level_used=0,
                feedback="",
                comprehension_type="epl",
                comprehension_prompt="hist",
                comprehension_answer="hist",
                comprehension_passed=passed,
            )
            db.add(hist)

        # 當前作答（無 comprehension）
        current = StudentAnswer(
            user_id=user.id,
            question_id=q.id,
            answer={"code": "x"} if qtype == "coding" else {"selected": 0},
            is_correct=True,
            time_spent_seconds=10,
            hint_level_used=0,
            feedback="",
        )
        db.add(current)
        await db.commit()
        await db.refresh(current)
        return current.id


# === auth ===


async def test_trigger_requires_auth(client: AsyncClient):
    resp = await client.get(f"/comprehension/trigger-suggestion/{uuid.uuid4()}")
    assert resp.status_code == 401


# === ownership ===


async def test_trigger_other_user_returns_404(client: AsyncClient):
    answer_id = await _seed_answer(OWNER_PAYLOAD, client, qtype="coding")
    other_token = encrypt_test_token(OTHER_PAYLOAD)
    await client.get("/auth/me", cookies={"authjs.session-token": other_token})

    resp = await client.get(
        f"/comprehension/trigger-suggestion/{answer_id}",
        cookies={"authjs.session-token": other_token},
    )
    assert resp.status_code == 404


# === decision matrix ===


async def test_trigger_cold_start_returns_epl(client: AsyncClient):
    answer_id = await _seed_answer(OWNER_PAYLOAD, client, qtype="coding", history_passed=[])
    token = encrypt_test_token(OWNER_PAYLOAD)

    resp = await client.get(
        f"/comprehension/trigger-suggestion/{answer_id}",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["should_trigger"] is True
    assert body["suggested_type"] == "epl"
    assert body["pass_rate"] is None
    assert body["sample_size"] == 0


async def test_trigger_high_pass_rate_skips(client: AsyncClient):
    answer_id = await _seed_answer(
        OWNER_PAYLOAD, client, qtype="coding",
        history_passed=[True, True, True, True, True],  # 100%
    )
    token = encrypt_test_token(OWNER_PAYLOAD)

    resp = await client.get(
        f"/comprehension/trigger-suggestion/{answer_id}",
        cookies={"authjs.session-token": token},
    )
    body = resp.json()
    assert body["should_trigger"] is False
    assert body["suggested_type"] is None
    assert body["pass_rate"] == 1.0


async def test_trigger_mid_pass_rate_picks_predict_output_for_coding(client: AsyncClient):
    """2/5 = 0.4 → 中段（[0.3, 0.6)）→ predict_output（coding 題）。"""
    answer_id = await _seed_answer(
        OWNER_PAYLOAD, client, qtype="coding",
        history_passed=[True, False, False, True, False],  # 2/5 = 0.4
    )
    token = encrypt_test_token(OWNER_PAYLOAD)

    resp = await client.get(
        f"/comprehension/trigger-suggestion/{answer_id}",
        cookies={"authjs.session-token": token},
    )
    body = resp.json()
    assert body["should_trigger"] is True
    assert body["suggested_type"] == "predict_output"
    assert body["pass_rate"] == 0.4


async def test_trigger_mid_high_non_coding_falls_back_to_epl(client: AsyncClient):
    """3/5 = 0.6 → 中高 → 應給 VARIATION，但非 coding → fallback EPL。"""
    answer_id = await _seed_answer(
        OWNER_PAYLOAD, client, qtype="multiple_choice",
        history_passed=[True, True, True, False, False],  # 3/5 = 0.6
    )
    token = encrypt_test_token(OWNER_PAYLOAD)

    resp = await client.get(
        f"/comprehension/trigger-suggestion/{answer_id}",
        cookies={"authjs.session-token": token},
    )
    body = resp.json()
    assert body["should_trigger"] is True
    assert body["suggested_type"] == "epl"  # fallback
    assert "fallback" in body["reason"]


async def test_trigger_low_pass_rate_picks_epl(client: AsyncClient):
    answer_id = await _seed_answer(
        OWNER_PAYLOAD, client, qtype="coding",
        history_passed=[False, False, False, False, False],  # 0%
    )
    token = encrypt_test_token(OWNER_PAYLOAD)

    resp = await client.get(
        f"/comprehension/trigger-suggestion/{answer_id}",
        cookies={"authjs.session-token": token},
    )
    body = resp.json()
    assert body["should_trigger"] is True
    assert body["suggested_type"] == "epl"
    assert body["pass_rate"] == 0.0
    assert "回基礎" in body["reason"]
