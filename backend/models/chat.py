"""Chat Session / Message Models — 對應 Module 3: EDF 教學管線。"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    String,
    Text,
    Enum,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class MessageRole(str, enum.Enum):
    """訊息角色。"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class DialogueAct(str, enum.Enum):
    """學生訊息對話行為分類（StudyChat dialogue act schema，roadmap 5-2c）。"""

    ASKING_HINT = "asking_hint"
    CLARIFICATION_REQUEST = "clarification_request"
    DEBUGGING = "debugging"
    OFF_TOPIC = "off_topic"
    ACKNOWLEDGMENT = "acknowledgment"
    VERIFICATION = "verification"


class ChatSession(Base):
    """對話 Session — 一次教學互動上下文。"""

    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), default="新對話")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    """對話訊息 — 包含程式碼快照和 EDF 分析結果。"""

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
    )
    role: Mapped[MessageRole] = mapped_column(
        # values_callable：寫入 enum.value（小寫）對齊 Postgres ENUM；見 user.py 同款註解
        Enum(
            MessageRole,
            name="message_role",
            values_callable=lambda x: [e.value for e in x],
        ),
    )
    content: Mapped[str] = mapped_column(Text)
    code_snapshot: Mapped[str | None] = mapped_column(Text, default=None)
    execution_result: Mapped[dict | None] = mapped_column(JSON, default=None)
    evidence: Mapped[dict | None] = mapped_column(JSON, default=None)
    # 學生訊息對話行為分類（StudyChat schema，5-2c）；String+CHECK 避開 PG ENUM 雙寫坑，
    # 與 coding_events.event_type 同款；啟發式分類、訊號不足留 NULL（僅 user 訊息填值）
    dialogue_act: Mapped[str | None] = mapped_column(String(24), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    session: Mapped[ChatSession] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_chat_messages_session_created", "session_id", "created_at"),
        CheckConstraint(
            "dialogue_act IS NULL OR dialogue_act IN ("
            "'asking_hint', 'clarification_request', 'debugging', "
            "'off_topic', 'acknowledgment', 'verification')",
            name="ck_chat_messages_dialogue_act_enum",
        ),
    )
