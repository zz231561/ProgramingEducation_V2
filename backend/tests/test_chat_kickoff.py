"""Coddy 反思開場測試 — POST /chat/reflection-kickoff。"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from models.reflection import Reflection, ReflectionSourceType
from models.user import User
from services import chat_kickoff
from services.chat_kickoff import _FALLBACK_MESSAGE, _followup_instruction
from tests.helpers import TestSessionFactory, encrypt_test_token

USER_A = {"sub": "ck-a", "email": "cka@ex.com", "name": "A", "googleId": "g-ck-a"}
USER_B = {"sub": "ck-b", "email": "ckb@ex.com", "name": "B", "googleId": "g-ck-b"}
_COOKIE = "authjs.session-token"


def _ck(p: dict) -> dict:
    return {_COOKIE: encrypt_test_token(p)}


async def _make_reflection(client: AsyncClient, payload: dict) -> str:
    """註冊使用者並直接插入一筆反思，回傳 reflection id。"""
    ck = _ck(payload)
    await client.get("/users/me", cookies=ck)
    async with TestSessionFactory() as db:
        user = (
            await db.execute(select(User).where(User.email == payload["email"]))
        ).scalar_one()
        r = Reflection(
            user_id=user.id,
            source_type=ReflectionSourceType.QUIZ.value,
            source_id=uuid.uuid4(),
            problem_understanding="要印出比大小的結果",
            planned_steps=["讀入兩個數", "用 if 比較", "印出結果"],
            expected_concepts="if 判斷",
            followup_question="你會怎麼處理相等的情況？",
        )
        db.add(r)
        await db.commit()
        return str(r.id)


def _mock_llm(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value=resp)
    return client


async def test_kickoff_creates_session_with_opening(client: AsyncClient):
    rid = await _make_reflection(client, USER_A)
    with patch.object(
        chat_kickoff, "_get_client", return_value=_mock_llm("你的計畫很清楚！")
    ):
        resp = await client.post(
            "/chat/reflection-kickoff",
            json={"reflection_id": rid},
            cookies=_ck(USER_A),
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["assistant_message"]["content"] == "你的計畫很清楚！"
    assert body["assistant_message"]["role"] == "assistant"
    # session 已持久化，可透過歷史 API 讀回
    detail = await client.get(
        f"/chat/sessions/{body['session_id']}", cookies=_ck(USER_A)
    )
    assert detail.status_code == 200
    assert detail.json()["messages"][0]["content"] == "你的計畫很清楚！"


async def test_kickoff_llm_failure_falls_back(client: AsyncClient):
    rid = await _make_reflection(client, USER_A)
    broken = AsyncMock()
    broken.chat.completions.create = AsyncMock(side_effect=RuntimeError("down"))
    with patch.object(chat_kickoff, "_get_client", return_value=broken):
        resp = await client.post(
            "/chat/reflection-kickoff",
            json={"reflection_id": rid},
            cookies=_ck(USER_A),
        )
    assert resp.status_code == 200
    assert resp.json()["assistant_message"]["content"] == _FALLBACK_MESSAGE


async def test_kickoff_other_users_reflection_404(client: AsyncClient):
    rid = await _make_reflection(client, USER_A)
    ck_b = _ck(USER_B)
    await client.get("/users/me", cookies=ck_b)
    resp = await client.post(
        "/chat/reflection-kickoff", json={"reflection_id": rid}, cookies=ck_b
    )
    assert resp.status_code == 404


def test_followup_instruction_branches():
    """追問狀態決定開場指示：未回應→接手；已回應→不重複；無追問→挑模糊處。"""
    r = MagicMock(followup_question="Q?", followup_answer=None)
    assert "尚未回應" in _followup_instruction(r)
    r = MagicMock(followup_question="Q?", followup_answer="A")
    assert "不要重複" in _followup_instruction(r)
    r = MagicMock(followup_question=None, followup_answer=None)
    assert "最模糊" in _followup_instruction(r)
