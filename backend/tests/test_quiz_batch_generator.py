"""Phase 6-3a-2 測試：quiz batch generator + scripts.generate_unit_questions。

涵蓋：
- per-concept N 題：題型 mix（multiple_choice + coding）全 validated → 入庫
- validate 失敗（concept_fits=False）→ 該題 rollback、不入庫、不阻擋同 concept 下一題
- generate 例外（LLM_PARSE_ERROR）→ 該題 fail、不影響下一題
- NO_VIDEO_ORDER concept → 422 防呆
- generate_all skip_existing：已有足量 validated 題 → 跳過該 concept
- list_target_concepts only 過濾
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from core.errors import AppError
from models.concept import Concept
from models.quiz import Question, QuestionSource, QuestionType
from services.quiz.batch_generator import (
    ConceptBatchResult,
    generate_all,
    generate_questions_for_concept,
    list_target_concepts,
)
from tests.helpers import TestSessionFactory


# === Mock helpers ===


def _mock_completion(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


_VALID_MC_JSON = json.dumps({
    "stem": "下列何者正確？",
    "options": ["a", "b"],
    "answer_index": 0,
    "explanation": "解釋",
})

_VALID_CODING_JSON = json.dumps({
    "stem": "請依字幕示範實作 add(int a, int b)",
    "starter_code": "int add(int a, int b) {\n    // TODO\n}",
    "expected_output": None,
    "explanation": "回傳 a+b 即可",
})


def _validator_json(
    answer_correct: bool = True,
    concept_fits: bool = True,
    bloom_appropriate: bool = True,
) -> str:
    return json.dumps({
        "answer_correct": answer_correct,
        "answer_reason": "ok",
        "concept_fits": concept_fits,
        "concept_reason": "ok",
        "bloom_appropriate": bloom_appropriate,
        "bloom_reason": "ok",
    })


@contextmanager
def patched_pipeline(
    generate_responses: list[str | Exception],
    validate_responses: list[str | Exception],
):
    """同時 patch generate + validate 的 LLM client，以及兩條 RAG retrieve。

    generate_responses / validate_responses 依呼叫順序逐筆消費（side_effect list）。
    """
    gen_client = AsyncMock()
    gen_client.chat.completions.create = AsyncMock(
        side_effect=[
            r if isinstance(r, Exception) else _mock_completion(r)
            for r in generate_responses
        ]
    )
    val_client = AsyncMock()
    val_client.chat.completions.create = AsyncMock(
        side_effect=[
            r if isinstance(r, Exception) else _mock_completion(r)
            for r in validate_responses
        ]
    )
    with (
        patch("services.quiz.generate._get_client", return_value=gen_client),
        patch("services.quiz.validate._get_client", return_value=val_client),
        patch(
            "services.quiz.generate.retrieve_chunks",
            AsyncMock(return_value=[]),
        ),
        patch(
            "services.quiz.generate.get_chunks_by_video_order",
            AsyncMock(return_value=[]),
        ),
    ):
        yield


# === Concept seeding ===


async def _seed_concept(
    tag: str = "syntax-basic",
    video_order: int | None = 4,
) -> Concept:
    async with TestSessionFactory() as db:
        c = Concept(
            tag=tag,
            name_zh="語法基礎",
            name_en="Syntax Basics",
            description="C++ 基本語法、變數宣告、輸出。",
            difficulty_level=2,
            category="基礎",
            video_order=video_order,
        )
        db.add(c)
        await db.commit()
        await db.refresh(c)
        return c


# === per-concept 路徑 ===


@pytest.mark.asyncio
async def test_all_questions_validated_persist_to_db():
    """2 題都通過 generate + validate → questions 表寫入 2 列、皆 validated=True。"""
    concept = await _seed_concept()
    with patched_pipeline(
        generate_responses=[_VALID_MC_JSON, _VALID_CODING_JSON],
        validate_responses=[_validator_json(), _validator_json()],
    ):
        async with TestSessionFactory() as db:
            concept_db = (
                await db.execute(select(Concept).where(Concept.id == concept.id))
            ).scalar_one()
            result = await generate_questions_for_concept(db, concept_db)

    assert result.requested == 2
    assert result.validated_count == 2
    assert all(a.validated for a in result.attempts)

    async with TestSessionFactory() as db:
        rows = (await db.execute(select(Question))).scalars().all()
        assert len(rows) == 2
        assert {r.type for r in rows} == {"multiple_choice", "coding"}
        assert all(r.validated for r in rows)
        assert all(r.source == QuestionSource.GENERATED.value for r in rows)


@pytest.mark.asyncio
async def test_validation_failure_rolls_back_but_continues_next_question():
    """第 1 題 validate concept_fits=False（兩輪 retry 都 fail），第 2 題正常 → 只 1 列入庫。

    每題最多 2 次 retry（MAX_VALIDATE_RETRIES=2），所以第 1 題會耗掉 2 次 generate + 2 次 validate。
    """
    concept = await _seed_concept()
    with patched_pipeline(
        generate_responses=[
            _VALID_MC_JSON,  # 第 1 題 attempt 1 generate
            _VALID_MC_JSON,  # 第 1 題 attempt 2 generate
            _VALID_CODING_JSON,  # 第 2 題 generate
        ],
        validate_responses=[
            _validator_json(concept_fits=False),  # 第 1 題 attempt 1 validate fail
            _validator_json(concept_fits=False),  # 第 1 題 attempt 2 validate fail
            _validator_json(),  # 第 2 題 pass
        ],
    ):
        async with TestSessionFactory() as db:
            concept_db = (
                await db.execute(select(Concept).where(Concept.id == concept.id))
            ).scalar_one()
            result = await generate_questions_for_concept(db, concept_db)

    assert result.validated_count == 1
    assert result.attempts[0].validated is False
    assert result.attempts[0].error == "VALIDATION_RETRY_EXHAUSTED"
    assert result.attempts[1].validated is True

    async with TestSessionFactory() as db:
        rows = (await db.execute(select(Question))).scalars().all()
        assert len(rows) == 1
        assert rows[0].type == "coding"


@pytest.mark.asyncio
async def test_generate_llm_failure_does_not_block_next_question():
    """第 1 題 generate 拋例外（直接 abort，不 retry）→ 第 2 題正常 → 1 列入庫。

    與 orchestrator 同策略：generate 例外視為非 transient（如 LLM_PARSE_ERROR 多半是
    LLM 行為偏差，retry 通常仍失敗），不耗費額外呼叫。validate 失敗才 retry。
    """
    concept = await _seed_concept()
    with patched_pipeline(
        generate_responses=[
            "not json",  # 第 1 題 → LLM_PARSE_ERROR、直接 abort
            _VALID_CODING_JSON,  # 第 2 題
        ],
        validate_responses=[_validator_json()],  # 第 2 題 validate pass
    ):
        async with TestSessionFactory() as db:
            concept_db = (
                await db.execute(select(Concept).where(Concept.id == concept.id))
            ).scalar_one()
            result = await generate_questions_for_concept(db, concept_db)

    assert result.validated_count == 1
    assert result.attempts[0].validated is False
    assert "LLM_PARSE_ERROR" in (result.attempts[0].error or "")
    assert result.attempts[0].attempt_count == 1  # 沒 retry
    assert result.attempts[1].validated is True

    async with TestSessionFactory() as db:
        rows = (await db.execute(select(Question))).scalars().all()
        assert len(rows) == 1
        assert rows[0].type == "coding"


@pytest.mark.asyncio
async def test_no_video_order_raises_app_error():
    """concept 缺 video_order → 422 防呆，不嘗試出題。"""
    concept = await _seed_concept(video_order=None)
    with pytest.raises(AppError) as exc_info:
        async with TestSessionFactory() as db:
            concept_db = (
                await db.execute(select(Concept).where(Concept.id == concept.id))
            ).scalar_one()
            await generate_questions_for_concept(db, concept_db)
    assert exc_info.value.status_code == 422
    assert exc_info.value.error == "NO_VIDEO_ORDER"


# === generate_all：skip_existing / only ===


async def _seed_validated_question(concept_tag: str, qtype: str) -> None:
    async with TestSessionFactory() as db:
        db.add(
            Question(
                type=qtype,
                concept_tags=[concept_tag],
                bloom_level=3,
                difficulty=2,
                content={"stem": "x", "options": ["a", "b"], "answer_index": 0},
                explanation="",
                source=QuestionSource.GENERATED.value,
                validated=True,
            )
        )
        await db.commit()


@pytest.mark.asyncio
async def test_generate_all_skips_concept_with_enough_validated_questions():
    """已有 ≥ N validated 題的 concept → 直接跳過、不呼叫 LLM。"""
    concept = await _seed_concept(tag="cpp-04", video_order=4)
    await _seed_validated_question(concept.tag, "multiple_choice")
    await _seed_validated_question(concept.tag, "coding")

    # patched_pipeline 提供 0 個 generate response —— 若被呼叫即 raise StopIteration
    with patched_pipeline(generate_responses=[], validate_responses=[]):
        async with TestSessionFactory() as db:
            results = await generate_all(db, only=4, skip_existing=True)

    assert len(results) == 1
    assert results[0].error == "SKIPPED_HAS_ENOUGH"
    assert results[0].validated_count == 0  # 跳過 → 沒有 attempts


@pytest.mark.asyncio
async def test_generate_all_force_regenerates_even_with_existing():
    """skip_existing=False → 即使已有題仍重新生成。"""
    concept = await _seed_concept(tag="cpp-04", video_order=4)
    await _seed_validated_question(concept.tag, "multiple_choice")
    await _seed_validated_question(concept.tag, "coding")

    with patched_pipeline(
        generate_responses=[_VALID_MC_JSON, _VALID_CODING_JSON],
        validate_responses=[_validator_json(), _validator_json()],
    ):
        async with TestSessionFactory() as db:
            results = await generate_all(db, only=4, skip_existing=False)

    assert len(results) == 1
    assert results[0].error is None
    assert results[0].validated_count == 2


@pytest.mark.asyncio
async def test_generate_all_survives_rollback_expiring_other_concepts():
    """回歸測試（2026-07-06 實機批次炸 MissingGreenlet）：

    rollback 會讓 session 內「所有」concept expire，不只當前那顆；
    第 1 個 concept 的 validate 失敗回滾後，第 2 個 concept 的屬性存取
    必須仍可運作（generate_all 逐輪 refresh），不得觸發同步 lazy-load。
    """
    await _seed_concept(tag="cpp-04", video_order=4)
    await _seed_concept(tag="cpp-05", video_order=5)

    with patched_pipeline(
        generate_responses=[
            _VALID_MC_JSON,  # c4 MC attempt 1
            _VALID_MC_JSON,  # c4 MC attempt 2
            _VALID_CODING_JSON,  # c4 coding
            _VALID_MC_JSON,  # c5 MC
            _VALID_CODING_JSON,  # c5 coding
        ],
        validate_responses=[
            _validator_json(answer_correct=False),  # c4 MC fail → rollback（expire 全部）
            _validator_json(answer_correct=False),  # c4 MC fail → rollback
            _validator_json(),  # c4 coding pass
            _validator_json(),  # c5 MC pass
            _validator_json(),  # c5 coding pass
        ],
    ):
        async with TestSessionFactory() as db:
            results = await generate_all(db, skip_existing=True)

    assert len(results) == 2
    assert results[0].validated_count == 1  # MC 耗盡 retry、coding 過
    assert results[1].validated_count == 2


@pytest.mark.asyncio
async def test_list_target_concepts_filters_by_only():
    """only=N → 僅該 video_order；其餘 concept 排除。"""
    await _seed_concept(tag="cpp-04", video_order=4)
    await _seed_concept(tag="cpp-05", video_order=5)
    await _seed_concept(tag="cpp-orphan", video_order=None)  # 不應出現

    async with TestSessionFactory() as db:
        all_targets = await list_target_concepts(db)
        only_5 = await list_target_concepts(db, only=5)

    assert {c.tag for c in all_targets} == {"cpp-04", "cpp-05"}
    assert [c.tag for c in only_5] == ["cpp-05"]


@pytest.mark.asyncio
async def test_concept_batch_result_validated_count_property():
    """ConceptBatchResult.validated_count 屬性計算正確（無 DB）。"""
    from services.quiz.batch_generator import QuestionAttempt
    import uuid

    r = ConceptBatchResult(
        concept_id=uuid.uuid4(),
        concept_tag="tag",
        video_order=1,
        requested=3,
        attempts=[
            QuestionAttempt(question_type="multiple_choice", validated=True, attempt_count=1),
            QuestionAttempt(question_type="coding", validated=False, attempt_count=2),
            QuestionAttempt(question_type="fill_blank", validated=True, attempt_count=1),
        ],
    )
    assert r.validated_count == 2
