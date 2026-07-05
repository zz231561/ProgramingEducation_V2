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
from models.quiz import Question, QuestionSource, StudentAnswer
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


async def test_generate_with_concept_tag_targets_specified_concept(client: AsyncClient):
    """3-1e：指定 concept_tag → 直接針對該 concept 出題（跳過弱項邏輯）。"""
    # 兩個 concept；學生若用弱項邏輯會選 control-flow（mastery=0）；指定 syntax-basic 應蓋過
    async with TestSessionFactory() as db:
        db.add(Concept(
            tag="syntax-basic", name_zh="X", name_en="X",
            description="", difficulty_level=1, category="基礎",
        ))
        db.add(Concept(
            tag="control-flow", name_zh="Y", name_en="Y",
            description="", difficulty_level=2, category="進階",
        ))
        await db.commit()

    token = encrypt_test_token(STUDENT_PAYLOAD)
    with patched_quiz_llms(_VALID_MC_JSON):
        resp = await client.post(
            "/quiz/generate",
            json={"type": "multiple_choice", "bloom_level": 3, "concept_tag": "syntax-basic"},
            cookies={"authjs.session-token": token},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "syntax-basic" in body["concept_tags"]


async def test_generate_with_unknown_concept_tag_returns_404(client: AsyncClient):
    await _seed_starter_concept()
    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.post(
        "/quiz/generate",
        json={"type": "multiple_choice", "bloom_level": 3, "concept_tag": "nonexistent-tag"},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "CONCEPT_NOT_FOUND"


async def test_generate_cold_start_dynamic_fallback_when_no_legacy_tag(
    client: AsyncClient,
):
    """V2 cpp-XX seed 不含 syntax-basic：cold-start 應動態取難度最低 concept 出題。"""
    async with TestSessionFactory() as db:
        db.add(Concept(
            tag="cpp-25-if-else", name_zh="if-else", name_en="if-else",
            description="", difficulty_level=2, category="控制流", video_order=22,
        ))
        db.add(Concept(
            tag="cpp-04-first-program", name_zh="第一支程式", name_en="First Program",
            description="", difficulty_level=1, category="入門", video_order=1,
        ))
        db.add(Concept(
            tag="cpp-05-syntax", name_zh="基本語法", name_en="Basic Syntax",
            description="", difficulty_level=1, category="入門", video_order=2,
        ))
        await db.commit()

    token = encrypt_test_token(STUDENT_PAYLOAD)
    with patched_quiz_llms(_VALID_MC_JSON):
        resp = await client.post(
            "/quiz/generate",
            json={"type": "multiple_choice", "bloom_level": 3},
            cookies={"authjs.session-token": token},
        )

    assert resp.status_code == 200
    body = resp.json()
    # 應挑 difficulty_level=1 且 video_order 最小（cpp-04-first-program）
    assert "cpp-04-first-program" in body["concept_tags"]


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


# === Phase 6-3b /quiz/from-bank ===


async def _seed_validated_bank_question(concept_tag: str) -> Question:
    async with TestSessionFactory() as db:
        q = Question(
            type="multiple_choice",
            concept_tags=[concept_tag],
            bloom_level=3,
            difficulty=2,
            content={
                "stem": "題庫題：下列何者正確？",
                "options": ["A", "B", "C", "D"],
                "answer_index": 1,
            },
            explanation="B is correct.",
            source=QuestionSource.GENERATED.value,
            validated=True,
        )
        db.add(q)
        await db.commit()
        await db.refresh(q)
        return q


async def test_from_bank_requires_auth(client: AsyncClient):
    resp = await client.get("/quiz/from-bank?concept_tag=syntax-basic")
    assert resp.status_code == 401


async def test_from_bank_returns_masked_question_when_available(client: AsyncClient):
    """命中題庫 → 200 + 題目（答案已 mask）；不呼叫任何 LLM。"""
    await _seed_validated_bank_question("syntax-basic")
    token = encrypt_test_token(STUDENT_PAYLOAD)

    resp = await client.get(
        "/quiz/from-bank?concept_tag=syntax-basic",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "multiple_choice"
    assert "options" in body["content"]
    assert "answer_index" not in body["content"]  # 答案 mask
    assert "syntax-basic" in body["concept_tags"]


async def test_from_bank_empty_returns_404(client: AsyncClient):
    """題庫無題 → 404 QUESTION_BANK_EMPTY，前端可 fallback /quiz/generate。"""
    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.get(
        "/quiz/from-bank?concept_tag=syntax-basic",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "QUESTION_BANK_EMPTY"


async def test_from_bank_weakness_mode_without_concept_tag(client: AsyncClient):
    """U2d：省略 concept_tag → 後端挑目標概念（cold-start 落到 syntax-basic）再抽題庫。"""
    await _seed_starter_concept()
    await _seed_validated_bank_question("syntax-basic")
    token = encrypt_test_token(STUDENT_PAYLOAD)

    resp = await client.get(
        "/quiz/from-bank",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    assert "syntax-basic" in resp.json()["concept_tags"]


async def test_from_bank_question_type_filter(client: AsyncClient):
    """U2d：question_type 過濾——題庫只有 MC 卻要 coding → 404 fallback。"""
    await _seed_validated_bank_question("syntax-basic")
    token = encrypt_test_token(STUDENT_PAYLOAD)

    resp = await client.get(
        "/quiz/from-bank?concept_tag=syntax-basic&question_type=coding",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "QUESTION_BANK_EMPTY"


async def test_from_bank_excludes_already_answered(client: AsyncClient):
    """U2d 重複曝光防護：唯一一題已答過 → 404（前端 fallback 現生新題）。"""
    q = await _seed_validated_bank_question("syntax-basic")
    token = encrypt_test_token(STUDENT_PAYLOAD)

    # 先命中一次並作答
    first = await client.get(
        "/quiz/from-bank?concept_tag=syntax-basic",
        cookies={"authjs.session-token": token},
    )
    assert first.status_code == 200
    submit = await client.post(
        "/quiz/submit",
        json={"question_id": str(q.id), "answer": {"selected_index": 1}},
        cookies={"authjs.session-token": token},
    )
    assert submit.status_code == 200

    # 再抽 → 已答過的題被排除
    resp = await client.get(
        "/quiz/from-bank?concept_tag=syntax-basic",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "QUESTION_BANK_EMPTY"


async def test_from_bank_only_returns_matching_tag(client: AsyncClient):
    """有其他 tag 的 validated 題不應命中查詢 tag。"""
    await _seed_validated_bank_question("control-flow")
    token = encrypt_test_token(STUDENT_PAYLOAD)

    resp = await client.get(
        "/quiz/from-bank?concept_tag=syntax-basic",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "QUESTION_BANK_EMPTY"
