"""`/code/execute` 的 stdin 傳遞測試（2026-08-05）。

背景：後端一直支援 stdin，但前端從未送出、也沒有輸入介面，學生寫 `cin` 就卡住。
補上 UI 的同時鎖住這條契約，避免日後又被漏掉。
"""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from services.judge0 import ExecutionResult
from tests.helpers import encrypt_test_token

USER = {"sub": "ex-a", "email": "ex@ex.com", "name": "A", "googleId": "g-ex-a"}
_CK = {"authjs.session-token": encrypt_test_token(USER)}


async def test_stdin_is_forwarded_to_judge0(client: AsyncClient):
    fake = ExecutionResult(status_description="Accepted", exit_code=0, stdout="hi Alice")
    with patch(
        "api.routes.code.submit_and_poll", new=AsyncMock(return_value=fake)
    ) as submit:
        resp = await client.post(
            "/code/execute",
            json={"code": "int main(){}", "stdin": "Alice\n25"},
            cookies=_CK,
        )
    assert resp.status_code == 200
    assert submit.await_args.kwargs["stdin"] == "Alice\n25"


async def test_stdin_defaults_to_empty(client: AsyncClient):
    fake = ExecutionResult(status_description="Accepted", exit_code=0)
    with patch(
        "api.routes.code.submit_and_poll", new=AsyncMock(return_value=fake)
    ) as submit:
        await client.post(
            "/code/execute", json={"code": "int main(){}"}, cookies=_CK
        )
    assert submit.await_args.kwargs["stdin"] == ""


async def test_language_cannot_be_overridden(client: AsyncClient):
    """本平台只教 C++：前端就算送 language_id 也不採用（A3）。"""
    fake = ExecutionResult(status_description="Accepted", exit_code=0)
    with patch(
        "api.routes.code.submit_and_poll", new=AsyncMock(return_value=fake)
    ) as submit:
        resp = await client.post(
            "/code/execute",
            json={"code": "print(1)", "language_id": 71},  # 71 = Python
            cookies=_CK,
        )
    assert resp.status_code == 200
    assert submit.await_args.kwargs["language_id"] == 54  # C++ (GCC 9.2.0)


async def test_command_line_arguments_forwarded(client: AsyncClient):
    """章節 58 main 參數：args 要傳到 Judge0 的 command_line_arguments。"""
    fake = ExecutionResult(status_description="Accepted", exit_code=0)
    with patch(
        "api.routes.code.submit_and_poll", new=AsyncMock(return_value=fake)
    ) as submit:
        await client.post(
            "/code/execute",
            json={"code": "int main(){}", "args": "hello world"},
            cookies=_CK,
        )
    assert submit.await_args.kwargs["command_line_arguments"] == "hello world"
