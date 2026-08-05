"""並行閘 — 限制同時編譯/執行數，超出者排隊並可回報位置。

設計意圖：R3 互動終端只在編譯階段持有 slot（等待輸入時不佔），
所以 acquire 範圍由呼叫端控制；position 回呼供 WS 即時推送「排隊中 n/m」。
"""

import asyncio
import time
from collections.abc import Callable
from contextlib import asynccontextmanager

from .config import settings


class QueueTimeout(Exception):
    """排隊超過上限時間，呼叫端應回 503 RUNNER_BUSY。"""


class Gate:
    def __init__(self) -> None:
        self._sem = asyncio.Semaphore(settings.gate_slots)
        self._waiters: list[object] = []  # 以身分物件記錄排隊順序
        self.active = 0

    @property
    def queue_depth(self) -> int:
        return len(self._waiters)

    def position_of(self, ticket: object) -> int:
        """1-indexed 排隊位置；不在隊中回 0。"""
        try:
            return self._waiters.index(ticket) + 1
        except ValueError:
            return 0

    @asynccontextmanager
    async def slot(self, on_wait: Callable[[int], None] | None = None):
        """取得一個 slot；排隊時（可選）回報位置。yield 排隊毫秒數。"""
        ticket = object()
        self._waiters.append(ticket)
        if on_wait:
            on_wait(self.position_of(ticket))
        started = time.monotonic()
        try:
            try:
                await asyncio.wait_for(
                    self._sem.acquire(), timeout=settings.gate_queue_timeout
                )
            except TimeoutError as e:
                raise QueueTimeout() from e
        finally:
            self._waiters.remove(ticket)

        self.active += 1
        try:
            yield int((time.monotonic() - started) * 1000)
        finally:
            self.active -= 1
            self._sem.release()


gate = Gate()
