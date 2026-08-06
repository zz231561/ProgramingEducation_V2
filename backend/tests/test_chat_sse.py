"""`/chat/interact` SSE 串流測試（7-U6）。

驗三件事：階段事件依序推播、done 帶完整 InteractResponse、
管線途中失敗改發 error 事件（header 已送出無法改 HTTP status）。
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from core.errors import AppError
from services.edf.models import BloomLevel, ErrorType, EvidenceResult
from tests.helpers import encrypt_test_token

USER = {"sub": "sse-a", "email": "sse@ex.com", "name": "S", "googleId": "g-sse-a"}
_CK = {"authjs.session-token": encrypt_test_token(USER)}


def _evidence() -> EvidenceResult:
    return EvidenceResult(
        error_type=ErrorType.NONE,
        error_message="",
        concept_tags=["control-flow"],
        bloom_level=BloomLevel.APPLY,
        bloom_reasoning="r",
        code_analysis="a",
    )


def _parse_sse(text: str) -> list[tuple[str, dict]]:
    """SSE 原文 → [(event, data)]"""
    events: list[tuple[str, dict]] = []
    for block in text.strip().split("\n\n"):
        event, data = "message", None
        for line in block.splitlines():
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data = json.loads(line[5:].strip())
        if data is not None:
            events.append((event, data))
    return events


async def _post(client: AsyncClient) -> list[tuple[str, dict]]:
    resp = await client.post(
        "/chat/interact",
        json={"code": "int main(){}", "question": "怎麼寫迴圈"},
        cookies=_CK,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    return _parse_sse(resp.text)


@pytest.mark.asyncio
async def test_stream_emits_stages_then_done(client: AsyncClient):
    await client.get("/users/me", cookies=_CK)
    with (
        patch("services.chat.analyze_evidence", new=AsyncMock(return_value=_evidence())),
        patch("services.chat.generate_feedback", new=AsyncMock(return_value="回應內容")),
    ):
        events = await _post(client)

    kinds = [e for e, _ in events]
    assert kinds[-1] == "done"
    # 三個階段依管線順序推播，且都在 done 之前
    stages = [d["stage"] for e, d in events if e == "stage"]
    assert stages == ["analyzing", "retrieving", "composing"]

    _, payload = events[-1]
    assert payload["assistant_message"]["content"] == "回應內容"
    assert payload["user_message"]["content"] == "怎麼寫迴圈"
    assert payload["session_id"]


@pytest.mark.asyncio
async def test_stream_reports_pipeline_error_as_event(client: AsyncClient):
    """LLM 失敗時 header 已送出 → 必須以 error 事件回報，不能靜默結束。"""
    await client.get("/users/me", cookies=_CK)
    with (
        patch("services.chat.analyze_evidence", new=AsyncMock(return_value=_evidence())),
        patch(
            "services.chat.generate_feedback",
            new=AsyncMock(side_effect=AppError(502, "LLM_UNAVAILABLE", "AI 服務暫時不可用")),
        ),
    ):
        events = await _post(client)

    assert events[-1][0] == "error"
    assert events[-1][1]["error"] == "LLM_UNAVAILABLE"
    assert "done" not in [e for e, _ in events]


@pytest.mark.asyncio
async def test_unexpected_error_does_not_leak_details(client: AsyncClient):
    await client.get("/users/me", cookies=_CK)
    with (
        patch("services.chat.analyze_evidence", new=AsyncMock(return_value=_evidence())),
        patch(
            "services.chat.generate_feedback",
            new=AsyncMock(side_effect=RuntimeError("db password in message")),
        ),
    ):
        events = await _post(client)

    event, data = events[-1]
    assert event == "error"
    assert data["error"] == "INTERNAL_ERROR"
    assert "password" not in json.dumps(data)


@pytest.mark.asyncio
async def test_hint_request_logged_only_when_need_rises(client: AsyncClient):
    """7-C2a'：判準是 need，不是 reveal_level 也不是追問次數。

    2026-08-06 實測發現：用 reveal_level 當判準時，學生第一次貼出錯誤
    （base 已經是 2）就被記成求助，教師端的 hint 分布會全面灌水。
    """
    from sqlalchemy import select
    from models.coding_event import CodingEvent, CodingEventType
    from services.edf.models import ComprehensionSignal
    from tests.helpers import TestSessionFactory

    await client.get("/users/me", cookies=_CK)
    runtime = _evidence().model_copy(update={"error_type": ErrorType.RUNTIME})
    stuck = runtime.model_copy(
        update={"comprehension_signal": ComprehensionSignal.NOT_UNDERSTOOD}
    )

    async def _turn(evidence, question: str, session_id=None):
        with (
            patch("services.chat.analyze_evidence", new=AsyncMock(return_value=evidence)),
            patch("services.chat.generate_feedback", new=AsyncMock(return_value="回應內容")),
        ):
            resp = await client.post(
                "/chat/interact",
                json={"code": "int main(){}", "question": question, "session_id": session_id},
                cookies=_CK,
            )
        assert resp.status_code == 200
        return _parse_sse(resp.text)[-1][1]

    first = await _turn(runtime, "出現 Runtime Error 為什麼")  # need 0，不記
    await _turn(stuck, "我還是不懂", first["session_id"])       # need 1，記

    async with TestSessionFactory() as db:
        rows = (
            await db.execute(
                select(CodingEvent).where(
                    CodingEvent.event_type == CodingEventType.HINT_REQUEST.value
                )
            )
        ).scalars().all()
    assert len(rows) == 1, "第一輪（need 0）不該被記為 hint_request"
    assert rows[0].hint_level == 3  # runtime base 2 + need 1


@pytest.mark.asyncio
async def test_explicit_help_button_raises_reveal_level(client: AsyncClient):
    """7-C2a'：按「我卡住了」是唯一能直接推高揭露等級的前端輸入。

    同一句話、同一份證據，差別只在按鈕——沒按時 need 0，按了 +2。
    """
    from sqlalchemy import select
    from models.chat import ChatMessage
    from models.coding_event import CodingEvent, CodingEventType
    from tests.helpers import TestSessionFactory

    await client.get("/users/me", cookies=_CK)

    async def _ask(explicit: bool):
        with (
            patch("services.chat.analyze_evidence", new=AsyncMock(return_value=_evidence())),
            patch("services.chat.generate_feedback", new=AsyncMock(return_value="ok")),
        ):
            resp = await client.post(
                "/chat/interact",
                json={"code": "", "question": "這題怎麼開始", "explicit_help": explicit},
                cookies=_CK,
            )
        assert resp.status_code == 200
        return _parse_sse(resp.text)[-1][1]

    await _ask(False)
    await _ask(True)

    async with TestSessionFactory() as db:
        flagged = (
            await db.execute(
                select(ChatMessage).where(ChatMessage.explicit_help.is_(True))
            )
        ).scalars().all()
        events = (
            await db.execute(
                select(CodingEvent).where(
                    CodingEvent.event_type == CodingEventType.HINT_REQUEST.value
                )
            )
        ).scalars().all()

    assert len(flagged) == 1, "按鈕狀態必須隨學生訊息持久化，否則重放歷史會漏掉"
    # 沒按的那次 need 0 不記事件；按了的 need 2 → reveal = base(none) 0 + 2
    assert [e.hint_level for e in events] == [2]


@pytest.mark.asyncio
async def test_unauthenticated_still_returns_http_401(client: AsyncClient):
    """串流開始前的檢查仍走正常 HTTP status（不可被 SSE 吃掉）。"""
    resp = await client.post(
        "/chat/interact", json={"code": "", "question": "hi"}
    )
    assert resp.status_code == 401
