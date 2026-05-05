"""EPL HTTP 整合測試（roadmap 2-6b）— mock LLM，驗證 generate / grade 兩 endpoint 流程。

涵蓋：
- 401 未登入
- generate 成功 → 寫 type/prompt + 清空舊 answer/passed
- generate LLM 失敗 → 503
- generate 跨使用者 → 404
- grade 未先 generate → 400 EPL_NOT_STARTED
- grade 成功 → 寫 answer/passed + 回細項分數
- grade LLM 失敗 → 200 但 passed=None（不擋學生）
- grade 跨使用者 → 404
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from models.quiz import ComprehensionType, Question, StudentAnswer
from tests.helpers import TestSessionFactory, encrypt_test_token

OWNER_PAYLOAD = {
    "sub": "epl-owner",
    "email": "epl-owner@test.com",
    "name": "EPL Owner",
    "googleId": "g-epl-owner",
}

OTHER_PAYLOAD = {
    "sub": "epl-other",
    "email": "epl-other@test.com",
    "name": "EPL Other",
    "googleId": "g-epl-other",
}


def _llm_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


async def _seed_answer_for(user_payload: dict, client: AsyncClient) -> uuid.UUID:
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
            answer={"code": "int main() { return 0; }"},
            is_correct=True,
            time_spent_seconds=30,
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


async def test_epl_generate_requires_auth(client: AsyncClient):
    resp = await client.post(f"/comprehension/{uuid.uuid4()}/epl/generate")
    assert resp.status_code == 401


async def test_epl_grade_requires_auth(client: AsyncClient):
    resp = await client.post(
        f"/comprehension/{uuid.uuid4()}/epl/grade",
        json={"epl_answer": "x"},
    )
    assert resp.status_code == 401


# === generate ===


async def test_epl_generate_persists_prompt_and_clears_answer(client: AsyncClient):
    answer_id = await _seed_answer_for(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    # 先手動設定舊的 answer/passed 來驗證 generate 會清空
    from sqlalchemy import update

    async with TestSessionFactory() as db:
        await db.execute(
            update(StudentAnswer)
            .where(StudentAnswer.id == answer_id)
            .values(
                comprehension_type="epl",
                comprehension_prompt="舊題",
                comprehension_answer="舊答",
                comprehension_passed=False,
            )
        )
        await db.commit()

    llm = AsyncMock()
    llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"prompt": "請用自己的話解釋你的程式"}))
    )

    with patch("services.comprehension.epl._get_client", return_value=llm):
        resp = await client.post(
            f"/comprehension/{answer_id}/epl/generate",
            cookies={"authjs.session-token": token},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["comprehension_type"] == "epl"
    assert body["comprehension_prompt"] == "請用自己的話解釋你的程式"

    # DB 確認舊 answer/passed 已清空
    persisted = await _read_answer_state(answer_id)
    assert persisted.comprehension_prompt == "請用自己的話解釋你的程式"
    assert persisted.comprehension_answer is None
    assert persisted.comprehension_passed is None


async def test_epl_generate_llm_failure_returns_503(client: AsyncClient):
    answer_id = await _seed_answer_for(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    with patch("services.comprehension.epl._get_client", return_value=None):
        resp = await client.post(
            f"/comprehension/{answer_id}/epl/generate",
            cookies={"authjs.session-token": token},
        )
    assert resp.status_code == 503
    assert resp.json()["error"] == "EPL_GENERATION_FAILED"


async def test_epl_generate_other_user_returns_404(client: AsyncClient):
    answer_id = await _seed_answer_for(OWNER_PAYLOAD, client)
    other_token = encrypt_test_token(OTHER_PAYLOAD)
    await client.get("/auth/me", cookies={"authjs.session-token": other_token})

    llm = AsyncMock()
    llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"prompt": "x"}))
    )
    with patch("services.comprehension.epl._get_client", return_value=llm):
        resp = await client.post(
            f"/comprehension/{answer_id}/epl/generate",
            cookies={"authjs.session-token": other_token},
        )
    assert resp.status_code == 404


# === grade ===


async def test_epl_grade_without_generate_returns_400(client: AsyncClient):
    answer_id = await _seed_answer_for(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    resp = await client.post(
        f"/comprehension/{answer_id}/epl/grade",
        json={"epl_answer": "我用了迴圈"},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "EPL_NOT_STARTED"


async def test_epl_grade_success_persists_passed(client: AsyncClient):
    answer_id = await _seed_answer_for(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    # 先 generate
    gen_llm = AsyncMock()
    gen_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"prompt": "解釋你的程式"}))
    )
    with patch("services.comprehension.epl._get_client", return_value=gen_llm):
        await client.post(
            f"/comprehension/{answer_id}/epl/generate",
            cookies={"authjs.session-token": token},
        )

    # 再 grade（高分通過）
    grade_llm = AsyncMock()
    grade_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({
            "conceptual_correctness": 0.9,
            "specificity": 0.8,
            "causality": 0.7,
            "feedback": "解釋具體",
        }))
    )
    with patch("services.comprehension.epl._get_client", return_value=grade_llm):
        resp = await client.post(
            f"/comprehension/{answer_id}/epl/grade",
            json={"epl_answer": "我從 0 跑到 n，每次比較找最大"},
            cookies={"authjs.session-token": token},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["comprehension_passed"] is True
    assert body["conceptual_correctness"] == 0.9
    assert body["feedback"] == "解釋具體"

    persisted = await _read_answer_state(answer_id)
    assert persisted.comprehension_answer == "我從 0 跑到 n，每次比較找最大"
    assert persisted.comprehension_passed is True


async def test_epl_grade_llm_failure_returns_passed_none(client: AsyncClient):
    """LLM 評分失敗 → 200 但 passed=None；學生回答仍持久化方便重試。"""
    answer_id = await _seed_answer_for(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    gen_llm = AsyncMock()
    gen_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"prompt": "解釋你的程式"}))
    )
    with patch("services.comprehension.epl._get_client", return_value=gen_llm):
        await client.post(
            f"/comprehension/{answer_id}/epl/generate",
            cookies={"authjs.session-token": token},
        )

    # grade 階段 LLM 不可用
    with patch("services.comprehension.epl._get_client", return_value=None):
        resp = await client.post(
            f"/comprehension/{answer_id}/epl/grade",
            json={"epl_answer": "（短答）"},
            cookies={"authjs.session-token": token},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["comprehension_passed"] is None
    assert body["feedback"] is None

    persisted = await _read_answer_state(answer_id)
    assert persisted.comprehension_answer == "（短答）"
    assert persisted.comprehension_passed is None


async def test_epl_grade_other_user_returns_404(client: AsyncClient):
    answer_id = await _seed_answer_for(OWNER_PAYLOAD, client)
    owner_token = encrypt_test_token(OWNER_PAYLOAD)
    other_token = encrypt_test_token(OTHER_PAYLOAD)
    await client.get("/auth/me", cookies={"authjs.session-token": other_token})

    # owner generate
    gen_llm = AsyncMock()
    gen_llm.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"prompt": "解釋"}))
    )
    with patch("services.comprehension.epl._get_client", return_value=gen_llm):
        await client.post(
            f"/comprehension/{answer_id}/epl/generate",
            cookies={"authjs.session-token": owner_token},
        )

    # other 嘗試 grade
    resp = await client.post(
        f"/comprehension/{answer_id}/epl/grade",
        json={"epl_answer": "x"},
        cookies={"authjs.session-token": other_token},
    )
    assert resp.status_code == 404
