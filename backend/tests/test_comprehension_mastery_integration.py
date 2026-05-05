"""Comprehension grade → BKT mastery 整合測試（roadmap 2-6e）。

驗證三條 grade pipeline（EPL / Predict / Variation）通過後，學生的 student_mastery 表
對應 concept_tags 的 confidence 確實被 BKT 線上更新。

設計：
- 先 seed 一個 concept (syntax-basic)
- 學生答對 1 題後，跑 grade flow
- 對比 student_mastery 表的 confidence 變化
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient
from sqlalchemy import select

from models.concept import Concept
from models.mastery import StudentMastery
from models.quiz import Question, StudentAnswer
from models.user import User
from tests.helpers import TestSessionFactory, encrypt_test_token

USER_PAYLOAD = {
    "sub": "mastery-int",
    "email": "mastery-int@test.com",
    "name": "Mastery Integration",
    "googleId": "g-mastery-int",
}


def _llm_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


async def _seed_concept_and_answer(client: AsyncClient) -> tuple[uuid.UUID, uuid.UUID]:
    """seed concept + question + student_answer，回 (answer_id, concept_id)。"""
    token = encrypt_test_token(USER_PAYLOAD)
    await client.get("/auth/me", cookies={"authjs.session-token": token})

    async with TestSessionFactory() as db:
        user = (
            await db.execute(select(User).where(User.google_id == USER_PAYLOAD["googleId"]))
        ).scalar_one()
        c = Concept(
            tag="syntax-basic",
            name_zh="基礎語法",
            name_en="Basic Syntax",
            description="x",
            difficulty_level=1,
            category="基礎",
        )
        db.add(c)
        await db.flush()
        q = Question(
            type="coding",
            concept_tags=["syntax-basic"],
            bloom_level=3,
            difficulty=2,
            content={"stem": "x", "starter_code": "", "test_cases": []},
            explanation="",
            source="generated",
            validated=True,
        )
        db.add(q)
        await db.flush()
        ans = StudentAnswer(
            user_id=user.id,
            question_id=q.id,
            answer={"code": "int main() {}"},
            is_correct=True,
            time_spent_seconds=10,
            hint_level_used=0,
            feedback="",
        )
        db.add(ans)
        await db.commit()
        await db.refresh(ans)
        return ans.id, c.id


async def _read_mastery(user_email: str, concept_id: uuid.UUID) -> StudentMastery | None:
    async with TestSessionFactory() as db:
        user = (
            await db.execute(select(User).where(User.email == user_email))
        ).scalar_one()
        return (
            await db.execute(
                select(StudentMastery)
                .where(StudentMastery.user_id == user.id)
                .where(StudentMastery.concept_id == concept_id)
            )
        ).scalar_one_or_none()


# === EPL ===


async def test_epl_grade_passed_updates_mastery(client: AsyncClient):
    answer_id, concept_id = await _seed_concept_and_answer(client)
    token = encrypt_test_token(USER_PAYLOAD)

    gen_llm = AsyncMock()
    gen_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"prompt": "解釋你的程式"}))
    )
    with patch("services.comprehension.epl._get_client", return_value=gen_llm):
        await client.post(
            f"/comprehension/{answer_id}/epl/generate",
            cookies={"authjs.session-token": token},
        )

    grade_llm = AsyncMock()
    grade_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({
            "conceptual_correctness": 0.9,
            "specificity": 0.8,
            "causality": 0.7,
            "feedback": "好",
        }))
    )
    with patch("services.comprehension.epl._get_client", return_value=grade_llm):
        await client.post(
            f"/comprehension/{answer_id}/epl/grade",
            json={"epl_answer": "詳細解釋"},
            cookies={"authjs.session-token": token},
        )

    mastery = await _read_mastery(USER_PAYLOAD["email"], concept_id)
    assert mastery is not None
    assert mastery.confidence > 0  # BKT 上調過


async def test_epl_grade_passed_none_does_not_update_mastery(client: AsyncClient):
    """LLM fallback → passed=None → 不該建立 mastery row。"""
    answer_id, concept_id = await _seed_concept_and_answer(client)
    token = encrypt_test_token(USER_PAYLOAD)

    gen_llm = AsyncMock()
    gen_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"prompt": "解釋"}))
    )
    with patch("services.comprehension.epl._get_client", return_value=gen_llm):
        await client.post(
            f"/comprehension/{answer_id}/epl/generate",
            cookies={"authjs.session-token": token},
        )

    # grade LLM 不可用 → passed=None
    with patch("services.comprehension.epl._get_client", return_value=None):
        await client.post(
            f"/comprehension/{answer_id}/epl/grade",
            json={"epl_answer": "x"},
            cookies={"authjs.session-token": token},
        )

    mastery = await _read_mastery(USER_PAYLOAD["email"], concept_id)
    assert mastery is None  # 從未被 update_mastery touch 過


# === Predict ===


async def test_predict_grade_passed_updates_mastery(client: AsyncClient):
    answer_id, concept_id = await _seed_concept_and_answer(client)
    token = encrypt_test_token(USER_PAYLOAD)

    gen_llm = AsyncMock()
    gen_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({"input": "1\n", "expected": "1"})
        )
    )
    with patch("services.comprehension.predict_output._get_client", return_value=gen_llm):
        await client.post(
            f"/comprehension/{answer_id}/predict_output/generate",
            cookies={"authjs.session-token": token},
        )

    # exact 通過（無需 LLM）
    with patch("services.comprehension.predict_output._get_client", new=lambda: None):
        await client.post(
            f"/comprehension/{answer_id}/predict_output/grade",
            json={"predicted_output": "1"},
            cookies={"authjs.session-token": token},
        )

    mastery = await _read_mastery(USER_PAYLOAD["email"], concept_id)
    assert mastery is not None
    assert mastery.confidence > 0


# === Variation ===


async def test_variation_grade_passed_updates_mastery(client: AsyncClient):
    answer_id, concept_id = await _seed_concept_and_answer(client)
    token = encrypt_test_token(USER_PAYLOAD)

    gen_llm = AsyncMock()
    gen_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({
                "stem": "x", "starter_code": "", "test_cases": [], "concept_focus": ""
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
        return_value=_llm_response(json.dumps({"passed": True, "feedback": "好"}))
    )
    with patch("services.comprehension.variation._get_client", return_value=grade_llm):
        await client.post(
            f"/comprehension/{answer_id}/variation/grade",
            json={"student_code": "code"},
            cookies={"authjs.session-token": token},
        )

    mastery = await _read_mastery(USER_PAYLOAD["email"], concept_id)
    assert mastery is not None
    assert mastery.confidence > 0
