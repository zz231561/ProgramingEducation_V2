"""對話行為分類測試（5-2c）— classify_dialogue_act 啟發式 + interact 寫入。"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from models.chat import ChatMessage, DialogueAct, MessageRole
from models.user import User
from services.analytics import classify_dialogue_act
from tests.helpers import TestSessionFactory, encrypt_test_token

USER = {
    "sub": "chatter-1",
    "email": "chatter@example.com",
    "name": "Chatter",
    "googleId": "g-chatter-1",
}
_COOKIE = "authjs.session-token"


def _cookies() -> dict:
    return {_COOKIE: encrypt_test_token(USER)}


# === classify_dialogue_act 單元 ===

def test_empty_returns_none():
    assert classify_dialogue_act("   ") is None


def test_hint_level_wins():
    # 明確 hint 請求優先於文字內容
    assert classify_dialogue_act("這樣對嗎", hint_level=2) == DialogueAct.ASKING_HINT.value


def test_acknowledgment_short():
    assert classify_dialogue_act("謝謝！") == DialogueAct.ACKNOWLEDGMENT.value
    assert classify_dialogue_act("ok got it") == DialogueAct.ACKNOWLEDGMENT.value


def test_acknowledgment_ignored_when_long():
    # 長句含致謝詞但非單純致謝 → 不判 acknowledgment
    assert (
        classify_dialogue_act("謝謝你，可是我想知道為什麼要用指標")
        == DialogueAct.CLARIFICATION_REQUEST.value
    )


def test_verification():
    assert classify_dialogue_act("我這樣寫對嗎") == DialogueAct.VERIFICATION.value


def test_debugging_from_execution_error():
    act = classify_dialogue_act(
        "跑不出來", execution_result={"stderr": "segmentation fault"}
    )
    assert act == DialogueAct.DEBUGGING.value


def test_asking_hint_from_text():
    assert classify_dialogue_act("我卡住了幫我一下") == DialogueAct.ASKING_HINT.value


def test_clarification_request():
    assert (
        classify_dialogue_act("什麼是 pointer") == DialogueAct.CLARIFICATION_REQUEST.value
    )


def test_unknown_returns_none():
    assert classify_dialogue_act("aaa bbb ccc") is None


def test_verification_beats_execution_error():
    # 求證意圖優先於除錯（即使附帶執行錯誤）
    act = classify_dialogue_act(
        "這樣寫對嗎", execution_result={"compile_output": "error"}
    )
    assert act == DialogueAct.VERIFICATION.value


# === interact 寫入 dialogue_act ===

async def test_interact_persists_dialogue_act(client: AsyncClient):
    from unittest.mock import AsyncMock, patch

    await client.get("/users/me", cookies=_cookies())

    with patch(
        "services.chat.generate_feedback",
        new=AsyncMock(return_value="AI 回應"),
    ):
        resp = await client.post(
            "/chat/interact",
            json={"code": "int main(){}", "question": "什麼是指標", "hint_level": 0},
            cookies=_cookies(),
        )
    assert resp.status_code == 200

    async with TestSessionFactory() as db:
        u = (
            await db.execute(select(User).where(User.email == USER["email"]))
        ).scalar_one()
        msgs = (
            await db.execute(
                select(ChatMessage).where(ChatMessage.role == MessageRole.USER)
            )
        ).scalars().all()
        user_msgs = [m for m in msgs]
    assert user_msgs, "應有 user 訊息"
    assert user_msgs[-1].dialogue_act == DialogueAct.CLARIFICATION_REQUEST.value
