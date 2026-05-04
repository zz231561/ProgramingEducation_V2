"""Concept / ConceptEdge ORM Models — 對應 Module 5: 知識圖譜。

Schema 對齊 alembic migration `c3d4e5f6a7b8` 與 `docs/db-schema.md` Module 5。
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class EdgeType(str, enum.Enum):
    """概念邊類型（db-schema.md Module 5）。"""

    PREREQUISITE = "prerequisite"
    CONTAINS = "contains"
    SPECIALIZATION = "specialization"
    RELATED = "related"


class Concept(Base):
    """知識圖譜節點 — 對應 EDF ConceptTag enum。"""

    __tablename__ = "concepts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tag: Mapped[str] = mapped_column(String(50), unique=True)
    name_zh: Mapped[str] = mapped_column(String(100))
    name_en: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    difficulty_level: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "difficulty_level BETWEEN 1 AND 5",
            name="ck_concepts_difficulty_range",
        ),
        Index("ix_concepts_category", "category"),
    )


class ConceptEdge(Base):
    """知識圖譜邊 — 概念之間的關係。"""

    __tablename__ = "concept_edges"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"),
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"),
    )
    edge_type: Mapped[EdgeType] = mapped_column(
        # values_callable：與 user_role/message_role 同款修補；
        # PG ENUM 用小寫 value，無此設定讀取時會以 enum.name 比對而 LookupError
        Enum(
            EdgeType,
            name="concept_edge_type",
            values_callable=lambda x: [e.value for e in x],
        ),
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    source: Mapped[Concept] = relationship(foreign_keys=[source_id])
    target: Mapped[Concept] = relationship(foreign_keys=[target_id])

    __table_args__ = (
        UniqueConstraint(
            "source_id", "target_id", "edge_type", name="uq_concept_edges_triple"
        ),
        CheckConstraint("source_id <> target_id", name="ck_concept_edges_no_self"),
        Index("ix_concept_edges_source", "source_id"),
        Index("ix_concept_edges_target", "target_id"),
    )
