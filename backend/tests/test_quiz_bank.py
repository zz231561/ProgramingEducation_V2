"""Phase 6-3b：題庫抽題 service 單元測試。

涵蓋：
- 有 validated 題 + 對應 tag → 隨機回 1 題
- 無 validated 題 → None
- validated=False 的題不被抽中
- 不同 concept_tag 不串題
- exclude_question_ids 過濾
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from models.concept import Concept
from models.quiz import Question, QuestionSource
from services.quiz.bank import pick_random_validated_question
from tests.helpers import TestSessionFactory


def _make_question(
    concept_tags: list[str],
    validated: bool,
    qtype: str = "multiple_choice",
) -> Question:
    return Question(
        type=qtype,
        concept_tags=concept_tags,
        bloom_level=3,
        difficulty=2,
        content={"stem": "x", "options": ["a", "b"], "answer_index": 0},
        explanation="",
        source=QuestionSource.GENERATED.value,
        validated=validated,
    )


@pytest.mark.asyncio
async def test_returns_question_when_validated_exists():
    """有 1 個 validated + 該 tag 的題 → 必然抽中。"""
    async with TestSessionFactory() as db:
        db.add(_make_question(["syntax-basic"], validated=True))
        await db.commit()

    async with TestSessionFactory() as db:
        q = await pick_random_validated_question(db, "syntax-basic")
        assert q is not None
        assert q.validated is True
        assert "syntax-basic" in q.concept_tags


@pytest.mark.asyncio
async def test_returns_none_when_bank_empty():
    """完全沒題 → None。"""
    async with TestSessionFactory() as db:
        q = await pick_random_validated_question(db, "syntax-basic")
        assert q is None


@pytest.mark.asyncio
async def test_unvalidated_question_not_selected():
    """validated=False 的題不應被抽中。"""
    async with TestSessionFactory() as db:
        db.add(_make_question(["syntax-basic"], validated=False))
        db.add(_make_question(["syntax-basic"], validated=False))
        await db.commit()

    async with TestSessionFactory() as db:
        q = await pick_random_validated_question(db, "syntax-basic")
        assert q is None


@pytest.mark.asyncio
async def test_different_concept_tag_not_returned():
    """validated 題存在但不同 tag → None。"""
    async with TestSessionFactory() as db:
        db.add(_make_question(["control-flow"], validated=True))
        await db.commit()

    async with TestSessionFactory() as db:
        q = await pick_random_validated_question(db, "syntax-basic")
        assert q is None


@pytest.mark.asyncio
async def test_exclude_question_ids_filters_out():
    """exclude_question_ids 中的 question.id 不應被抽中（單題 + 排除 → None）。"""
    async with TestSessionFactory() as db:
        only_question = _make_question(["syntax-basic"], validated=True)
        db.add(only_question)
        await db.commit()
        await db.refresh(only_question)
        excluded_id = only_question.id

    async with TestSessionFactory() as db:
        q = await pick_random_validated_question(
            db, "syntax-basic", exclude_question_ids=[excluded_id]
        )
        assert q is None


@pytest.mark.asyncio
async def test_multiple_validated_questions_all_eligible():
    """多題均 validated + 同 tag → 抽中的必是 validated + tag 符合（n 次抽都符合條件）。"""
    async with TestSessionFactory() as db:
        for _ in range(5):
            db.add(_make_question(["syntax-basic"], validated=True))
        # 干擾項：不同 tag / unvalidated
        db.add(_make_question(["control-flow"], validated=True))
        db.add(_make_question(["syntax-basic"], validated=False))
        await db.commit()

    async with TestSessionFactory() as db:
        for _ in range(10):
            q = await pick_random_validated_question(db, "syntax-basic")
            assert q is not None
            assert q.validated is True
            assert "syntax-basic" in q.concept_tags

    # 確認干擾項在 DB 仍存在但不影響結果
    async with TestSessionFactory() as db:
        all_rows = (await db.execute(select(Question))).scalars().all()
        assert len(all_rows) == 7
