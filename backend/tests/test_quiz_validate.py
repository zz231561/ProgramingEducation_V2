"""出題 Validate 階段測試。

涵蓋：
- 三面向全 pass → flip validated=True，passed=True，issues 空
- 答案不正確 → passed=False，validated 保持 False，issues 含答案問題
- 概念不符 → passed=False
- Bloom 不適當 → passed=False
- 多面向同時 fail → issues 列出全部
- LLM 例外 / 非 JSON / 缺欄位 → 502
"""

import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.errors import AppError
from models.quiz import Question, QuestionSource, QuestionType
from services.quiz import validate_question
from tests.helpers import TestSessionFactory


def _mock_completion(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _make_question() -> Question:
    return Question(
        type=QuestionType.MULTIPLE_CHOICE.value,
        concept_tags=["pointer-arithmetic"],
        bloom_level=3,
        difficulty=3,
        content={
            "stem": "下列何者正確？",
            "options": ["A", "B"],
            "answer_index": 0,
        },
        explanation="A 是正解",
        source=QuestionSource.GENERATED.value,
        validated=False,
    )


@contextmanager
def patched_validator(content: str | Exception):
    mock_client = AsyncMock()
    if isinstance(content, Exception):
        mock_client.chat.completions.create = AsyncMock(side_effect=content)
    else:
        mock_client.chat.completions.create = AsyncMock(
            return_value=_mock_completion(content)
        )
    with patch("services.quiz.validate._get_client", return_value=mock_client):
        yield


def _validator_json(
    answer_correct: bool = True,
    concept_fits: bool = True,
    bloom_appropriate: bool = True,
    answer_reason: str = "正確",
    concept_reason: str = "符合",
    bloom_reason: str = "適當",
) -> str:
    return json.dumps({
        "answer_correct": answer_correct,
        "answer_reason": answer_reason,
        "concept_fits": concept_fits,
        "concept_reason": concept_reason,
        "bloom_appropriate": bloom_appropriate,
        "bloom_reason": bloom_reason,
    })


# === Pass / Fail ===


@pytest.mark.asyncio
async def test_all_three_pass_flips_validated_true():
    q = _make_question()
    with patched_validator(_validator_json()):
        async with TestSessionFactory() as db:
            db.add(q)
            await db.flush()
            report = await validate_question(db, q)
            await db.commit()
            await db.refresh(q)

    assert report.passed is True
    assert report.issues == []
    assert q.validated is True


@pytest.mark.asyncio
async def test_answer_incorrect_does_not_validate():
    q = _make_question()
    bad = _validator_json(answer_correct=False, answer_reason="answer_index 對應錯選項")
    with patched_validator(bad):
        async with TestSessionFactory() as db:
            db.add(q)
            await db.flush()
            report = await validate_question(db, q)
            await db.commit()
            await db.refresh(q)

    assert report.passed is False
    assert report.answer_correct is False
    assert any("答案不正確" in i for i in report.issues)
    assert q.validated is False


@pytest.mark.asyncio
async def test_concept_mismatch_does_not_validate():
    q = _make_question()
    bad = _validator_json(concept_fits=False, concept_reason="實際在考 io-streams")
    with patched_validator(bad):
        async with TestSessionFactory() as db:
            db.add(q)
            await db.flush()
            report = await validate_question(db, q)

    assert report.passed is False
    assert report.concept_fits is False
    assert any("概念不符" in i for i in report.issues)


@pytest.mark.asyncio
async def test_bloom_too_high_does_not_validate():
    q = _make_question()
    bad = _validator_json(bloom_appropriate=False, bloom_reason="實際要求 EVALUATE")
    with patched_validator(bad):
        async with TestSessionFactory() as db:
            db.add(q)
            await db.flush()
            report = await validate_question(db, q)

    assert report.passed is False
    assert report.bloom_appropriate is False
    assert any("Bloom" in i for i in report.issues)


@pytest.mark.asyncio
async def test_multiple_failures_listed_in_issues():
    q = _make_question()
    bad = _validator_json(
        answer_correct=False,
        concept_fits=False,
        bloom_appropriate=False,
        answer_reason="A1",
        concept_reason="A2",
        bloom_reason="A3",
    )
    with patched_validator(bad):
        async with TestSessionFactory() as db:
            db.add(q)
            await db.flush()
            report = await validate_question(db, q)

    assert report.passed is False
    assert len(report.issues) == 3


# === 錯誤處理 ===


@pytest.mark.asyncio
async def test_llm_exception_raises_502_llm_error():
    q = _make_question()
    with patched_validator(Exception("openai timeout")):
        with pytest.raises(AppError) as exc_info:
            async with TestSessionFactory() as db:
                db.add(q)
                await db.flush()
                await validate_question(db, q)
    assert exc_info.value.status_code == 502
    assert exc_info.value.error == "LLM_ERROR"


@pytest.mark.asyncio
async def test_non_json_response_raises_parse_error():
    q = _make_question()
    with patched_validator("不是 JSON"):
        with pytest.raises(AppError) as exc_info:
            async with TestSessionFactory() as db:
                db.add(q)
                await db.flush()
                await validate_question(db, q)
    assert exc_info.value.error == "LLM_PARSE_ERROR"


@pytest.mark.asyncio
async def test_missing_field_raises_validation_error():
    q = _make_question()
    incomplete = json.dumps({"answer_correct": True})  # 缺 concept_fits / bloom_appropriate
    with patched_validator(incomplete):
        with pytest.raises(AppError) as exc_info:
            async with TestSessionFactory() as db:
                db.add(q)
                await db.flush()
                await validate_question(db, q)
    assert exc_info.value.error == "LLM_VALIDATION_ERROR"
