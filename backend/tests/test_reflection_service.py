"""Reflection service 單元測試（roadmap 2-5a）— DB CRUD 與權限/驗證流程。"""

import uuid

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
from tests.helpers import TestSessionFactory


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
