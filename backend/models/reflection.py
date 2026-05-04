"""Reflection ORM Model — 對應跨模組機制：Pre-Coding Reflection。

Schema 對齊 alembic migration `a7b8c9d0e1f2`。
source_type 用 str 列舉避開 PG ENUM 雙重寫法的坑。
source_id 為 polymorphic UUID（不建 FK），指向 questions.id / learning_units.id；
應用層在 create 時驗證有效性。
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ReflectionSourceType(str, enum.Enum):
    """反思觸發來源。"""

    QUIZ = "quiz"
    LEARNING_UNIT = "learning_unit"


class Reflection(Base):
    """解題前反思（Pre-Coding Reflection）。

    `planned_steps` JSON 形狀：list[str]，學生填寫的步驟條列。
    """

    __tablename__ = "reflections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    source_type: Mapped[str] = mapped_column(String(20))
    source_id: Mapped[uuid.UUID] = mapped_column()
    problem_understanding: Mapped[str] = mapped_column(Text, default="")
    planned_steps: Mapped[list[str]] = mapped_column(JSON)
    expected_concepts: Mapped[str] = mapped_column(Text, default="")
    quality_score: Mapped[float | None] = mapped_column(Float, default=None)
    followup_question: Mapped[str | None] = mapped_column(Text, default=None)
    followup_answer: Mapped[str | None] = mapped_column(Text, default=None)
    is_modified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('quiz', 'learning_unit')",
            name="ck_reflections_source_type_enum",
        ),
        CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0.0 AND quality_score <= 1.0)",
            name="ck_reflections_quality_score_range",
        ),
        UniqueConstraint(
            "user_id", "source_type", "source_id",
            name="uq_reflections_user_source",
        ),
        Index("ix_reflections_user_id", "user_id"),
        Index("ix_reflections_source", "source_type", "source_id"),
    )
