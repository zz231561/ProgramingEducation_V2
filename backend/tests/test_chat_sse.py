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
async def test_hint_request_only_logged_when_student_persists(client: AsyncClient):
    """7-C2a：第一次提問不算求助——base(error_type) 撐高的 reveal_level 不得觸發事件。

    2026-08-06 實測發現：改用 reveal_level 當判準時，學生第一次貼出錯誤就被記成
    hint_request，教師端的 hint 分布會全面灌水。
    """
    from sqlalchemy import select
    from models.coding_event import CodingEvent, CodingEventType
    from tests.helpers import TestSessionFactory

    await client.get("/users/me", cookies=_CK)
    runtime_evidence = _evidence().model_copy(update={"error_type": ErrorType.RUNTIME})
    with (
        patch("services.chat.analyze_evidence", new=AsyncMock(return_value=runtime_evidence)),
        patch("services.chat.generate_feedback", new=AsyncMock(return_value="回應內容")),
    ):
        first = await _post(client)
        assert first[-1][0] == "done"  # reveal_level = base 2，但 persistence = 0
        # 同一 session 追問 → persistence 1（換 session 就等於換脈絡，不算追問）
        resp = await client.post(
            "/chat/interact",
            json={
                "code": "int main(){}",
                "question": "那要改哪裡",
                "session_id": first[-1][1]["session_id"],
            },
            cookies=_CK,
        )
        assert resp.status_code == 200

    async with TestSessionFactory() as db:
        rows = (
            await db.execute(
                select(CodingEvent).where(
                    CodingEvent.event_type == CodingEventType.HINT_REQUEST.value
                )
            )
        ).scalars().all()
    assert len(rows) == 1, "只有第二輪（真的在追問）該被記為 hint_request"
    assert rows[0].hint_level == 3  # runtime base 2 + persistence 1


@pytest.mark.asyncio
async def test_unauthenticated_still_returns_http_401(client: AsyncClient):
    """串流開始前的檢查仍走正常 HTTP status（不可被 SSE 吃掉）。"""
    resp = await client.post(
        "/chat/interact", json={"code": "", "question": "hi"}
    )
    assert resp.status_code == 401
