"""出題 Generate 階段測試。

涵蓋：
- 三種 type 各自能解析正確 LLM 回應 → Question 物件正確
- LLM 回傳非 JSON → 502 LLM_PARSE_ERROR
- LLM 回傳缺欄位（schema 不符）→ 502 LLM_VALIDATION_ERROR
- LLM 拋例外 → 502 LLM_ERROR
- RAG 失敗仍能出題（fallback 空 chunks）
- DB 寫入欄位正確
"""

import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from core.errors import AppError
from models.concept import Concept
from models.quiz import Question, QuestionSource, QuestionType
from services.quiz import generate_question
from tests.helpers import TestSessionFactory


def _mock_completion(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


async def _seed_concept() -> Concept:
    async with TestSessionFactory() as db:
        c = Concept(
            tag="pointer-arithmetic",
            name_zh="指標運算",
            name_en="Pointer Arithmetic",
            description="指標宣告、解引用、指標算術。",
            difficulty_level=3,
            category="記憶體",
        )
        db.add(c)
        await db.commit()
        await db.refresh(c)
        return c


@contextmanager
def patched_llm(content: str | Exception, rag_error: Exception | None = None):
    """同時 patch `_get_client` 與 `retrieve_chunks`（RAG 預設回 []）。"""
    mock_client = AsyncMock()
    if isinstance(content, Exception):
        mock_client.chat.completions.create = AsyncMock(side_effect=content)
    else:
        mock_client.chat.completions.create = AsyncMock(
            return_value=_mock_completion(content)
        )
    rag_mock = (
        AsyncMock(side_effect=rag_error) if rag_error else AsyncMock(return_value=[])
    )
    with (
        patch("services.quiz.generate._get_client", return_value=mock_client),
        patch("services.quiz.generate.retrieve_chunks", rag_mock),
    ):
        yield


# === 三種 type 各自能解析 ===


@pytest.mark.asyncio
async def test_generate_multiple_choice_success():
    concept = await _seed_concept()
    llm_json = json.dumps({
        "stem": "下列哪個運算式正確地對 nullptr 做防護？",
        "options": [
            "if (p == nullptr) ...",
            "if (p = nullptr) ...",
            "if (!nullptr) ...",
            "if (p != null) ...",
        ],
        "answer_index": 0,
        "explanation": "== 是比較運算子，= 是賦值；nullptr 是 C++11 的指標常量。",
    })

    with patched_llm(llm_json):
        async with TestSessionFactory() as db:
            q = await generate_question(
                db, concept, QuestionType.MULTIPLE_CHOICE, difficulty=3, bloom_level=3
            )
            await db.commit()
            await db.refresh(q)

    assert q.type == "multiple_choice"
    assert q.concept_tags == ["pointer-arithmetic"]
    assert q.bloom_level == 3
    assert q.difficulty == 3
    assert q.source == QuestionSource.GENERATED.value
    assert q.validated is False
    assert q.content["answer_index"] == 0
    assert len(q.content["options"]) == 4


@pytest.mark.asyncio
async def test_generate_fill_blank_success():
    concept = await _seed_concept()
    llm_json = json.dumps({
        "stem": "對指標 p 做解引用以取得它指向的值，使用運算子 ___。",
        "answers": ["*"],
        "explanation": "* 是解引用運算子。",
    })

    with patched_llm(llm_json):
        async with TestSessionFactory() as db:
            q = await generate_question(
                db, concept, QuestionType.FILL_BLANK, difficulty=2, bloom_level=2
            )
            await db.commit()
            await db.refresh(q)

    assert q.type == "fill_blank"
    assert q.content["answers"] == ["*"]


@pytest.mark.asyncio
async def test_generate_coding_success():
    concept = await _seed_concept()
    llm_json = json.dumps({
        "stem": "寫一個函式 safe_deref 接收 int*，若非 nullptr 回傳值否則回 -1。",
        "starter_code": "int safe_deref(int* p) {\n    // TODO\n}",
        "expected_output": None,
        "explanation": "需先檢查 nullptr。",
    })

    with patched_llm(llm_json):
        async with TestSessionFactory() as db:
            q = await generate_question(
                db, concept, QuestionType.CODING, difficulty=4, bloom_level=4
            )
            await db.commit()
            await db.refresh(q)

    assert q.type == "coding"
    assert q.content["starter_code"].startswith("int safe_deref")
    assert q.content["expected_output"] is None


# === 錯誤處理 ===


@pytest.mark.asyncio
async def test_generate_llm_returns_non_json_raises_parse_error():
    concept = await _seed_concept()
    with patched_llm("這不是 JSON"):
        with pytest.raises(AppError) as exc_info:
            async with TestSessionFactory() as db:
                await generate_question(
                    db, concept, QuestionType.MULTIPLE_CHOICE, 3, 3
                )
    assert exc_info.value.status_code == 502
    assert exc_info.value.error == "LLM_PARSE_ERROR"


@pytest.mark.asyncio
async def test_generate_schema_violation_raises_validation_error():
    """LLM 回 multiple_choice 但少 answer_index → 應拋 LLM_VALIDATION_ERROR。"""
    concept = await _seed_concept()
    bad_json = json.dumps({
        "stem": "下列何者正確？",
        "options": ["a", "b"],
        # 缺 answer_index
        "explanation": "...",
    })
    with patched_llm(bad_json):
        with pytest.raises(AppError) as exc_info:
            async with TestSessionFactory() as db:
                await generate_question(
                    db, concept, QuestionType.MULTIPLE_CHOICE, 3, 3
                )
    assert exc_info.value.status_code == 502
    assert exc_info.value.error == "LLM_VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_generate_llm_exception_raises_502():
    concept = await _seed_concept()
    with patched_llm(Exception("openai timeout")):
        with pytest.raises(AppError) as exc_info:
            async with TestSessionFactory() as db:
                await generate_question(
                    db, concept, QuestionType.MULTIPLE_CHOICE, 3, 3
                )
    assert exc_info.value.status_code == 502
    assert exc_info.value.error == "LLM_ERROR"


@pytest.mark.asyncio
async def test_generate_rag_failure_does_not_block_generation():
    """RAG 失敗應靜默 fallback 為空 chunks，仍能出題。"""
    concept = await _seed_concept()
    llm_json = json.dumps({
        "stem": "下列何者正確？",
        "options": ["a", "b"],
        "answer_index": 0,
        "explanation": "解釋",
    })
    with patched_llm(llm_json, rag_error=RuntimeError("vector db down")):
        async with TestSessionFactory() as db:
            q = await generate_question(
                db, concept, QuestionType.MULTIPLE_CHOICE, 3, 3
            )
            await db.commit()
            await db.refresh(q)
    assert q.type == "multiple_choice"


# === DB 寫入驗證 ===


@pytest.mark.asyncio
async def test_generated_question_persists_with_correct_metadata():
    concept = await _seed_concept()
    llm_json = json.dumps({
        "stem": "下列何者正確？",
        "options": ["a", "b"],
        "answer_index": 0,
        "explanation": "解釋",
    })
    with patched_llm(llm_json):
        async with TestSessionFactory() as db:
            await generate_question(
                db, concept, QuestionType.MULTIPLE_CHOICE, difficulty=2, bloom_level=2
            )
            await db.commit()

    async with TestSessionFactory() as db:
        rows = (await db.execute(select(Question))).scalars().all()
        assert len(rows) == 1
        q = rows[0]
        assert q.type == "multiple_choice"
        assert q.concept_tags == ["pointer-arithmetic"]
        assert q.difficulty == 2
        assert q.bloom_level == 2
        assert q.source == "generated"
        assert q.validated is False
