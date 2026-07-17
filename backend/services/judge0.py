"""Judge0 API client — 提交程式碼並 polling 取得執行結果。"""

import asyncio
import base64

import httpx
from pydantic import BaseModel

from core.config import settings
from core.errors import AppError

# Judge0 C++ (GCC 9.2.0) language id
CPP_LANGUAGE_ID = 54

# polling 參數
_POLL_INTERVAL = 0.8  # 秒
_MAX_POLLS = 15  # 最多等待 12 秒


class ExecutionResult(BaseModel):
    """Judge0 執行結果。"""

    stdout: str = ""
    stderr: str = ""
    compile_output: str = ""
    exit_code: int | None = None
    time: str | None = None
    memory: int | None = None
    status_description: str = ""


def _decode_b64(value: str | None) -> str:
    """解碼 Judge0 base64 編碼的輸出。"""
    if not value:
        return ""
    try:
        return base64.b64decode(value).decode("utf-8", errors="replace")
    except Exception:
        return value


def _resolve_auth_mode() -> str:
    """決定 authn 模式：JUDGE0_AUTH_MODE 顯式優先，否則依 URL 自動判斷。"""
    if settings.JUDGE0_AUTH_MODE:
        return settings.JUDGE0_AUTH_MODE
    return "rapidapi" if "rapidapi" in settings.JUDGE0_API_URL else "self-hosted"


def _build_headers() -> dict[str, str]:
    """根據設定建立 Judge0 request headers。

    RapidAPI 模式帶 X-RapidAPI-Key；自架模式（開 authn token 時）帶 X-Auth-Token；
    無 key 則不帶任何 auth header（自架未開 authn）。
    """
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if settings.JUDGE0_API_KEY:
        if _resolve_auth_mode() == "rapidapi":
            headers["X-RapidAPI-Key"] = settings.JUDGE0_API_KEY
            headers["X-RapidAPI-Host"] = "judge0-ce.p.rapidapi.com"
        else:
            headers["X-Auth-Token"] = settings.JUDGE0_API_KEY
    return headers


async def submit_and_poll(
    source_code: str,
    stdin: str = "",
    language_id: int = CPP_LANGUAGE_ID,
) -> ExecutionResult:
    """提交程式碼至 Judge0 並 polling 直到執行完成。

    Flow: POST /submissions → token → GET /submissions/{token} polling
    """
    base_url = settings.JUDGE0_API_URL.rstrip("/")
    headers = _build_headers()

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Step 1: 提交
        # 網路層例外（連線失敗 / timeout）須轉 503，不可冒泡成 500 誤導為內部錯誤
        try:
            submit_resp = await client.post(
                f"{base_url}/submissions",
                headers=headers,
                params={"base64_encoded": "true", "wait": "false"},
                json={
                    "source_code": base64.b64encode(source_code.encode()).decode(),
                    "language_id": language_id,
                    "stdin": base64.b64encode(stdin.encode()).decode() if stdin else "",
                },
            )
        except httpx.HTTPError as e:
            raise AppError(
                503, "JUDGE0_UNAVAILABLE", "執行服務暫時不可用，請稍後再試"
            ) from e

        if submit_resp.status_code != 201:
            _handle_submit_error(submit_resp)

        token = submit_resp.json().get("token")
        if not token:
            raise AppError(502, "JUDGE0_ERROR", "Judge0 未回傳 submission token")

        # Step 2: Polling
        for _ in range(_MAX_POLLS):
            await asyncio.sleep(_POLL_INTERVAL)

            # polling 途中的暫時性網路錯誤視同該輪失敗，留給下一輪重試
            try:
                poll_resp = await client.get(
                    f"{base_url}/submissions/{token}",
                    headers=headers,
                    params={"base64_encoded": "true", "fields": "stdout,stderr,compile_output,exit_code,time,memory,status"},
                )
            except httpx.HTTPError:
                continue

            if poll_resp.status_code != 200:
                continue

            data = poll_resp.json()
            status_id = data.get("status", {}).get("id", 0)

            # status 1=In Queue, 2=Processing — 繼續等
            if status_id <= 2:
                continue

            return ExecutionResult(
                stdout=_decode_b64(data.get("stdout")),
                stderr=_decode_b64(data.get("stderr")),
                compile_output=_decode_b64(data.get("compile_output")),
                exit_code=data.get("exit_code"),
                time=data.get("time"),
                memory=data.get("memory"),
                status_description=data.get("status", {}).get("description", ""),
            )

        # polling 逾時
        raise AppError(504, "EXECUTION_TIMEOUT", "編譯/執行逾時，請縮短程式或減少迴圈次數")


def _handle_submit_error(resp: httpx.Response) -> None:
    """處理 Judge0 submit 失敗。"""
    if resp.status_code == 429:
        raise AppError(429, "RATE_LIMITED", "執行服務已達使用上限，請稍後再試")
    if resp.status_code >= 500:
        raise AppError(503, "JUDGE0_UNAVAILABLE", "執行服務暫時不可用，請稍後再試")
    raise AppError(502, "JUDGE0_ERROR", f"Judge0 錯誤 ({resp.status_code})")
