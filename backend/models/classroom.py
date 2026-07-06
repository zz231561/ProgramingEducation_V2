"""班級 Models — 對應 Module 8: 教師端（roadmap 5-1a）。

Schema 對齊 alembic migration `l8a9b0c1d2e3` 與 db-schema.md §Module 8。
invite_code 的產生邏輯屬 5-1b（API 層）；本檔僅定義 schema。
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Classroom(Base):
    """教師建立的班級（__tablename__ = "classes"，避開 Python 保留字）。"""

    __tablename__ = "classes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    # 學生加入用的短碼；產生與碰撞重試在 API 層（5-1b）
    invite_code: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (Index("ix_classes_teacher_id", "teacher_id"),)


class ClassMember(Base):
    """班級成員關聯（複合主鍵 (class_id, user_id)）。"""

    __tablename__ = "class_members"

    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (Index("ix_class_members_user_id", "user_id"),)
