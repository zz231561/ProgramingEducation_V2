"""程式行為事件 Model — 對應 Module 9 學習行為分析（roadmap 5-2a）。

event_type 採 ProgSnap2 EventType 詞彙（CC-BY-4.0，見 references.md §1）；
concept_tags / execution_result / event_metadata 用通用 JSON 存（與 quiz/reflection
慣例一致，避開 PG-only ARRAY/JSONB 以相容 SQLite 測試）。

Schema 對齊 db-schema.md §Module 9 與 alembic migration `o1d2e3f4a5b6`。
- SubjectID = user_id；EventID = id（ProgSnap2 五欄主鍵對映）
- `metadata` 為 SQLAlchemy 保留字，欄位改名 `event_metadata`
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class CodingEventType(str, enum.Enum):
    """程式行為事件類型（ProgSnap2 EventType 詞彙精簡對映）。"""

    SUBMIT = "submit"
    COMPILE_ERROR = "compile_error"
    RUNTIME_ERROR = "runtime_error"
    SUCCESS = "success"
    HINT_REQUEST = "hint_request"
    FIX = "fix"


class CodingEvent(Base):
    """單一程式行為事件（提交 / 編譯錯誤 / 執行成功 / hint / 修復等）。"""

    __tablename__ = "coding_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    # 事件發生時的對話情境（可選）；chat session 刪除時保留事件但清空關聯
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="SET NULL"),
        default=None,
    )
    event_type: Mapped[str] = mapped_column(String(20))

    # 涉及的 ConceptTag（list[str]）；用 JSON 相容 SQLite
    concept_tags: Mapped[list | None] = mapped_column(JSON, default=None)
    code_snapshot: Mapped[str | None] = mapped_column(Text, default=None)
    # Judge0 結果摘要（dict）
    execution_result: Mapped[dict | None] = mapped_column(JSON, default=None)
    # 觸發的 hint 等級（0-5）
    hint_level: Mapped[int | None] = mapped_column(SmallInteger, default=None)
    # 額外資訊（error_type / fix_duration_ms 等）；attr 改名避開保留字
    event_metadata: Mapped[dict | None] = mapped_column(JSON, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('submit', 'compile_error', 'runtime_error', "
            "'success', 'hint_request', 'fix')",
            name="ck_coding_events_event_type_enum",
        ),
        CheckConstraint(
            "hint_level IS NULL OR hint_level BETWEEN 0 AND 5",
            name="ck_coding_events_hint_level_range",
        ),
        # 時序查詢主路徑（某使用者依時間排序）
        Index("ix_coding_events_user_created", "user_id", "created_at"),
    )
