"""Mastery hook unit tests（roadmap 2-6e）。

涵蓋：passed=True/False/None 三種；update_mastery 異常時 swallow。
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from models.quiz import Question
from services.comprehension.mastery_hook import apply_comprehension_mastery
from services.edf.models import ErrorType


def _make_question() -> Question:
    return Question(
        type="coding",
        concept_tags=["control-flow", "arrays-strings"],
        bloom_level=3,
        difficulty=2,
        content={"stem": "x"},
        explanation="",
        source="generated",
        validated=True,
    )


@pytest.mark.asyncio
async def test_passed_true_updates_with_error_type_none():
    update = AsyncMock()
    with patch("services.comprehension.mastery_hook.update_mastery", new=update):
        await apply_comprehension_mastery(
            db=AsyncMock(), user_id=uuid4(), question=_make_question(), passed=True
        )
    update.assert_awaited_once()
    evidence = update.await_args.args[2]
    assert evidence.error_type == ErrorType.NONE
    assert evidence.concept_tags == ["control-flow", "arrays-strings"]
    assert int(evidence.bloom_level) == 3


@pytest.mark.asyncio
async def test_passed_false_updates_with_error_type_logic():
    update = AsyncMock()
    with patch("services.comprehension.mastery_hook.update_mastery", new=update):
        await apply_comprehension_mastery(
            db=AsyncMock(), user_id=uuid4(), question=_make_question(), passed=False
        )
    update.assert_awaited_once()
    evidence = update.await_args.args[2]
    assert evidence.error_type == ErrorType.LOGIC


@pytest.mark.asyncio
async def test_passed_none_no_op():
    """passed=None（評分失敗 fallback）→ 不該呼叫 update_mastery。"""
    update = AsyncMock()
    with patch("services.comprehension.mastery_hook.update_mastery", new=update):
        await apply_comprehension_mastery(
            db=AsyncMock(), user_id=uuid4(), question=_make_question(), passed=None
        )
    update.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_mastery_exception_swallowed():
    """update_mastery 內部失敗不應 propagate（best-effort）。"""
    update = AsyncMock(side_effect=RuntimeError("DB down"))
    with patch("services.comprehension.mastery_hook.update_mastery", new=update):
        # 不該 raise
        await apply_comprehension_mastery(
            db=AsyncMock(), user_id=uuid4(), question=_make_question(), passed=True
        )
