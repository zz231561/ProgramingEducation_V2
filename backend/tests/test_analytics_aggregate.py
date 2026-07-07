"""行為指標聚合 service 測試（5-2d）— aggregate_user_behavior。"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from models.chat import ChatMessage, ChatSession, DialogueAct, MessageRole
from models.coding_event import CodingEvent, CodingEventType
from models.user import User
from services.analytics import aggregate_user_behavior
from tests.helpers import TestSessionFactory, encrypt_test_token

USER = {
    "sub": "agg-1",
    "email": "agg@example.com",
    "name": "Agg",
    "googleId": "g-agg-1",
}
_COOKIE = "authjs.session-token"
_T0 = datetime(2026, 7, 7, 10, 0, 0, tzinfo=timezone.utc)


async def _make_user(client: AsyncClient) -> uuid.UUID:
    await client.get("/users/me", cookies={_COOKIE: encrypt_test_token(USER)})
    async with TestSessionFactory() as db:
        return (
            await db.execute(select(User).where(User.email == USER["email"]))
        ).scalar_one().id


def _exec_event(uid: uuid.UUID, kind: CodingEventType, offset_s: int) -> CodingEvent:
    return CodingEvent(
        user_id=uid,
        event_type=kind.value,
        created_at=_T0 + timedelta(seconds=offset_s),
    )


async def test_empty_user_zero_metrics(client: AsyncClient):
    uid = await _make_user(client)
    async with TestSessionFactory() as db:
        m = await aggregate_user_behavior(db, uid)
    assert m.execution_count == 0
    assert m.success_rate == 0.0
    assert m.avg_fix_duration_seconds is None
    assert m.hint_distribution == {}
    assert m.dialogue_act_distribution == {}


async def test_execution_and_success_rate(client: AsyncClient):
    uid = await _make_user(client)
    async with TestSessionFactory() as db:
        db.add_all(
            [
                _exec_event(uid, CodingEventType.COMPILE_ERROR, 0),
                _exec_event(uid, CodingEventType.RUNTIME_ERROR, 10),
                _exec_event(uid, CodingEventType.SUCCESS, 30),
                _exec_event(uid, CodingEventType.SUCCESS, 40),
            ]
        )
        await db.commit()
        m = await aggregate_user_behavior(db, uid)
    assert m.execution_count == 4
    assert m.success_count == 2
    assert m.success_rate == 0.5


async def test_fix_duration_pairs_error_to_next_success(client: AsyncClient):
    uid = await _make_user(client)
    async with TestSessionFactory() as db:
        # 錯誤@0 → 錯誤@10（仍 pending，取首個）→ 成功@30 ⇒ 30 秒
        # 之後 錯誤@60 → 成功@100 ⇒ 40 秒；平均 (30+40)/2 = 35
        db.add_all(
            [
                _exec_event(uid, CodingEventType.COMPILE_ERROR, 0),
                _exec_event(uid, CodingEventType.COMPILE_ERROR, 10),
                _exec_event(uid, CodingEventType.SUCCESS, 30),
                _exec_event(uid, CodingEventType.RUNTIME_ERROR, 60),
                _exec_event(uid, CodingEventType.SUCCESS, 100),
            ]
        )
        await db.commit()
        m = await aggregate_user_behavior(db, uid)
    assert m.avg_fix_duration_seconds == 35.0


async def test_success_without_prior_error_no_duration(client: AsyncClient):
    uid = await _make_user(client)
    async with TestSessionFactory() as db:
        db.add(_exec_event(uid, CodingEventType.SUCCESS, 0))
        await db.commit()
        m = await aggregate_user_behavior(db, uid)
    assert m.avg_fix_duration_seconds is None


async def test_hint_distribution(client: AsyncClient):
    uid = await _make_user(client)
    async with TestSessionFactory() as db:
        db.add_all(
            [
                CodingEvent(
                    user_id=uid,
                    event_type=CodingEventType.HINT_REQUEST.value,
                    hint_level=1,
                ),
                CodingEvent(
                    user_id=uid,
                    event_type=CodingEventType.HINT_REQUEST.value,
                    hint_level=1,
                ),
                CodingEvent(
                    user_id=uid,
                    event_type=CodingEventType.HINT_REQUEST.value,
                    hint_level=3,
                ),
            ]
        )
        await db.commit()
        m = await aggregate_user_behavior(db, uid)
    assert m.hint_request_count == 3
    assert m.hint_distribution == {"1": 2, "3": 1}


async def test_dialogue_act_distribution(client: AsyncClient):
    uid = await _make_user(client)
    async with TestSessionFactory() as db:
        session = ChatSession(user_id=uid)
        db.add(session)
        await db.flush()
        db.add_all(
            [
                ChatMessage(
                    session_id=session.id,
                    role=MessageRole.USER,
                    content="什麼是指標",
                    dialogue_act=DialogueAct.CLARIFICATION_REQUEST.value,
                ),
                ChatMessage(
                    session_id=session.id,
                    role=MessageRole.USER,
                    content="卡住了",
                    dialogue_act=DialogueAct.ASKING_HINT.value,
                ),
                ChatMessage(
                    session_id=session.id,
                    role=MessageRole.USER,
                    content="謝謝",
                    dialogue_act=DialogueAct.CLARIFICATION_REQUEST.value,
                ),
                # 未分類（NULL）不計入
                ChatMessage(
                    session_id=session.id,
                    role=MessageRole.USER,
                    content="aaa",
                    dialogue_act=None,
                ),
                # assistant 訊息本就無 dialogue_act
                ChatMessage(
                    session_id=session.id,
                    role=MessageRole.ASSISTANT,
                    content="AI 回應",
                ),
            ]
        )
        await db.commit()
        m = await aggregate_user_behavior(db, uid)
    assert m.dialogue_act_distribution == {"clarification_request": 2, "asking_hint": 1}


async def test_time_window_filter(client: AsyncClient):
    uid = await _make_user(client)
    async with TestSessionFactory() as db:
        db.add_all(
            [
                _exec_event(uid, CodingEventType.SUCCESS, 0),
                _exec_event(uid, CodingEventType.SUCCESS, 3600),
            ]
        )
        await db.commit()
        m = await aggregate_user_behavior(
            db, uid, since=_T0 + timedelta(seconds=1)
        )
    assert m.execution_count == 1
