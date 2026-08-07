"""執行引擎 dispatcher — 自建 runner 主路徑 + Judge0 fallback（7-R R2）。

介面與 `services.judge0.submit_and_poll` 完全相同，呼叫端只需換 import。
路由規則：
- `RUNNER_BACKEND=judge0` → 強制走 Judge0（B 機故障時的手動降級開關）
- `RUNNER_URL` 未設定 → 自動退 Judge0（R5 部署前的過渡保護，生產不會斷）
- 其餘 → 自建 runner（`POST {RUNNER_URL}/run`，帶 X-Runner-Token）

runner 回應欄位與狀態字串已在 R1 對齊 ExecutionResult / Judge0 慣例，直接建模。
"""

import httpx

from core.config import settings
from core.errors import AppError

# re-export：呼叫端從本模組取得完整介面（模型正本仍在 judge0.py）
from services.judge0 import (
    CPP_LANGUAGE_ID,
    ExecutionResult,
)
from services.judge0 import (
    submit_and_poll as _judge0_submit_and_poll,
)

# 最長等待：runner 排隊上限 30s + 編譯 12s + 執行 12s，取 60s 保險
_RUNNER_TIMEOUT = 60.0


async def submit_and_poll(
    source_code: str,
    stdin: str = "",
    language_id: int = CPP_LANGUAGE_ID,
    command_line_arguments: str = "",
) -> ExecutionResult:
    """執行程式碼 — 依設定分派至自建 runner 或 Judge0。"""
    if settings.RUNNER_BACKEND == "judge0" or not settings.RUNNER_URL:
        return await _judge0_submit_and_poll(
            source_code=source_code,
            stdin=stdin,
            language_id=language_id,
            command_line_arguments=command_line_arguments,
        )
    return await _self_runner(source_code, stdin, command_line_arguments)


async def _self_runner(
    source_code: str, stdin: str, command_line_arguments: str
) -> ExecutionResult:
    """呼叫自建 runner。網路層例外一律轉 AppError，禁止冒泡成 500。"""
    url = settings.RUNNER_URL.rstrip("/") + "/run"
    headers = {"X-Runner-Token": settings.RUNNER_TOKEN}
    try:
        async with httpx.AsyncClient(timeout=_RUNNER_TIMEOUT) as client:
            resp = await client.post(
                url,
                headers=headers,
                json={
                    "code": source_code,
                    "stdin": stdin,
                    "args": command_line_arguments,
                },
            )
    except httpx.TimeoutException as e:
        raise AppError(
            504, "EXECUTION_TIMEOUT", "編譯/執行逾時，請縮短程式或減少迴圈次數"
        ) from e
    except httpx.HTTPError as e:
        raise AppError(
            503, "RUNNER_UNAVAILABLE", "執行服務暫時不可用，請稍後再試"
        ) from e

    if resp.status_code == 503:  # runner 排隊滿（RUNNER_BUSY）
        raise AppError(503, "RUNNER_BUSY", "執行服務忙碌中（排隊已滿），請稍候重試")
    if resp.status_code != 200:  # 401 = token 配置錯誤等，皆屬服務端問題
        raise AppError(502, "RUNNER_ERROR", f"執行服務錯誤 ({resp.status_code})")

    data = resp.json()
    return ExecutionResult(
        stdout=data.get("stdout", ""),
        stderr=data.get("stderr", ""),
        compile_output=data.get("compile_output", ""),
        exit_code=data.get("exit_code"),
        time=data.get("time"),
        memory=data.get("memory"),
        status_description=data.get("status_description", ""),
    )
