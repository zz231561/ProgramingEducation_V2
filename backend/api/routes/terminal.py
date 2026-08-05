"""互動終端 API — ticket 發放 + WS 中繼至 B 機 runner（7-R R3）。

為什麼用 ticket：前端 WS 直連 backend 公開子網域（Next.js Route Handler 不能
proxy WS），跨子網域帶不到 HttpOnly session cookie。故先經既有 proxy 打
``POST /terminal/ticket``（cookie 認證 + 沿用 execute rate limit）取得
單次使用、60 秒 TTL 的 ticket（存 Redis），WS 首訊息帶 ticket 換 session。

中繼：backend ↔ runner 以 X-Runner-Token 認證；frame 原樣轉發
（協議見 runner/app/terminal.py），僅在 exit/compile_error 時側錄
ExecutionResult 供行為事件記錄（best-effort）。
"""

import asyncio
import json
import logging
import secrets
import uuid

import websockets
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from api.deps import get_current_db_user, User
from core.config import settings
from core.database import async_session
from core.errors import AppError
from core.rate_limit import rate_limit
from core.redis import get_redis
from services.analytics import log_execution
from services.runner import ExecutionResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/terminal", tags=["terminal"])

_TICKET_TTL_SECONDS = 60
_FIRST_FRAME_TIMEOUT = 15


def _runner_ws_url() -> str:
    base = settings.RUNNER_URL.rstrip("/")
    return base.replace("http://", "ws://").replace("https://", "wss://") + "/terminal"


@router.post("/ticket", dependencies=[Depends(rate_limit("execute"))])
async def create_ticket(user: User = Depends(get_current_db_user)) -> dict:
    """發放單次使用 WS ticket。runner 未配置時 503（前端退回批次執行）。"""
    if settings.RUNNER_BACKEND == "judge0" or not settings.RUNNER_URL:
        raise AppError(503, "RUNNER_UNAVAILABLE", "互動終端目前未啟用")
    ticket = secrets.token_urlsafe(24)
    await get_redis().setex(f"terminal:ticket:{ticket}", _TICKET_TTL_SECONDS, str(user.id))
    return {"ticket": ticket}


async def _consume_ticket(ticket: str) -> uuid.UUID | None:
    try:
        user_id = await get_redis().getdel(f"terminal:ticket:{ticket}")
    except Exception:  # Redis 掛掉：終端不可用（批次路徑不受影響）
        logger.warning("terminal ticket lookup failed", exc_info=True)
        return None
    return uuid.UUID(user_id) if user_id else None


@router.websocket("/ws")
async def terminal_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        first = await asyncio.wait_for(ws.receive_json(), timeout=_FIRST_FRAME_TIMEOUT)
    except (TimeoutError, WebSocketDisconnect):
        await ws.close(code=4408)
        return

    user_id = await _consume_ticket(str(first.get("ticket", "")))
    if user_id is None or first.get("type") != "start" or not first.get("code"):
        await ws.send_json({"type": "error", "code": "UNAUTHORIZED"})
        await ws.close(code=4401)
        return

    code = first["code"]
    try:
        await _relay(ws, user_id, code, str(first.get("args", "")))
    except (WebSocketDisconnect, RuntimeError):
        pass  # 學生關頁面；runner 端 session 由其 stdin pump 斷線回收
    except Exception:
        logger.warning("terminal relay failed", exc_info=True)
        try:
            await ws.send_json({"type": "error", "code": "RUNNER_UNAVAILABLE"})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


async def _relay(ws: WebSocket, user_id: uuid.UUID, code: str, args: str) -> None:
    headers = {"X-Runner-Token": settings.RUNNER_TOKEN}
    async with websockets.connect(
        _runner_ws_url(), additional_headers=headers
    ) as runner:
        await runner.send(json.dumps({"type": "start", "code": code, "args": args}))

        async def to_runner() -> None:
            while True:
                msg = await ws.receive_json()
                if msg.get("type") == "stdin":  # 只轉發 stdin，其餘丟棄
                    await runner.send(json.dumps(msg))

        async def to_client() -> dict | None:
            async for raw in runner:
                frame = json.loads(raw)
                await ws.send_json(frame)
                if frame.get("type") in ("exit", "compile_error"):
                    return frame
            return None

        up = asyncio.create_task(to_runner())
        try:
            final = await to_client()
        finally:
            up.cancel()
    if final is not None:
        await _log_session(user_id, code, final)


async def _log_session(user_id: uuid.UUID, code: str, frame: dict) -> None:
    """行為事件記錄（best-effort，與批次 /code/execute 同一管線）。"""
    result = ExecutionResult(
        stdout=frame.get("output_summary", ""),
        compile_output=frame.get("output", ""),  # compile_error frame 才有
        exit_code=frame.get("exit_code"),
        time=frame.get("time"),
        status_description=frame.get("status_description", ""),
    )
    try:
        async with async_session() as db:
            await log_execution(db, user_id=user_id, result=result, code=code)  # 自行 commit
    except Exception:
        logger.warning("terminal log_execution failed", exc_info=True)
