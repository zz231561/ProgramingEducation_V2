"""LearningPath / LearningUnit ORM Models — 對應 Module 7: 學習路徑（roadmap 3-1a）。

Schema 對齊 alembic migration `c9d0e1f2a3b4` 與 `docs/db-schema.md` Module 7。

設計：
- `LearningUnitStatus` 用 str enum（與 QuestionType / ReflectionSourceType 慣例一致），
  避開 enum.value/.name 雙寫法 + SQLite 測試相容。
- `(path_id, order_index)` UNIQUE 強制同路徑內位置唯一。
- `concept_id` 指向 concepts 表（ON DELETE RESTRICT）— 概念被刪需先處理路徑。
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
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class LearningUnitStatus(str, enum.Enum):
    """學習單元狀態（漸進解鎖機制）。"""

    LOCKED = "locked"           # 前置單元未完成，不可進入
    AVAILABLE = "available"     # 可開始學習
    IN_PROGRESS = "in_progress" # 學生已開始但未完成
    COMPLETED = "completed"     # 通過所有練習


class LearningPath(Base):
    """學習路徑 — 一名學生對應 1+ 條路徑（不同主題/階段）。"""

    __tablename__ = "learning_paths"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (Index("ix_learning_paths_user_id", "user_id"),)


class LearningUnit(Base):
    """學習單元 — 一條路徑由多個有序單元組成，每個單元 1:1 對應一個 concept。

    `content` JSON 形狀（application 層驗證）：
    - {"summary": "...", "examples": [...], "exercise_question_ids": [UUID, ...]}
    - shape 隨教學需求演進；目前不強制欄位避免綁死 schema
    """

    __tablename__ = "learning_units"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    path_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("concepts.id", ondelete="RESTRICT"),
    )
    order_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(20), default=LearningUnitStatus.LOCKED.value
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    __table_args__ = (
        UniqueConstraint(
            "path_id", "order_index", name="uq_learning_units_path_order"
        ),
        CheckConstraint(
            "status IN ('locked', 'available', 'in_progress', 'completed')",
            name="ck_learning_units_status_enum",
        ),
        CheckConstraint(
            "order_index >= 0", name="ck_learning_units_order_non_negative"
        ),
        Index("ix_learning_units_path_id", "path_id"),
        Index("ix_learning_units_concept_id", "concept_id"),
    )
