"""Runner service 進入點 — POST /run（批次）+ GET /healthz。

R3 將在此加 WS /terminal（互動 PTY）。認證：X-Runner-Token 共享密鑰
（B 機防火牆僅放行 A 機之外的第二道縱深；token 未設定＝本機開發模式不驗）。
"""

import logging

from fastapi import FastAPI, Header, HTTPException

from .cache import binary_cache
from .compiler import compile_code
from .config import settings
from .executor import execute
from .gate import QueueTimeout, gate
from .models import STATUS_COMPILE_ERROR, RunRequest, RunResponse

logger = logging.getLogger(__name__)
app = FastAPI(title="codedge-runner", docs_url=None, redoc_url=None)


def _check_token(x_runner_token: str | None) -> None:
    if settings.token and x_runner_token != settings.token:
        raise HTTPException(status_code=401, detail="invalid runner token")


@app.get("/healthz")
async def healthz() -> dict:
    return {
        "status": "ok",
        "sandbox": settings.sandbox,
        "active": gate.active,
        "queue_depth": gate.queue_depth,
        "cache_entries": len(binary_cache),
    }


@app.post("/run")
async def run(
    req: RunRequest, x_runner_token: str | None = Header(default=None)
) -> RunResponse:
    _check_token(x_runner_token)
    if len(req.code.encode()) > settings.max_code_bytes:
        raise HTTPException(status_code=422, detail="code too large")

    # 編譯與批次執行都在閘內：執行有 wall 上限（≤12s），保護 2 核不被併發打穿。
    # R3 互動模式只在編譯階段持有 slot（等待輸入不佔）。
    try:
        async with gate.slot() as queued_ms:
            compiled = await compile_code(req.code)
            if compiled.binary_path is None:
                return RunResponse(
                    compile_output=compiled.compile_output,
                    status_description=STATUS_COMPILE_ERROR,
                    queued_ms=queued_ms,
                )
            result = await execute(compiled.binary_path, req.stdin, req.args)
            result.cache_hit = compiled.cache_hit
            result.queued_ms = queued_ms
            return result
    except QueueTimeout:
        raise HTTPException(status_code=503, detail="RUNNER_BUSY") from None
