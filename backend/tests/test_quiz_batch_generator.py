"""6-3c 測試：知識點驅動 quiz batch generator + scripts.generate_unit_questions。

涵蓋：
- per-concept：每知識點 1 題 MC + 1 題 coding（非 intro）全 validated → 入庫 source='batch'
- 題量 = 萃取的知識點數；content 記錄 knowledge_point
- 課程介紹 concept → 不生 coding
- validate 失敗 → 該題 rollback、不阻擋同 concept 下一題
- generate 例外（LLM_PARSE_ERROR）→ 該題 fail、不影響下一題
- NO_VIDEO_ORDER concept → 422 防呆
- skip_existing：已有 batch MC 題組 + validated coding → 跳過（requested=0）
- 知識點萃取失敗 → concept-level error
- rollback expire 其他 concept 的 MissingGreenlet 回歸
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


def _points_json(points: list[str]) -> str:
    return json.dumps({"points": points})


def _validator_json(
    answer_correct: bool = True,
    concept_fits: bool = True,
    bloom_appropriate: bool = True,
    point_meaningful: bool = True,
) -> str:
    return json.dumps({
        "answer_correct": answer_correct,
        "answer_reason": "ok",
        "concept_fits": concept_fits,
        "concept_reason": "ok",
        "bloom_appropriate": bloom_appropriate,
        "bloom_reason": "ok",
        "point_meaningful": point_meaningful,
        "point_reason": "ok",
    })


@contextmanager
def patched_pipeline(
    generate_responses: list[str | Exception],
    validate_responses: list[str | Exception],
    points: list[str] | Exception | None = None,
):
    """Patch 知識點萃取 + generate + validate 三個 LLM client，以及 RAG retrieve。

    points: 知識點萃取回傳（None → 預設 1 個知識點）；Exception → 萃取失敗。
    generate_responses / validate_responses 依呼叫順序逐筆消費。
    """
    kp_client = AsyncMock()
    if isinstance(points, Exception):
        kp_client.chat.completions.create = AsyncMock(side_effect=points)
    else:
        pts = points if points is not None else ["知識點一"]
        kp_client.chat.completions.create = AsyncMock(
            return_value=_mock_completion(_points_json(pts))
        )

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
        patch("services.quiz.knowledge_points._get_client", return_value=kp_client),
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
        patch(
            "services.quiz.batch_generator.get_chunks_by_video_order",
            AsyncMock(return_value=[]),
        ),
    ):
        yield


# === Concept seeding ===


async def _seed_concept(
    tag: str = "syntax-basic",
    video_order: int | None = 4,
    category: str = "基礎",
) -> Concept:
    async with TestSessionFactory() as db:
        c = Concept(
            tag=tag,
            name_zh="語法基礎",
            name_en="Syntax Basics",
            description="C++ 基本語法、變數宣告、輸出。",
            difficulty_level=2,
            category=category,
            video_order=video_order,
        )
        db.add(c)
        await db.commit()
        await db.refresh(c)
        return c


# === per-concept 路徑 ===


@pytest.mark.asyncio
async def test_one_point_one_mc_plus_coding_persist():
    """1 知識點 → 1 MC + 1 coding 全過 → 入庫 2 列、source='batch'、MC 記 knowledge_point。"""
    concept = await _seed_concept()
    with patched_pipeline(
        points=["變數宣告需先宣告再使用"],
        generate_responses=[_VALID_MC_JSON, _VALID_CODING_JSON],
        validate_responses=[_validator_json(), _validator_json()],
    ):
        async with TestSessionFactory() as db:
            concept_db = (
                await db.execute(select(Concept).where(Concept.id == concept.id))
            ).scalar_one()
            result = await generate_questions_for_concept(db, concept_db)

    assert result.requested == 2  # 1 point + 1 coding
    assert result.validated_count == 2

    async with TestSessionFactory() as db:
        rows = (await db.execute(select(Question))).scalars().all()
        assert len(rows) == 2
        assert {r.type for r in rows} == {"multiple_choice", "coding"}
        assert all(r.source == QuestionSource.BATCH.value for r in rows)
        mc = next(r for r in rows if r.type == "multiple_choice")
        assert mc.content.get("knowledge_point") == "變數宣告需先宣告再使用"


@pytest.mark.asyncio
async def test_question_count_follows_knowledge_points():
    """3 個知識點 → 3 題 MC + 1 coding。"""
    concept = await _seed_concept()
    with patched_pipeline(
        points=["點一", "點二", "點三"],
        generate_responses=[_VALID_MC_JSON] * 3 + [_VALID_CODING_JSON],
        validate_responses=[_validator_json()] * 4,
    ):
        async with TestSessionFactory() as db:
            concept_db = (
                await db.execute(select(Concept).where(Concept.id == concept.id))
            ).scalar_one()
            result = await generate_questions_for_concept(db, concept_db)

    assert result.requested == 4
    assert result.validated_count == 4
    async with TestSessionFactory() as db:
        mc = (
            await db.execute(
                select(Question).where(Question.type == "multiple_choice")
            )
        ).scalars().all()
        assert len(mc) == 3


@pytest.mark.asyncio
async def test_intro_category_skips_coding():
    """課程介紹 concept → 只生 MC，不生 coding。"""
    concept = await _seed_concept(tag="cpp-01", video_order=1, category="課程介紹")
    with patched_pipeline(
        points=["點一"],
        generate_responses=[_VALID_MC_JSON],
        validate_responses=[_validator_json()],
    ):
        async with TestSessionFactory() as db:
            concept_db = (
                await db.execute(select(Concept).where(Concept.id == concept.id))
            ).scalar_one()
            result = await generate_questions_for_concept(db, concept_db)

    assert result.requested == 1
    async with TestSessionFactory() as db:
        rows = (await db.execute(select(Question))).scalars().all()
        assert len(rows) == 1
        assert rows[0].type == "multiple_choice"


@pytest.mark.asyncio
async def test_point_meaningful_false_rejects_question():
    """審查 point_meaningful=False（考操作細節）→ 該題不入庫。"""
    concept = await _seed_concept()
    with patched_pipeline(
        points=["點一"],
        generate_responses=[_VALID_MC_JSON, _VALID_MC_JSON, _VALID_CODING_JSON],
        validate_responses=[
            _validator_json(point_meaningful=False),  # MC attempt 1 fail
            _validator_json(point_meaningful=False),  # MC attempt 2 fail
            _validator_json(),  # coding pass
        ],
    ):
        async with TestSessionFactory() as db:
            concept_db = (
                await db.execute(select(Concept).where(Concept.id == concept.id))
            ).scalar_one()
            result = await generate_questions_for_concept(db, concept_db)

    assert result.validated_count == 1  # 只有 coding 過
    assert result.attempts[0].validated is False
    assert "考點無意義" in "; ".join(result.attempts[0].issues)


@pytest.mark.asyncio
async def test_validation_failure_rolls_back_but_continues():
    """MC validate concept_fits=False（兩輪 retry 都 fail）→ coding 正常 → 只 1 列入庫。"""
    concept = await _seed_concept()
    with patched_pipeline(
        points=["點一"],
        generate_responses=[_VALID_MC_JSON, _VALID_MC_JSON, _VALID_CODING_JSON],
        validate_responses=[
            _validator_json(concept_fits=False),
            _validator_json(concept_fits=False),
            _validator_json(),
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
async def test_generate_llm_failure_does_not_block_next():
    """MC generate 拋例外（直接 abort，不 retry）→ coding 正常 → 1 列入庫。"""
    concept = await _seed_concept()
    with patched_pipeline(
        points=["點一"],
        generate_responses=["not json", _VALID_CODING_JSON],
        validate_responses=[_validator_json()],
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


@pytest.mark.asyncio
async def test_knowledge_points_failure_is_concept_error():
    """知識點萃取失敗 → concept-level error，不出題。"""
    concept = await _seed_concept()
    with patched_pipeline(
        points=RuntimeError("network down"),
        generate_responses=[],
        validate_responses=[],
    ):
        async with TestSessionFactory() as db:
            concept_db = (
                await db.execute(select(Concept).where(Concept.id == concept.id))
            ).scalar_one()
            result = await generate_questions_for_concept(db, concept_db)

    assert result.error is not None
    assert "KNOWLEDGE_POINTS_FAILED" in result.error
    assert result.validated_count == 0


@pytest.mark.asyncio
async def test_no_video_order_raises_app_error():
    """concept 缺 video_order → 422 防呆。"""
    concept = await _seed_concept(video_order=None)
    with pytest.raises(AppError) as exc_info:
        async with TestSessionFactory() as db:
            concept_db = (
                await db.execute(select(Concept).where(Concept.id == concept.id))
            ).scalar_one()
            await generate_questions_for_concept(db, concept_db)
    assert exc_info.value.status_code == 422
    assert exc_info.value.error == "NO_VIDEO_ORDER"


# === skip_existing / generate_all ===


async def _seed_validated_question(
    concept_tag: str, qtype: str, source: str = QuestionSource.BATCH.value
) -> None:
    async with TestSessionFactory() as db:
        db.add(
            Question(
                type=qtype,
                concept_tags=[concept_tag],
                bloom_level=3,
                difficulty=2,
                content={"stem": "x", "options": ["a", "b"], "answer_index": 0},
                explanation="",
                source=source,
                validated=True,
            )
        )
        await db.commit()


@pytest.mark.asyncio
async def test_generate_all_skips_concept_with_batch_set():
    """已有 batch MC + validated coding → 跳過（requested=0，不呼叫 LLM）。"""
    concept = await _seed_concept(tag="cpp-04", video_order=4)
    await _seed_validated_question(concept.tag, "multiple_choice")
    await _seed_validated_question(concept.tag, "coding")

    with patched_pipeline(generate_responses=[], validate_responses=[]):
        async with TestSessionFactory() as db:
            results = await generate_all(db, only=4, skip_existing=True)

    assert len(results) == 1
    assert results[0].requested == 0
    assert results[0].error is None
    assert results[0].validated_count == 0


@pytest.mark.asyncio
async def test_generate_all_force_regenerates_even_with_existing():
    """skip_existing=False → 即使已有題仍重新生成。"""
    concept = await _seed_concept(tag="cpp-04", video_order=4)
    await _seed_validated_question(concept.tag, "multiple_choice")
    await _seed_validated_question(concept.tag, "coding")

    with patched_pipeline(
        points=["點一"],
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
    """回歸（實機批次炸 MissingGreenlet）：rollback expire 全部 concept，
    下一輪 concept 屬性存取須仍可運作（逐輪 refresh）。"""
    await _seed_concept(tag="cpp-04", video_order=4)
    await _seed_concept(tag="cpp-05", video_order=5)

    with patched_pipeline(
        points=["點一"],
        generate_responses=[
            _VALID_MC_JSON,  # c4 MC attempt 1
            _VALID_MC_JSON,  # c4 MC attempt 2
            _VALID_CODING_JSON,  # c4 coding
            _VALID_MC_JSON,  # c5 MC
            _VALID_CODING_JSON,  # c5 coding
        ],
        validate_responses=[
            _validator_json(answer_correct=False),  # c4 MC fail → rollback
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
    await _seed_concept(tag="cpp-04", video_order=4)
    await _seed_concept(tag="cpp-05", video_order=5)
    await _seed_concept(tag="cpp-orphan", video_order=None)

    async with TestSessionFactory() as db:
        all_targets = await list_target_concepts(db)
        only_5 = await list_target_concepts(db, only=5)

    assert {c.tag for c in all_targets} == {"cpp-04", "cpp-05"}
    assert [c.tag for c in only_5] == ["cpp-05"]


@pytest.mark.asyncio
async def test_concept_batch_result_validated_count_property():
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
            QuestionAttempt(question_type="multiple_choice", validated=True, attempt_count=1),
        ],
    )
    assert r.validated_count == 2
