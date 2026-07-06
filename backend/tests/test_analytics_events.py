"""行為事件 logging service 測試（5-2b）— 分類 + 寫入 + /code/execute 掛鉤。"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from models.coding_event import CodingEvent, CodingEventType
from models.user import User
from services.analytics import classify_execution, log_execution
from services.judge0 import ExecutionResult
from tests.helpers import TestSessionFactory, encrypt_test_token

USER = {
    "sub": "coder-1",
    "email": "coder@example.com",
    "name": "Coder",
    "googleId": "g-coder-1",
}
_COOKIE = "authjs.session-token"


def _cookies() -> dict:
    return {_COOKIE: encrypt_test_token(USER)}


async def _user_id(client: AsyncClient) -> uuid.UUID:
    await client.get("/users/me", cookies=_cookies())
    async with TestSessionFactory() as db:
        u = (
            await db.execute(select(User).where(User.email == USER["email"]))
        ).scalar_one()
        return u.id


async def _events(user_id: uuid.UUID) -> list[CodingEvent]:
    async with TestSessionFactory() as db:
        return list(
            (
                await db.execute(
                    select(CodingEvent).where(CodingEvent.user_id == user_id)
                )
            ).scalars()
        )


# === classify_execution 單元 ===

def test_classify_compile_error():
    r = ExecutionResult(
        compile_output="error: expected ';'", status_description="Compilation Error"
    )
    assert classify_execution(r) == CodingEventType.COMPILE_ERROR


def test_classify_success():
    r = ExecutionResult(status_description="Accepted", exit_code=0)
    assert classify_execution(r) == CodingEventType.SUCCESS


def test_classify_runtime_error():
    r = ExecutionResult(status_description="Runtime Error (SIGSEGV)")
    assert classify_execution(r) == CodingEventType.RUNTIME_ERROR


# === log_execution 寫入 ===

async def test_log_execution_writes_row(client: AsyncClient):
    uid = await _user_id(client)
    async with TestSessionFactory() as db:
        await log_execution(
            db,
            user_id=uid,
            result=ExecutionResult(status_description="Accepted", exit_code=0),
            code="int main(){}",
        )
    rows = await _events(uid)
    assert len(rows) == 1
    assert rows[0].event_type == "success"
    assert rows[0].code_snapshot == "int main(){}"
    assert rows[0].execution_result["status"] == "Accepted"


# === /code/execute 掛鉤 ===

async def test_execute_route_logs_event(client: AsyncClient):
    uid = await _user_id(client)
    fake = ExecutionResult(status_description="Accepted", exit_code=0, stdout="hi")
    with patch(
        "api.routes.code.submit_and_poll", new=AsyncMock(return_value=fake)
    ):
        resp = await client.post(
            "/code/execute", json={"code": "int main(){}"}, cookies=_cookies()
        )
    assert resp.status_code == 200
    rows = await _events(uid)
    assert len(rows) == 1
    assert rows[0].event_type == "success"


async def test_execute_route_logs_compile_error(client: AsyncClient):
    uid = await _user_id(client)
    fake = ExecutionResult(
        compile_output="error", status_description="Compilation Error"
    )
    with patch(
        "api.routes.code.submit_and_poll", new=AsyncMock(return_value=fake)
    ):
        await client.post(
            "/code/execute", json={"code": "bad"}, cookies=_cookies()
        )
    rows = await _events(uid)
    assert len(rows) == 1
    assert rows[0].event_type == "compile_error"
