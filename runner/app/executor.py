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


async def execute(binary_path: str, stdin: str, args: str) -> RunResponse:
    """執行 binary；cwd 用全新空目錄（binary 在快取目錄，不受影響）。"""
    workdir = tempfile.mkdtemp(prefix="run-")
    # 沙箱模式下 binary 需綁進 /box：hardlink 進 workdir（同檔案系統零成本；跨 fs 退回複製）
    local = os.path.join(workdir, "app")
    try:
        os.link(binary_path, local)
    except OSError:
        shutil.copy2(binary_path, local)

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

    if result.timed_out:
        status, exit_code = STATUS_TIME_LIMIT, None
    elif result.returncode is not None and result.returncode < 0:
        status, exit_code = _signal_status(result.returncode), result.returncode
    elif result.returncode == 0:
        status, exit_code = STATUS_ACCEPTED, 0
    else:
        status, exit_code = STATUS_NZEC, result.returncode

    return RunResponse(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=exit_code,
        time=f"{result.wall_seconds:.3f}",
        status_description=status,
    )
