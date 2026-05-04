"""StudentMastery ORM Model — 對應 Module 5: 精熟度追蹤。

Schema 對齊 alembic migration `e5f6a7b8c9d0`。
2-3b 將由 pyBKT + EDF Evidence 共同維護 confidence / counts；本檔僅 schema。
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class StudentMastery(Base):
    """單一 (user, concept) 對的精熟度記錄。"""

    __tablename__ = "student_mastery"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"),
    )

    # pyBKT 維護的精熟機率（0-1）
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # 累計互動次數（由 EDF Pipeline 寫入）
    exposure_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)

    # 已達到的最高 Bloom 等級（1-6）；尚未互動為 None
    bloom_level: Mapped[int | None] = mapped_column(SmallInteger, default=None)
    last_practiced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "concept_id", name="uq_student_mastery_user_concept"
        ),
        CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name="ck_student_mastery_confidence_range",
        ),
        CheckConstraint(
            "bloom_level IS NULL OR bloom_level BETWEEN 1 AND 6",
            name="ck_student_mastery_bloom_range",
        ),
        CheckConstraint(
            "exposure_count >= 0 AND success_count >= 0 AND error_count >= 0",
            name="ck_student_mastery_counts_non_negative",
        ),
        Index("ix_student_mastery_user_id", "user_id"),
        Index("ix_student_mastery_concept_id", "concept_id"),
    )
