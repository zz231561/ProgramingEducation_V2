"""測試環境 — 必須在 import app.* 之前設定環境變數（config 於 import 時讀取）。

sandbox=none：本機無 nsjail，以 rlimit 模式直接編譯執行（macOS clang / Linux g++ 皆可）。
"""

import os
import sys
import tempfile

os.environ["RUNNER_SANDBOX"] = "none"
os.environ["RUNNER_TOKEN"] = "test-token"
os.environ["RUNNER_CACHE_DIR"] = tempfile.mkdtemp(prefix="runner-test-cache-")
os.environ["RUNNER_EXEC_WALL"] = "1"  # 逾時測試不用等 10 秒
os.environ["RUNNER_PCH_HEADER"] = "/nonexistent/std.h"  # 本機無 PCH，明確跳過

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import pytest

from app.main import app  # noqa: E402 -- 測試路徑需先注入 sys.path


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://runner.test",
        headers={"X-Runner-Token": "test-token"},
        timeout=30.0,
    ) as c:
        yield c
