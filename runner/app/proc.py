"""子行程執行底層 — compile 與 run 共用的 subprocess 包裝。

安全設計：
- 輸出**串流封頂**讀取（超過 output_limit_bytes 即丟棄）——不能用 communicate()
  一次全讀，否則 `while(1) cout` 會在截斷前把 runner 自己灌爆記憶體。
- sandbox=nsjail 時資源限制由 nsjail 旗標負責；sandbox=none（本機測試）時
  以 preexec_fn + setrlimit 補基本限制（RLIMIT_AS 僅 Linux 可靠，macOS 跳過）。
"""

import asyncio
import resource
import sys
import time
from dataclasses import dataclass

from .config import settings

_CHUNK = 65536
_IO_GRACE_SECONDS = 2  # 行程結束後等 reader 收尾的上限（防孫行程佔住 pipe）


@dataclass
class ProcResult:
    returncode: int | None  # None = 逾時被殺
    stdout: str
    stderr: str
    timed_out: bool
    wall_seconds: float
    truncated: bool


def _rlimit_preexec(cpu_seconds: int, ram_mb: int):
    """sandbox=none 模式的資源限制（fork 後、exec 前套用）。"""

    def apply() -> None:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1))
        if sys.platform == "linux":
            ram = ram_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (ram, ram))
            resource.setrlimit(
                resource.RLIMIT_NPROC, (settings.exec_pids, settings.exec_pids)
            )

    return apply


async def _feed_stdin(proc: asyncio.subprocess.Process, data: bytes) -> None:
    if proc.stdin is None:
        return
    try:
        if data:
            proc.stdin.write(data)
            await proc.stdin.drain()
    except (BrokenPipeError, ConnectionResetError):
        pass  # 程式沒讀輸入就結束，正常情境
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass


async def _read_capped(stream: asyncio.StreamReader | None) -> tuple[bytes, bool]:
    """讀到 EOF，但只保留前 output_limit_bytes，其餘持續丟棄（讓程式能寫完）。"""
    if stream is None:
        return b"", False
    limit = settings.output_limit_bytes
    buf = bytearray()
    truncated = False
    while True:
        chunk = await stream.read(_CHUNK)
        if not chunk:
            return bytes(buf), truncated
        room = limit - len(buf)
        if room > 0:
            buf += chunk[:room]
        if len(chunk) > room:
            truncated = True


async def run_process(
    argv: list[str],
    *,
    cwd: str,
    stdin_data: bytes = b"",
    wall_seconds: int,
    cpu_seconds: int,
    ram_mb: int,
) -> ProcResult:
    """執行 argv 直到結束或逾時；輸出串流封頂。"""
    preexec = (
        _rlimit_preexec(cpu_seconds, ram_mb) if settings.sandbox == "none" else None
    )
    started = time.monotonic()
    proc = await asyncio.create_subprocess_exec(
        *argv,
        cwd=cwd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        preexec_fn=preexec,
    )
    io_task = asyncio.gather(
        _feed_stdin(proc, stdin_data),
        _read_capped(proc.stdout),
        _read_capped(proc.stderr),
    )

    timed_out = False
    try:
        await asyncio.wait_for(proc.wait(), timeout=wall_seconds)
    except TimeoutError:
        timed_out = True
        proc.kill()
        await proc.wait()

    # 行程已結束，reader 應在 EOF 收尾；孫行程若佔住 pipe 則寬限後放棄
    try:
        _, (out, t_out), (err, t_err) = await asyncio.wait_for(
            io_task, timeout=_IO_GRACE_SECONDS
        )
    except TimeoutError:
        io_task.cancel()
        out, err, t_out, t_err = b"", b"", True, True

    return ProcResult(
        returncode=None if timed_out else proc.returncode,
        stdout=out.decode("utf-8", errors="replace"),
        stderr=err.decode("utf-8", errors="replace"),
        timed_out=timed_out,
        wall_seconds=time.monotonic() - started,
        truncated=t_out or t_err,
    )
