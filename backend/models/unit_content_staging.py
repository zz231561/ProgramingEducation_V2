"""UnitContentStaging ORM — Phase 6-2b grounded LLM 生成 unit content 中介存放區。

Schema 對齊 alembic migration `g3b4c5d6e7f8`。

設計：
- 1 row 對應 1 concept（UNIQUE(concept_id)），與用戶無關（內容 grounded 在 video）
- `content` JSON shape = `services.learning.content_generator.UnitContent`
- `status` 用 String + CHECK，沿用 quiz/learning_unit 慣例
- `needs_more_source` Bool：3 section 任一 flag → True，方便 6-4 教授抽查介面篩選
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class StagingStatus(str, enum.Enum):
    """Staging 審查狀態 — 對齊 6-4 教授抽查流程。"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UnitContentStaging(Base):
    """Grounded LLM 生成的 unit content 中介存放區（Phase 6-2b）。"""

    __tablename__ = "unit_content_staging"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    concept_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"),
    )
    content: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(20), default=StagingStatus.PENDING.value
    )
    needs_more_source: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    model_used: Mapped[str] = mapped_column(String(50), default="")
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    __table_args__ = (
        UniqueConstraint("concept_id", name="uq_unit_content_staging_concept"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_unit_content_staging_status_enum",
        ),
        CheckConstraint(
            "attempt_count >= 1", name="ck_unit_content_staging_attempt_positive"
        ),
        Index("ix_unit_content_staging_status", "status"),
        Index("ix_unit_content_staging_needs_more_source", "needs_more_source"),
    )
