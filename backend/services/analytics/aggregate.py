"""行為指標聚合 service（roadmap 5-2d / Module 9）。

從 coding_events + chat_messages 計算單一使用者的行為指標，供教師端行為分析（5-3/5-4）與
個人摘要使用。

**設計決策**：compute-on-read（不建 `behavior_aggregates` 預聚合表、不排程）——初期 < 100 人
規模查詢壓力低；db-schema 所載預聚合表 + 定期計算屬效能優化，留待 5-3/5-4 有真實資料且出現
查詢壓力時再評估。dialogue_act 分布走 DB group_by（比照 6-R8「func.count() 取代全表載入」），
執行事件需時序配對修復時間故單查詢載精簡欄位後記憶體聚合。
"""

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.chat import ChatMessage, ChatSession
from models.coding_event import CodingEvent, CodingEventType

# 執行類事件（一次 Judge0 執行的三種結果）——編譯頻率 / 成功率的分母
_EXECUTION_TYPES = frozenset(
    {
        CodingEventType.SUCCESS.value,
        CodingEventType.COMPILE_ERROR.value,
        CodingEventType.RUNTIME_ERROR.value,
    }
)
_ERROR_TYPES = frozenset(
    {CodingEventType.COMPILE_ERROR.value, CodingEventType.RUNTIME_ERROR.value}
)


@dataclass
class BehaviorMetrics:
    """單一使用者的行為指標摘要。"""

    execution_count: int = 0  # 編譯/執行總次數
    success_count: int = 0
    success_rate: float = 0.0  # success_count / execution_count（無執行為 0）
    hint_request_count: int = 0
    # 平均修復時間（秒）：一次錯誤到下一次成功的間隔平均；無配對為 None
    avg_fix_duration_seconds: float | None = None
    # hint 等級分布 { "1": 3, "2": 5, ... }（僅 hint_request 事件）
    hint_distribution: dict[str, int] = field(default_factory=dict)
    # 對話行為分布 { "asking_hint": 4, "debugging": 7, ... }（5-2c dialogue_act）
    dialogue_act_distribution: dict[str, int] = field(default_factory=dict)


def _compute_fix_durations(
    events: list[tuple[str, datetime]]
) -> list[float]:
    """時序配對「首次未解錯誤 → 下一次成功」的間隔秒數（events 已依 created_at 升冪）。"""
    durations: list[float] = []
    pending_error_ts: datetime | None = None
    for event_type, created_at in events:
        if event_type in _ERROR_TYPES:
            if pending_error_ts is None:
                pending_error_ts = created_at
        elif event_type == CodingEventType.SUCCESS.value:
            if pending_error_ts is not None:
                durations.append((created_at - pending_error_ts).total_seconds())
                pending_error_ts = None
    return durations


async def _dialogue_act_distribution(
    db: AsyncSession,
    user_id,
    since: datetime | None,
    until: datetime | None,
) -> dict[str, int]:
    """DB group_by 統計使用者非空 dialogue_act 分布（chat_messages join session）。"""
    stmt = (
        select(ChatMessage.dialogue_act, func.count())
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(
            ChatSession.user_id == user_id,
            ChatMessage.dialogue_act.is_not(None),
        )
        .group_by(ChatMessage.dialogue_act)
    )
    if since is not None:
        stmt = stmt.where(ChatMessage.created_at >= since)
    if until is not None:
        stmt = stmt.where(ChatMessage.created_at <= until)
    rows = (await db.execute(stmt)).all()
    return {act: count for act, count in rows}


async def aggregate_user_behavior(
    db: AsyncSession,
    user_id,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
) -> BehaviorMetrics:
    """計算單一使用者在 [since, until] 區間的行為指標（compute-on-read）。"""
    stmt = (
        select(
            CodingEvent.event_type,
            CodingEvent.created_at,
            CodingEvent.hint_level,
        )
        .where(CodingEvent.user_id == user_id)
        .order_by(CodingEvent.created_at)
    )
    if since is not None:
        stmt = stmt.where(CodingEvent.created_at >= since)
    if until is not None:
        stmt = stmt.where(CodingEvent.created_at <= until)
    rows = (await db.execute(stmt)).all()

    metrics = BehaviorMetrics()
    executions: list[tuple[str, datetime]] = []
    for event_type, created_at, hint_level in rows:
        if event_type in _EXECUTION_TYPES:
            executions.append((event_type, created_at))
            metrics.execution_count += 1
            if event_type == CodingEventType.SUCCESS.value:
                metrics.success_count += 1
        elif event_type == CodingEventType.HINT_REQUEST.value:
            metrics.hint_request_count += 1
            key = str(hint_level if hint_level is not None else 0)
            metrics.hint_distribution[key] = metrics.hint_distribution.get(key, 0) + 1

    if metrics.execution_count:
        metrics.success_rate = metrics.success_count / metrics.execution_count

    durations = _compute_fix_durations(executions)
    if durations:
        metrics.avg_fix_duration_seconds = sum(durations) / len(durations)

    metrics.dialogue_act_distribution = await _dialogue_act_distribution(
        db, user_id, since, until
    )
    return metrics
