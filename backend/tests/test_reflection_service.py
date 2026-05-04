"""Reflection service 單元測試（roadmap 2-5a + 2-5b）— DB CRUD + LLM 評分整合。"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from core.errors import AppError
from models.quiz import Question
from models.reflection import Reflection, ReflectionSourceType
from services.reflection import (
    ReflectionUpdate,
    create_reflection,
    get_reflection,
    update_reflection,
)
from services.reflection.evaluate import ReflectionEvaluation
from tests.helpers import TestSessionFactory


def _eval(quality: float | None = None, followup: str | None = None) -> ReflectionEvaluation:
    return ReflectionEvaluation(
        quality_score=quality,
        understanding_score=quality,
        plan_quality_score=quality,
        concept_recall_score=quality,
        followup_question=followup,
    )


@pytest.fixture(autouse=True)
def _mock_evaluate():
    """預設 mock evaluate_reflection 為 fallback（quality_score=None），避免測試打 OpenAI。

    需要驗證評分行為的測試自己用 `with patch(...)` overlay 此 fixture。
    """
    with patch(
        "services.reflection.crud.evaluate_reflection",
        new=AsyncMock(return_value=_eval()),
    ) as m:
        yield m


async def _seed_question() -> Question:
    async with TestSessionFactory() as db:
        q = Question(
            type="multiple_choice",
            concept_tags=["syntax-basic"],
            bloom_level=3,
            difficulty=1,
            content={"stem": "...", "options": ["a", "b"], "answer_index": 0},
            explanation="",
            source="generated",
            validated=True,
        )
        db.add(q)
        await db.commit()
        await db.refresh(q)
        return q


# === create ===


async def test_create_reflection_persists_with_defaults():
    question = await _seed_question()
    user_id = uuid.uuid4()

    async with TestSessionFactory() as db:
        reflection = await create_reflection(
            db,
            user_id=user_id,
            source_type=ReflectionSourceType.QUIZ,
            source_id=question.id,
            problem_understanding="要判斷整數宣告語法",
            planned_steps=["看選項", "比對 C++ 語法"],
            expected_concepts="syntax-basic",
        )
        assert reflection.id is not None
        assert reflection.source_type == "quiz"
        assert reflection.planned_steps == ["看選項", "比對 C++ 語法"]
        assert reflection.is_modified is False
        assert reflection.quality_score is None
        assert reflection.followup_question is None


async def test_create_reflection_quiz_source_not_found_raises_404():
    user_id = uuid.uuid4()
    fake_question_id = uuid.uuid4()

    async with TestSessionFactory() as db:
        with pytest.raises(AppError) as exc:
            await create_reflection(
                db,
                user_id=user_id,
                source_type=ReflectionSourceType.QUIZ,
                source_id=fake_question_id,
                problem_understanding="",
                planned_steps=[],
                expected_concepts="",
            )
    assert exc.value.status_code == 404
    assert exc.value.error == "REFLECTION_SOURCE_NOT_FOUND"


async def test_create_reflection_learning_unit_skips_source_check():
    """learning_units 表尚未建立，learning_unit 來源不擋。"""
    user_id = uuid.uuid4()

    async with TestSessionFactory() as db:
        reflection = await create_reflection(
            db,
            user_id=user_id,
            source_type=ReflectionSourceType.LEARNING_UNIT,
            source_id=uuid.uuid4(),
            problem_understanding="",
            planned_steps=["step"],
            expected_concepts="",
        )
        assert reflection.source_type == "learning_unit"


async def test_create_reflection_duplicate_returns_409():
    question = await _seed_question()
    user_id = uuid.uuid4()

    async with TestSessionFactory() as db:
        await create_reflection(
            db,
            user_id=user_id,
            source_type=ReflectionSourceType.QUIZ,
            source_id=question.id,
            problem_understanding="一次",
            planned_steps=["a"],
            expected_concepts="",
        )

    async with TestSessionFactory() as db:
        with pytest.raises(AppError) as exc:
            await create_reflection(
                db,
                user_id=user_id,
                source_type=ReflectionSourceType.QUIZ,
                source_id=question.id,
                problem_understanding="二次",
                planned_steps=["b"],
                expected_concepts="",
            )
    assert exc.value.status_code == 409
    assert exc.value.error == "REFLECTION_ALREADY_EXISTS"


# === get ===


async def test_get_reflection_by_owner():
    question = await _seed_question()
    user_id = uuid.uuid4()

    async with TestSessionFactory() as db:
        created = await create_reflection(
            db,
            user_id=user_id,
            source_type=ReflectionSourceType.QUIZ,
            source_id=question.id,
            problem_understanding="X",
            planned_steps=[],
            expected_concepts="",
        )

    async with TestSessionFactory() as db:
        fetched = await get_reflection(db, created.id, user_id)
        assert fetched.id == created.id


async def test_get_reflection_other_user_returns_404():
    """權限隔離：他人的反思不可見（且不洩漏存在性）。"""
    question = await _seed_question()
    owner = uuid.uuid4()
    intruder = uuid.uuid4()

    async with TestSessionFactory() as db:
        created = await create_reflection(
            db,
            user_id=owner,
            source_type=ReflectionSourceType.QUIZ,
            source_id=question.id,
            problem_understanding="",
            planned_steps=[],
            expected_concepts="",
        )

    async with TestSessionFactory() as db:
        with pytest.raises(AppError) as exc:
            await get_reflection(db, created.id, intruder)
    assert exc.value.status_code == 404


# === update ===


async def test_update_reflection_marks_modified_and_changes_fields():
    question = await _seed_question()
    user_id = uuid.uuid4()

    async with TestSessionFactory() as db:
        created = await create_reflection(
            db,
            user_id=user_id,
            source_type=ReflectionSourceType.QUIZ,
            source_id=question.id,
            problem_understanding="原",
            planned_steps=["a"],
            expected_concepts="",
        )
        original_updated_at = created.updated_at

    async with TestSessionFactory() as db:
        updated = await update_reflection(
            db,
            reflection_id=created.id,
            user_id=user_id,
            payload=ReflectionUpdate(
                planned_steps=["a", "b"],
                followup_answer="補充：再想一次",
            ),
        )
        assert updated.planned_steps == ["a", "b"]
        assert updated.followup_answer == "補充：再想一次"
        assert updated.is_modified is True
        assert updated.updated_at >= original_updated_at


async def test_update_reflection_no_change_keeps_is_modified_false():
    """payload 全空 → 不該標 modified。"""
    question = await _seed_question()
    user_id = uuid.uuid4()

    async with TestSessionFactory() as db:
        created = await create_reflection(
            db,
            user_id=user_id,
            source_type=ReflectionSourceType.QUIZ,
            source_id=question.id,
            problem_understanding="",
            planned_steps=[],
            expected_concepts="",
        )

    async with TestSessionFactory() as db:
        updated = await update_reflection(
            db,
            reflection_id=created.id,
            user_id=user_id,
            payload=ReflectionUpdate(),
        )
        assert updated.is_modified is False


async def test_update_reflection_other_user_returns_404():
    question = await _seed_question()
    owner = uuid.uuid4()
    intruder = uuid.uuid4()

    async with TestSessionFactory() as db:
        created = await create_reflection(
            db,
            user_id=owner,
            source_type=ReflectionSourceType.QUIZ,
            source_id=question.id,
            problem_understanding="",
            planned_steps=[],
            expected_concepts="",
        )

    async with TestSessionFactory() as db:
        with pytest.raises(AppError) as exc:
            await update_reflection(
                db,
                reflection_id=created.id,
                user_id=intruder,
                payload=ReflectionUpdate(planned_steps=["x"]),
            )
    assert exc.value.status_code == 404


# === 2-5b LLM evaluation 整合 ===


async def test_create_persists_high_quality_score_no_followup():
    """高分 → quality_score 寫入、followup_question 為 None。"""
    question = await _seed_question()
    user_id = uuid.uuid4()

    with patch(
        "services.reflection.crud.evaluate_reflection",
        new=AsyncMock(return_value=_eval(quality=0.85, followup=None)),
    ):
        async with TestSessionFactory() as db:
            reflection = await create_reflection(
                db,
                user_id=user_id,
                source_type=ReflectionSourceType.QUIZ,
                source_id=question.id,
                problem_understanding="判斷 C++ 整數宣告語法",
                planned_steps=["看 4 個選項", "對照 C++ type-name 順序"],
                expected_concepts="syntax-basic",
            )
    assert reflection.quality_score == 0.85
    assert reflection.followup_question is None


async def test_create_persists_low_quality_with_followup():
    """低分 → quality_score 寫入、followup_question 寫入供 UI 提示。"""
    question = await _seed_question()
    user_id = uuid.uuid4()

    with patch(
        "services.reflection.crud.evaluate_reflection",
        new=AsyncMock(return_value=_eval(quality=0.3, followup="你能更具體列出步驟嗎？")),
    ):
        async with TestSessionFactory() as db:
            reflection = await create_reflection(
                db,
                user_id=user_id,
                source_type=ReflectionSourceType.QUIZ,
                source_id=question.id,
                problem_understanding="不知道",
                planned_steps=["想想看"],
                expected_concepts="",
            )
    assert reflection.quality_score == 0.3
    assert reflection.followup_question == "你能更具體列出步驟嗎？"


async def test_create_llm_unavailable_falls_back_to_none():
    """LLM 不可用 → quality_score=None；反思仍寫入（不擋學生流程）。"""
    question = await _seed_question()
    user_id = uuid.uuid4()

    # 預設 fixture 已是 fallback，這裡直接驗證
    async with TestSessionFactory() as db:
        reflection = await create_reflection(
            db,
            user_id=user_id,
            source_type=ReflectionSourceType.QUIZ,
            source_id=question.id,
            problem_understanding="X",
            planned_steps=[],
            expected_concepts="",
        )
    assert reflection.id is not None
    assert reflection.quality_score is None
    assert reflection.followup_question is None


async def test_update_re_evaluates_after_followup_answer():
    """補充 followup_answer → 重新 LLM 評分；quality 提升 → followup 清除。"""
    question = await _seed_question()
    user_id = uuid.uuid4()

    # 第一次：低分有追問
    with patch(
        "services.reflection.crud.evaluate_reflection",
        new=AsyncMock(return_value=_eval(quality=0.3, followup="說明步驟")),
    ):
        async with TestSessionFactory() as db:
            created = await create_reflection(
                db,
                user_id=user_id,
                source_type=ReflectionSourceType.QUIZ,
                source_id=question.id,
                problem_understanding="略",
                planned_steps=["想"],
                expected_concepts="",
            )
            assert created.quality_score == 0.3
            assert created.followup_question == "說明步驟"

    # 補充答覆後：高分清空 followup
    with patch(
        "services.reflection.crud.evaluate_reflection",
        new=AsyncMock(return_value=_eval(quality=0.8, followup=None)),
    ):
        async with TestSessionFactory() as db:
            updated = await update_reflection(
                db,
                reflection_id=created.id,
                user_id=user_id,
                payload=ReflectionUpdate(
                    followup_answer="1. 看選項 2. 對照 C++ 語法 3. 選 int x;"
                ),
            )
    assert updated.quality_score == 0.8
    assert updated.followup_question is None
    assert updated.is_modified is True


async def test_update_no_op_does_not_call_evaluate():
    """payload 全空 PATCH → 不呼叫 evaluate（避免無謂 LLM call）。"""
    question = await _seed_question()
    user_id = uuid.uuid4()

    async with TestSessionFactory() as db:
        created = await create_reflection(
            db,
            user_id=user_id,
            source_type=ReflectionSourceType.QUIZ,
            source_id=question.id,
            problem_understanding="",
            planned_steps=[],
            expected_concepts="",
        )

    eval_mock = AsyncMock(return_value=_eval(quality=0.9))
    with patch("services.reflection.crud.evaluate_reflection", new=eval_mock):
        async with TestSessionFactory() as db:
            await update_reflection(
                db,
                reflection_id=created.id,
                user_id=user_id,
                payload=ReflectionUpdate(),
            )
    eval_mock.assert_not_called()
