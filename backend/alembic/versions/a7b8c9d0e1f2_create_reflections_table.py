"""create reflections table

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-05-04 00:00:00.000000

對應 roadmap 2-5a：Pre-Coding Reflection 解題前反思（跨模組機制，schema 見 db-schema.md）。

設計取捨：
- `source_type` 用 String + CHECK 而非 PG ENUM：與 quiz/concept 表慣例一致，避開
  enum.value/.name 雙重寫法的坑，且 SQLite 測試需要相容。
- `source_id` 為「polymorphic」UUID（指向 questions.id 或 learning_units.id），
  因目標表不固定，不建立 FK；應用層在 create 時驗證指向有效對象。
- `planned_steps` 用 JSON（list of strings）：步驟數量不定，application 層驗證 shape。
- `(user_id, source_type, source_id)` UNIQUE：同一學生對同一題只允許一份反思，
  後續修改走 PATCH（updated_at + is_modified）。
- `learning_units` 表尚未建立（Phase 3-1a），但 source_type='learning_unit' 已先在 schema
  保留，避免之後再加欄位 + migrate。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_REFLECTION_SOURCE_TYPES = ("quiz", "learning_unit")


def upgrade() -> None:
    op.create_table(
        "reflections",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("problem_understanding", sa.Text(), nullable=False, server_default=""),
        # planned_steps：JSON list of strings
        sa.Column("planned_steps", sa.JSON(), nullable=False),
        sa.Column("expected_concepts", sa.Text(), nullable=False, server_default=""),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("followup_question", sa.Text(), nullable=True),
        sa.Column("followup_answer", sa.Text(), nullable=True),
        sa.Column(
            "is_modified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            f"source_type IN {_REFLECTION_SOURCE_TYPES}",
            name="ck_reflections_source_type_enum",
        ),
        sa.CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0.0 AND quality_score <= 1.0)",
            name="ck_reflections_quality_score_range",
        ),
        sa.UniqueConstraint(
            "user_id", "source_type", "source_id",
            name="uq_reflections_user_source",
        ),
    )
    op.create_index("ix_reflections_user_id", "reflections", ["user_id"])
    op.create_index(
        "ix_reflections_source", "reflections", ["source_type", "source_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_reflections_source", table_name="reflections")
    op.drop_index("ix_reflections_user_id", table_name="reflections")
    op.drop_table("reflections")
