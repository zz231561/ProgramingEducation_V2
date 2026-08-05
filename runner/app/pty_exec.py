"""PTY 行程 — 互動終端的核心（7-R R3）。

為什麼是 PTY 而非 pipe：程式偵測到 tty 時 stdout 轉行緩衝，
`cout << "請輸入姓名: "`（無 endl）的提示字**即時出現**；kernel 行規範
（ICANON/ECHO/ICRNL）原生處理行編輯、回顯與 \r→\n，前端 xterm 無需 local echo。

輸出以 asyncio.Queue 交給 WS sender（add_reader 回呼是同步的，不能直接 await）。
"""

import asyncio
import codecs
import os
import pty
import time

from .config import settings
from .proc import _rlimit_preexec

_READ_CHUNK = 65536
_STDIN_FRAME_CAP = 4096  # 單一 stdin frame 上限（防灌注）


class PtyProcess:
    """spawn 一個掛在 PTY 上的行程，輸出推入 queue、輸入寫回 master。"""

    def __init__(self) -> None:
        self.output: asyncio.Queue[str | None] = asyncio.Queue()  # None = EOF
        self.last_activity = time.monotonic()
        self.started_at = time.monotonic()
        self._summary = bytearray()  # 給 backend 做 EDF/analytics 的輸出摘要
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._master: int | None = None
        self._proc: asyncio.subprocess.Process | None = None

    async def spawn(self, argv: list[str], cwd: str) -> None:
        master, slave = pty.openpty()
        self._master = master
        preexec = (
            _rlimit_preexec(settings.exec_cpu_seconds, settings.exec_ram_mb)
            if settings.sandbox == "none"
            else None
        )
        self._proc = await asyncio.create_subprocess_exec(
            *argv,
            cwd=cwd,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            preexec_fn=preexec,
            start_new_session=True,  # 自成 process group，kill 時整組收
        )
        os.close(slave)
        self.started_at = self.last_activity = time.monotonic()
        asyncio.get_running_loop().add_reader(master, self._on_readable)

    def _on_readable(self) -> None:
        if self._master is None:  # close() 之後殘留的回呼
            return
        try:
            data = os.read(self._master, _READ_CHUNK)
        except OSError:  # 行程結束後 master 讀到 EIO = EOF
            data = b""
        if not data:
            asyncio.get_running_loop().remove_reader(self._master)
            self.output.put_nowait(None)
            return
        self.last_activity = time.monotonic()
        room = settings.summary_limit_bytes - len(self._summary)
        if room > 0:
            self._summary += data[:room]
        self.output.put_nowait(self._decoder.decode(data))

    def write_stdin(self, text: str) -> None:
        if self._master is None:
            return
        self.last_activity = time.monotonic()
        try:
            os.write(self._master, text[:_STDIN_FRAME_CAP].encode())
        except OSError:
            pass  # 行程剛結束的 race，忽略

    def kill(self) -> None:
        if self._proc and self._proc.returncode is None:
            self._proc.kill()

    async def wait(self) -> int | None:
        """等行程結束。master 不在此關閉——EOF 回呼可能尚未觸發（race），
        由 session 端 drain 完 queue 後呼叫 close()。"""
        assert self._proc is not None
        return await self._proc.wait()

    def close(self) -> None:
        if self._master is None:
            return
        try:
            asyncio.get_running_loop().remove_reader(self._master)
        except Exception:
            pass
        try:
            os.close(self._master)
        except OSError:
            pass
        self._master = None

    @property
    def summary(self) -> str:
        return self._summary.decode("utf-8", errors="replace")

    @property
    def wall_seconds(self) -> float:
        return time.monotonic() - self.started_at
