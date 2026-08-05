"""WS /terminal — 互動終端 session（7-R R3）。

Frame 協議（backend 中繼原樣轉發給前端，R4 依此渲染）：
- client → runner：``start{code,args}``、``stdin{data}``
- runner → client：``queue{position}``、``compiling``、``compile_error{output}``、
  ``started``、``output{data}``、``exit{exit_code,status_description,time,output_summary}``、
  ``error{code}``

資源紀律：gate slot **只在編譯階段持有**（等待輸入不佔）；
idle 60s（無輸入且無輸出）/ 硬上限 300s / 同時 session 上限 40。
"""

import asyncio
import contextlib
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from . import sandbox
from .compiler import compile_code
from .config import settings
from .executor import classify_exit, split_args, stage_workdir
from .gate import QueueTimeout, gate
from .models import STATUS_COMPILE_ERROR
from .pty_exec import PtyProcess

router = APIRouter()
active_sessions = 0

# 看門狗覆寫的結束狀態（"Time Limit" 子字串維持前端 limit-exceeded 分類）
STATUS_IDLE = "Session Idle Timeout"
STATUS_HARD = "Session Time Limit Exceeded"


@router.websocket("/terminal")
async def terminal(ws: WebSocket) -> None:
    global active_sessions
    if settings.token and ws.headers.get("x-runner-token") != settings.token:
        await ws.close(code=4401)
        return
    await ws.accept()
    if active_sessions >= settings.max_sessions:
        await ws.send_json({"type": "error", "code": "SESSION_LIMIT"})
        await ws.close()
        return
    active_sessions += 1
    try:
        await _run_session(ws)
    except (WebSocketDisconnect, RuntimeError):
        pass  # 客端斷線（RuntimeError = 對已關閉的 WS send）
    finally:
        active_sessions -= 1
        with contextlib.suppress(Exception):
            await ws.close()


async def _compile_phase(ws: WebSocket, code: str) -> str | None:
    """編譯（gate 內，排隊回報位置）；失敗回 None（已送 compile_error）。"""
    loop = asyncio.get_running_loop()

    def on_wait(position: int) -> None:
        if position:
            loop.create_task(ws.send_json({"type": "queue", "position": position}))

    try:
        async with gate.slot(on_wait):
            await ws.send_json({"type": "compiling"})
            compiled = await compile_code(code)
    except QueueTimeout:
        await ws.send_json({"type": "error", "code": "RUNNER_BUSY"})
        return None
    if compiled.binary_path is None:
        await ws.send_json(
            {
                "type": "compile_error",
                "output": compiled.compile_output,
                "status_description": STATUS_COMPILE_ERROR,
            }
        )
        return None
    return compiled.binary_path


async def _run_session(ws: WebSocket) -> None:
    start = await asyncio.wait_for(ws.receive_json(), timeout=15)
    if start.get("type") != "start" or not start.get("code"):
        await ws.send_json({"type": "error", "code": "BAD_START"})
        return

    binary = await _compile_phase(ws, start["code"])
    if binary is None:
        return

    workdir = stage_workdir(binary)
    argv = sandbox.wrap(
        ["./app", *split_args(start.get("args", ""))],
        workdir,
        wall_seconds=settings.session_hard_seconds,
        cpu_seconds=settings.exec_cpu_seconds,
        ram_mb=settings.exec_ram_mb,
    )
    proc = PtyProcess()
    await proc.spawn(argv, cwd=workdir)
    await ws.send_json({"type": "started"})

    kill_reason: list[str] = []  # 看門狗寫入，結束時覆寫狀態
    tasks = [
        asyncio.create_task(_pump_output(ws, proc)),
        asyncio.create_task(_pump_stdin(ws, proc)),
        asyncio.create_task(_watchdog(proc, kill_reason)),
    ]
    try:
        rc = await proc.wait()
        # 讓 output pump 把殘餘輸出（含 EOF 訊號）送完
        await tasks[0]
    finally:
        for t in tasks:
            t.cancel()
        proc.kill()
        proc.close()

    status, exit_code = classify_exit(rc, timed_out=False)
    if kill_reason:
        status, exit_code = kill_reason[0], None
    await ws.send_json(
        {
            "type": "exit",
            "exit_code": exit_code,
            "status_description": status,
            "time": f"{proc.wall_seconds:.3f}",
            "output_summary": proc.summary,
        }
    )


async def _pump_output(ws: WebSocket, proc: PtyProcess) -> None:
    while True:
        text = await proc.output.get()
        if text is None:  # EOF
            return
        await ws.send_json({"type": "output", "data": text})


async def _pump_stdin(ws: WebSocket, proc: PtyProcess) -> None:
    try:
        while True:
            msg = await ws.receive_json()
            if msg.get("type") == "stdin":
                proc.write_stdin(str(msg.get("data", "")))
    except WebSocketDisconnect:
        proc.kill()  # 學生關頁面 → 立即回收行程，不等 idle 看門狗


async def _watchdog(proc: PtyProcess, kill_reason: list[str]) -> None:
    while True:
        await asyncio.sleep(0.25)
        now = time.monotonic()
        if now - proc.started_at > settings.session_hard_seconds:
            kill_reason.append(STATUS_HARD)
        elif now - proc.last_activity > settings.session_idle_seconds:
            kill_reason.append(STATUS_IDLE)
        else:
            continue
        proc.kill()
        return
