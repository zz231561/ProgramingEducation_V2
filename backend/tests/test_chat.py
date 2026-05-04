"""Chat service 單元測試 — mock EDF pipeline 驗證互動流程。"""

import uuid
import pytest
from unittest.mock import AsyncMock, patch

from sqlalchemy import select

from models.chat import ChatSession, ChatMessage, MessageRole
from services.edf.models import EvidenceResult, BloomLevel, ErrorType
from services.edf.decision import TeachingStrategy
from tests.helpers import TestSessionFactory


def _mock_evidence() -> EvidenceResult:
    return EvidenceResult(
        error_type=ErrorType.LOGIC,
        error_message="infinite loop",
        concept_tags=["control-flow"],
        bloom_level=BloomLevel.APPLY,
        bloom_reasoning="applying loops",
        code_analysis="while condition never false",
    )


@pytest.mark.asyncio
async def test_interact_creates_session_and_messages():
    """interact 建立 session + user/assistant 訊息。"""
    from services.chat import interact

    user_id = uuid.uuid4()

    with (
        patch("services.chat.analyze_evidence", new_callable=AsyncMock, return_value=_mock_evidence()),
        patch("services.chat.generate_feedback", new_callable=AsyncMock, return_value="試試看追蹤變數 i 的值？"),
    ):
        async with TestSessionFactory() as db:
            session, user_msg, ai_msg = await interact(
                db=db,
                user_id=user_id,
                code="while(true){}",
                question="為什麼跑不停？",
            )

            assert session.id is not None
            assert session.title == "為什麼跑不停？"
            assert user_msg.role == MessageRole.USER
            assert ai_msg.role == MessageRole.ASSISTANT
            assert "追蹤" in ai_msg.content


@pytest.mark.asyncio
async def test_interact_reuses_existing_session():
    """傳入 session_id 時復用既有 session。"""
    from services.chat import interact

    user_id = uuid.uuid4()

    with (
        patch("services.chat.analyze_evidence", new_callable=AsyncMock, return_value=_mock_evidence()),
        patch("services.chat.generate_feedback", new_callable=AsyncMock, return_value="回應1"),
    ):
        async with TestSessionFactory() as db:
            session1, _, _ = await interact(db=db, user_id=user_id, code="a", question="q1")
            sid = session1.id

    with (
        patch("services.chat.analyze_evidence", new_callable=AsyncMock, return_value=_mock_evidence()),
        patch("services.chat.generate_feedback", new_callable=AsyncMock, return_value="回應2"),
    ):
        async with TestSessionFactory() as db:
            session2, _, _ = await interact(
                db=db, user_id=user_id, code="b", question="q2", session_id=sid,
            )
            assert session2.id == sid


@pytest.mark.asyncio
async def test_list_sessions():
    """list_sessions 回傳使用者的 session。"""
    from services.chat import interact, list_sessions

    user_id = uuid.uuid4()

    with (
        patch("services.chat.analyze_evidence", new_callable=AsyncMock, return_value=_mock_evidence()),
        patch("services.chat.generate_feedback", new_callable=AsyncMock, return_value="ok"),
    ):
        async with TestSessionFactory() as db:
            await interact(db=db, user_id=user_id, code="a", question="q1")
            await interact(db=db, user_id=user_id, code="b", question="q2")

        async with TestSessionFactory() as db:
            sessions, total = await list_sessions(db, user_id)
            assert total == 2
            assert len(sessions) == 2


@pytest.mark.asyncio
async def test_delete_session():
    """delete_session 刪除 session + cascade 刪除訊息。"""
    from services.chat import interact, delete_session

    user_id = uuid.uuid4()

    with (
        patch("services.chat.analyze_evidence", new_callable=AsyncMock, return_value=_mock_evidence()),
        patch("services.chat.generate_feedback", new_callable=AsyncMock, return_value="ok"),
    ):
        async with TestSessionFactory() as db:
            session, _, _ = await interact(db=db, user_id=user_id, code="a", question="q")
            sid = session.id

        async with TestSessionFactory() as db:
            result = await delete_session(db, user_id, sid)
            assert result is True

        async with TestSessionFactory() as db:
            result = await delete_session(db, user_id, sid)
            assert result is False


# === Phase 2-5e — reflection_id 注入 EDF Pipeline ===


async def _seed_reflection(user_id: uuid.UUID, planned_steps: list[str]) -> uuid.UUID:
    """直接寫入 reflection 資料表，跳過 LLM 評分。"""
    from models.quiz import Question
    from models.reflection import Reflection, ReflectionSourceType

    async with TestSessionFactory() as db:
        q = Question(
            type="multiple_choice",
            concept_tags=["control-flow"],
            bloom_level=3,
            difficulty=1,
            content={"stem": "...", "options": ["a"], "answer_index": 0},
            explanation="",
            source="generated",
            validated=True,
        )
        db.add(q)
        await db.flush()
        r = Reflection(
            user_id=user_id,
            source_type=ReflectionSourceType.QUIZ.value,
            source_id=q.id,
            problem_understanding="判斷無窮迴圈",
            planned_steps=planned_steps,
            expected_concepts="control-flow",
            quality_score=0.8,
        )
        db.add(r)
        await db.commit()
        await db.refresh(r)
        return r.id


@pytest.mark.asyncio
async def test_interact_injects_reflection_into_evidence_and_feedback():
    """傳 reflection_id → analyze_evidence + generate_feedback 都收到反思摘要。"""
    from services.chat import interact

    user_id = uuid.uuid4()
    rid = await _seed_reflection(user_id, ["先觀察迴圈條件", "確認變數有更新"])

    evidence_mock = AsyncMock(return_value=_mock_evidence())
    feedback_mock = AsyncMock(return_value="你前面說要觀察迴圈條件，找到了嗎？")

    with (
        patch("services.chat.analyze_evidence", evidence_mock),
        patch("services.chat.generate_feedback", feedback_mock),
    ):
        async with TestSessionFactory() as db:
            await interact(
                db=db,
                user_id=user_id,
                code="while(true){}",
                question="跑不停",
                reflection_id=rid,
            )

    # Evidence 收到簡短版反思摘要
    ev_kwargs = evidence_mock.call_args
    summary_arg = ev_kwargs.args[4] if len(ev_kwargs.args) >= 5 else ev_kwargs.kwargs.get("reflection_summary", "")
    assert "先觀察迴圈條件" in summary_arg
    assert "control-flow" in summary_arg

    # Feedback 收到詳細版反思 block（含品質分數 + 蘇格拉底引導）
    fb_block = feedback_mock.call_args.kwargs["reflection_block"]
    assert "判斷無窮迴圈" in fb_block
    assert "蘇格拉底式提問" in fb_block
    assert "80%" in fb_block


@pytest.mark.asyncio
async def test_interact_without_reflection_id_passes_empty_block():
    """未傳 reflection_id → 兩層都收到空字串（不阻擋 EDF 流程）。"""
    from services.chat import interact

    evidence_mock = AsyncMock(return_value=_mock_evidence())
    feedback_mock = AsyncMock(return_value="ok")

    with (
        patch("services.chat.analyze_evidence", evidence_mock),
        patch("services.chat.generate_feedback", feedback_mock),
    ):
        async with TestSessionFactory() as db:
            await interact(db=db, user_id=uuid.uuid4(), code="a", question="q")

    summary_arg = evidence_mock.call_args.args[4] if len(evidence_mock.call_args.args) >= 5 else ""
    assert summary_arg == ""
    assert feedback_mock.call_args.kwargs["reflection_block"] == ""


@pytest.mark.asyncio
async def test_interact_other_users_reflection_is_ignored():
    """權限隔離：其他使用者的 reflection_id 不可注入到本人 prompt。"""
    from services.chat import interact

    other_user = uuid.uuid4()
    rid = await _seed_reflection(other_user, ["other 的計畫"])

    evidence_mock = AsyncMock(return_value=_mock_evidence())
    feedback_mock = AsyncMock(return_value="ok")

    with (
        patch("services.chat.analyze_evidence", evidence_mock),
        patch("services.chat.generate_feedback", feedback_mock),
    ):
        async with TestSessionFactory() as db:
            await interact(
                db=db,
                user_id=uuid.uuid4(),  # 不同 user
                code="a",
                question="q",
                reflection_id=rid,
            )

    fb_block = feedback_mock.call_args.kwargs["reflection_block"]
    assert "other 的計畫" not in fb_block
    assert fb_block == ""


@pytest.mark.asyncio
async def test_interact_unknown_reflection_id_does_not_block():
    """傳不存在的 reflection_id → fallback 為空字串，教學流程不擋。"""
    from services.chat import interact

    evidence_mock = AsyncMock(return_value=_mock_evidence())
    feedback_mock = AsyncMock(return_value="ok")

    with (
        patch("services.chat.analyze_evidence", evidence_mock),
        patch("services.chat.generate_feedback", feedback_mock),
    ):
        async with TestSessionFactory() as db:
            session, _, _ = await interact(
                db=db,
                user_id=uuid.uuid4(),
                code="a",
                question="q",
                reflection_id=uuid.uuid4(),
            )
    assert session.id is not None
    assert feedback_mock.call_args.kwargs["reflection_block"] == ""
