"""`/chat/interact` 的 SSE 組裝層（7-U6）。

自 `chat.py` 抽出：加入串流後該檔到 263 行、超過 250 硬上限，而膨脹全來自
這裡的邏輯。路由本身只留宣告與依賴注入，串流細節集中於此。

事件序：`stage`（analyzing → retrieving → composing）→ `done`（InteractResponse）。
管線途中失敗時 HTTP header 已送出、無法改 status，故以 `error` 事件回報；
rate limit / 認證等前置檢查發生在串流開始前，仍是正常的 429 / 401。
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.coding_event import CodingEventType
from models.user import User
from services.analytics import log_coding_event
from services.chat import interact

logger = logging.getLogger(__name__)

# 沒有階段事件排入時的輪詢間隔；夠小到進度即時，又不會空轉燒 CPU
_DRAIN_INTERVAL = 0.1


def sse(event: str, data: dict) -> str:
    """組一則 SSE 事件。data 一律單行 JSON，避免多行 payload 破壞格式。"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def interact_event_stream(
    *,
    db: AsyncSession,
    user: User,
    body,  # InteractRequest（型別在 chat.py，此處避免循環 import）
    debug_sink: dict | None,
    build_payload: Callable[[object, object, object], dict],
) -> AsyncIterator[str]:
    """跑 EDF 管線並邊跑邊推播階段；結束後推 done 或 error。"""
    queue: asyncio.Queue[str] = asyncio.Queue()
    # 7-C2a：揭露等級在 service 內算出，回填此處供 hint_request 事件記錄
    strategy_sink: dict = {}

    async def on_stage(stage: str) -> None:
        await queue.put(sse("stage", {"stage": stage}))

    task = asyncio.create_task(
        interact(
            db=db,
            user_id=user.id,
            code=body.code,
            question=body.question,
            session_id=body.session_id,
            execution_result=body.execution_result,
            reflection_id=body.reflection_id,
            explicit_help=body.explicit_help,
            debug_sink=debug_sink,
            strategy_sink=strategy_sink,
            on_stage=on_stage,
        )
    )

    # 邊跑邊送已排入的階段事件；管線結束後再排空剩餘的
    while not task.done() or not queue.empty():
        try:
            yield await asyncio.wait_for(queue.get(), timeout=_DRAIN_INTERVAL)
        except TimeoutError:
            continue

    try:
        session, user_msg, ai_msg = task.result()
    except AppError as e:
        yield sse("error", {"error": e.error, "message": e.message})
        return
    except Exception:
        # 內部細節（連線字串、堆疊）不可外流給學生，只記 log
        logger.exception("chat interact failed")
        yield sse("error", {"error": "INTERNAL_ERROR", "message": "系統發生錯誤"})
        return

    # 學生真的需要額外協助時才記 hint_request（best-effort）。
    # 判準用 need 而非 reveal_level：後者的 base 來自錯誤類型，
    # 學生第一次貼出編譯錯誤就已經是 2，照記會把每一輪都算成求助
    if strategy_sink.get("need", 0) > 0:
        reveal_level = strategy_sink.get("reveal_level", 0)
        evidence = ai_msg.evidence if isinstance(ai_msg.evidence, dict) else {}
        await log_coding_event(
            db,
            user_id=user.id,
            event_type=CodingEventType.HINT_REQUEST,
            session_id=session.id,
            hint_level=reveal_level,
            concept_tags=evidence.get("concept_tags"),
            code_snapshot=body.code,
        )

    yield sse("done", build_payload(session, user_msg, ai_msg))
