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
