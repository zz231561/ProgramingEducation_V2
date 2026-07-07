"""作業 Models — 對應 Module 8: 教師端（roadmap 5-5，TronClass 式文件繳交）。

Schema 對齊 alembic migration `q3f4a5b6c7d8` 與 db-schema.md §Module 8。
設計：
- 教師建立作業（標題 + 內容 + 附件）指派整班 → 學生繳交（文字 + 附件）→ 教師評分/評語。
- 附件內容存 Postgres bytea（`LargeBinary`）——Zeabur 容器檔案系統 ephemeral，存 DB 才不遺失；
  單檔 ≤ 10MB（DB CHECK + API 雙重把關）。
- `attachments` 多型（owner_type = assignment / submission）同時服務教師附件與學生繳交附件；
  polymorphic 無 FK cascade，刪除由 service 層顯式處理。
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base

# 單檔大小上限（bytes）；API 與 DB CHECK 共用
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024  # 10 MB


class AttachmentOwner(str, enum.Enum):
    """附件歸屬類型（多型 owner）。"""

    ASSIGNMENT = "assignment"  # 教師建立作業時的附件（教材 / 題目卷）
    SUBMISSION = "submission"  # 學生繳交的附件


class Assignment(Base):
    """教師建立的作業（指派給整個班級）。"""

    __tablename__ = "assignments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"),
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("ix_assignments_class_id", "class_id"),)


class AssignmentSubmission(Base):
    """學生對某作業的繳交（每生每作業至多一份，重繳覆蓋）。"""

    __tablename__ = "assignment_submissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"),
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    text: Mapped[str] = mapped_column(Text, default="")
    # 教師評分（nullable = 未批改）；不設固定量尺上限，只擋負值
    score: Mapped[float | None] = mapped_column(Float, default=None)
    feedback: Mapped[str] = mapped_column(Text, default="")
    graded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "assignment_id", "student_id", name="uq_submission_assignment_student"
        ),
        CheckConstraint("score IS NULL OR score >= 0", name="ck_submission_score_non_negative"),
        Index("ix_submissions_assignment_id", "assignment_id"),
        Index("ix_submissions_student_id", "student_id"),
    )


class Attachment(Base):
    """多型附件（作業 / 繳交）— 檔案內容存 bytea。"""

    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_type: Mapped[str] = mapped_column(String(20))
    owner_id: Mapped[uuid.UUID] = mapped_column()
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    content: Mapped[bytes] = mapped_column(LargeBinary)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "owner_type IN ('assignment', 'submission')",
            name="ck_attachments_owner_type_enum",
        ),
        CheckConstraint(
            f"size_bytes >= 0 AND size_bytes <= {MAX_ATTACHMENT_BYTES}",
            name="ck_attachments_size_limit",
        ),
        Index("ix_attachments_owner", "owner_type", "owner_id"),
    )
