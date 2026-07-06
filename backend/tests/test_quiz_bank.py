"""Phase 6-3b：題庫抽題 service 單元測試。

涵蓋：
- 有 validated 題 + 對應 tag → 隨機回 1 題
- 無 validated 題 → None
- validated=False 的題不被抽中
- 不同 concept_tag 不串題
- exclude_question_ids 過濾
- U2d：question_type 過濾 + exclude_answered_by 排除已答過
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from models.concept import Concept
from models.quiz import Question, QuestionSource, StudentAnswer
from models.user import User
from services.quiz.bank import (
    list_unit_question_set,
    pick_random_validated_question,
)
from tests.helpers import TestSessionFactory


def _make_question(
    concept_tags: list[str],
    validated: bool,
    qtype: str = "multiple_choice",
    source: str = QuestionSource.GENERATED.value,
) -> Question:
    return Question(
        type=qtype,
        concept_tags=concept_tags,
        bloom_level=3,
        difficulty=2,
        content={"stem": "x", "options": ["a", "b"], "answer_index": 0},
        explanation="",
        source=source,
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


# === U2d：question_type 過濾 + 重複曝光防護 ===


@pytest.mark.asyncio
async def test_question_type_filter():
    """指定 question_type 只抽該題型；無該題型 → None。"""
    async with TestSessionFactory() as db:
        db.add(_make_question(["syntax-basic"], validated=True, qtype="multiple_choice"))
        await db.commit()

    async with TestSessionFactory() as db:
        assert (
            await pick_random_validated_question(
                db, "syntax-basic", question_type="coding"
            )
        ) is None
        q = await pick_random_validated_question(
            db, "syntax-basic", question_type="multiple_choice"
        )
        assert q is not None
        assert q.type == "multiple_choice"


@pytest.mark.asyncio
async def test_exclude_answered_by_filters_answered_questions():
    """已答過的題不再抽中；未答過的其他學生不受影響。"""
    async with TestSessionFactory() as db:
        user_a = User(google_id=f"g-{uuid.uuid4()}", email="a@bank.test", name="A")
        user_b = User(google_id=f"g-{uuid.uuid4()}", email="b@bank.test", name="B")
        question = _make_question(["syntax-basic"], validated=True)
        db.add_all([user_a, user_b, question])
        await db.flush()
        db.add(
            StudentAnswer(
                user_id=user_a.id,
                question_id=question.id,
                answer={"selected_index": 0},
                is_correct=True,
            )
        )
        await db.commit()
        user_a_id, user_b_id = user_a.id, user_b.id

    async with TestSessionFactory() as db:
        # A 已答過唯一一題 → None（caller fallback 現生）
        assert (
            await pick_random_validated_question(
                db, "syntax-basic", exclude_answered_by=user_a_id
            )
        ) is None
        # B 沒答過 → 正常抽中
        q = await pick_random_validated_question(
            db, "syntax-basic", exclude_answered_by=user_b_id
        )
        assert q is not None


# === list_unit_question_set（6-3c LEARN 單元題組）===


@pytest.mark.asyncio
async def test_unit_set_only_lists_batch_source():
    """LEARN 題組只列 source='batch'；QUIZ 弱項現生題（generated）不列入。"""
    async with TestSessionFactory() as db:
        user = User(google_id=f"g-{uuid.uuid4()}", email="s@set.test", name="S")
        db.add(user)
        db.add(_make_question(["syntax-basic"], validated=True,
                              source=QuestionSource.BATCH.value))
        db.add(_make_question(["syntax-basic"], validated=True,
                              source=QuestionSource.GENERATED.value))
        await db.flush()
        uid = user.id
        await db.commit()

    async with TestSessionFactory() as db:
        items = await list_unit_question_set(db, "syntax-basic", answered_by=uid)
        assert len(items) == 1
        assert items[0].question.source == QuestionSource.BATCH.value


@pytest.mark.asyncio
async def test_unit_set_reports_answered_status():
    """已答過的題標 is_answered=True 並帶最後一次對錯；未答為 False。"""
    async with TestSessionFactory() as db:
        user = User(google_id=f"g-{uuid.uuid4()}", email="s2@set.test", name="S2")
        answered = _make_question(["syntax-basic"], validated=True,
                                  source=QuestionSource.BATCH.value)
        unanswered = _make_question(["syntax-basic"], validated=True,
                                    source=QuestionSource.BATCH.value)
        db.add_all([user, answered, unanswered])
        await db.flush()
        db.add(
            StudentAnswer(
                user_id=user.id,
                question_id=answered.id,
                answer={"selected_index": 0},
                is_correct=True,
            )
        )
        uid, answered_id = user.id, answered.id
        await db.commit()

    async with TestSessionFactory() as db:
        items = await list_unit_question_set(db, "syntax-basic", answered_by=uid)
        by_id = {it.question.id: it for it in items}
        assert by_id[answered_id].is_answered is True
        assert by_id[answered_id].is_correct is True
        other = next(it for qid, it in by_id.items() if qid != answered_id)
        assert other.is_answered is False


@pytest.mark.asyncio
async def test_unit_set_filters_by_question_type():
    """question_type 過濾：只回該題型（LEARN 觀念題 tab 只要 MC）。"""
    async with TestSessionFactory() as db:
        user = User(google_id=f"g-{uuid.uuid4()}", email="s3@set.test", name="S3")
        db.add(user)
        db.add(_make_question(["syntax-basic"], validated=True,
                              qtype="multiple_choice", source=QuestionSource.BATCH.value))
        db.add(_make_question(["syntax-basic"], validated=True,
                              qtype="coding", source=QuestionSource.BATCH.value))
        await db.flush()
        uid = user.id
        await db.commit()

    async with TestSessionFactory() as db:
        items = await list_unit_question_set(
            db, "syntax-basic", answered_by=uid, question_type="multiple_choice"
        )
        assert len(items) == 1
        assert items[0].question.type == "multiple_choice"
