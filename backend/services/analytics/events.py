"""行為事件 logging service（roadmap 5-2b）。

從既有 Judge0 執行與 EDF 對話流程擷取事件寫入 `coding_events`。
一律 best-effort：失敗吞例外 + logger.warning，不阻擋主流程（比照 mastery/RAG 注入慣例）。
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.coding_event import CodingEvent, CodingEventType
from services.judge0 import ExecutionResult

logger = logging.getLogger(__name__)

_CODE_SNAPSHOT_MAX = 10_000  # 截斷過長程式碼避免膨脹


def classify_execution(result: ExecutionResult) -> CodingEventType:
    """依 Judge0 status 判定事件類型（編譯錯誤 / 成功 / 執行期錯誤）。"""
    status = (result.status_description or "").lower()
    if result.compile_output.strip() or "compil" in status:
        return CodingEventType.COMPILE_ERROR
    if status == "accepted":
        return CodingEventType.SUCCESS
    return CodingEventType.RUNTIME_ERROR


def _execution_summary(result: ExecutionResult) -> dict:
    """摘要 Judge0 結果（不存完整 stdout/stderr，只留分析所需欄位）。"""
    return {
        "status": result.status_description,
        "exit_code": result.exit_code,
        "time": result.time,
        "memory": result.memory,
        "has_stderr": bool(result.stderr.strip()),
        "has_compile_output": bool(result.compile_output.strip()),
    }


async def log_coding_event(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    event_type: CodingEventType,
    session_id: uuid.UUID | None = None,
    concept_tags: list[str] | None = None,
    code_snapshot: str | None = None,
    execution_result: dict | None = None,
    hint_level: int | None = None,
    event_metadata: dict | None = None,
) -> None:
    """best-effort 寫入一筆 coding_event；失敗不擋主流程。"""
    try:
        event = CodingEvent(
            user_id=user_id,
            event_type=event_type.value,
            session_id=session_id,
            concept_tags=concept_tags,
            code_snapshot=(code_snapshot or "")[:_CODE_SNAPSHOT_MAX] or None,
            execution_result=execution_result,
            hint_level=hint_level,
            event_metadata=event_metadata,
        )
        db.add(event)
        await db.commit()
    except Exception:
        logger.warning(
            "[analytics] log_coding_event failed user=%s type=%s",
            user_id,
            event_type,
            exc_info=True,
        )
        await db.rollback()


async def log_execution(
    db: AsyncSession, *, user_id: uuid.UUID, result: ExecutionResult, code: str
) -> None:
    """從一次 Judge0 執行記錄事件（成功 / 編譯錯誤 / 執行期錯誤）。"""
    await log_coding_event(
        db,
        user_id=user_id,
        event_type=classify_execution(result),
        code_snapshot=code,
        execution_result=_execution_summary(result),
    )
