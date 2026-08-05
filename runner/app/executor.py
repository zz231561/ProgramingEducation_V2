"""批次執行 — 跑編譯好的 binary，把結果分類為 Judge0 慣例狀態。

狀態對映（前端 classifyStatus / run_help 依賴這些字串）：
- exit 0            → "Accepted"
- 逾時              → "Time Limit Exceeded"
- 訊號終止          → "Runtime Error (SIGXXX)"
- 非零 exit         → "Runtime Error (NZEC)"（Judge0 同名慣例）
"""

import os
import shlex
import shutil
import signal
import tempfile

from . import sandbox
from .config import settings
from .models import (
    STATUS_ACCEPTED,
    STATUS_NZEC,
    STATUS_TIME_LIMIT,
    RunResponse,
)
from .proc import run_process


def split_args(raw: str) -> list[str]:
    """空白分隔的 argv 字串 → list；引號語法錯誤時退回單純 split。"""
    if not raw.strip():
        return []
    try:
        return shlex.split(raw)
    except ValueError:
        return raw.split()


def _signal_status(returncode: int) -> str:
    sig = -returncode
    try:
        name = signal.Signals(sig).name
    except ValueError:
        name = f"signal {sig}"
    return f"Runtime Error ({name})"


def classify_exit(returncode: int | None, timed_out: bool) -> tuple[str, int | None]:
    """(status_description, exit_code) — 批次與互動終端共用的狀態分類。"""
    if timed_out:
        return STATUS_TIME_LIMIT, None
    if returncode is not None and returncode < 0:
        return _signal_status(returncode), returncode
    if returncode == 0:
        return STATUS_ACCEPTED, 0
    return STATUS_NZEC, returncode


def stage_workdir(binary_path: str) -> str:
    """建立全新執行目錄並把 binary 放入（沙箱綁定用），回傳 workdir。"""
    workdir = tempfile.mkdtemp(prefix="run-")
    # hardlink 零成本（快取同檔案系統）；跨 fs 退回複製
    local = os.path.join(workdir, "app")
    try:
        os.link(binary_path, local)
    except OSError:
        shutil.copy2(binary_path, local)
    return workdir


async def execute(binary_path: str, stdin: str, args: str) -> RunResponse:
    """執行 binary；cwd 用全新空目錄（binary 在快取目錄，不受影響）。"""
    workdir = stage_workdir(binary_path)

    argv = sandbox.wrap(
        ["./app", *split_args(args)],
        workdir,
        wall_seconds=settings.exec_wall_seconds,
        cpu_seconds=settings.exec_cpu_seconds,
        ram_mb=settings.exec_ram_mb,
    )
    result = await run_process(
        argv,
        cwd=workdir,
        stdin_data=stdin.encode(),
        wall_seconds=settings.exec_wall_seconds + 2,
        cpu_seconds=settings.exec_cpu_seconds,
        ram_mb=settings.exec_ram_mb,
    )

    status, exit_code = classify_exit(result.returncode, result.timed_out)

    return RunResponse(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=exit_code,
        time=f"{result.wall_seconds:.3f}",
        status_description=status,
    )
