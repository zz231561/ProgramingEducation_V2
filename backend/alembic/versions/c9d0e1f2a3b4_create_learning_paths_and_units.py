"""create learning_paths + learning_units tables

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-05-05 00:00:00.000000

對應 roadmap 3-1a：結構化學習路徑基礎 schema（Module 7）。

設計取捨：
- `status` 用 String + CHECK：與 quiz/concept/reflection 慣例一致，避開 PG ENUM 雙寫法
  + SQLite 測試相容。
- `(path_id, order_index)` UNIQUE：同 path 內順序唯一，禁止位置碰撞。
- `content` 用 JSON（dict）：unit 內容形狀依教學需求變化（summary / examples /
  exercise_question_ids 等），application 層驗證 shape。
- 預設 `status='locked'`：路徑生成（3-1b）後由 service 解鎖第一單元；後續單元依完成度
  漸進解鎖。
- `learning_paths` 不加 `is_active` / `archived_at`：MVP 先不支援軟刪除，避免不必要欄位；
  使用者刪 path 走 ON DELETE CASCADE 連動 units。
- 預留供 reflection (`source_type='learning_unit'`) 指向 — 已在 reflections schema
  中保留 source_type，本表 id 為 polymorphic target，無 FK 反向約束。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_LEARNING_UNIT_STATUSES = ("locked", "available", "in_progress", "completed")


def upgrade() -> None:
    # === learning_paths ===
    op.create_table(
        "learning_paths",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
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
    )
    op.create_index("ix_learning_paths_user_id", "learning_paths", ["user_id"])

    # === learning_units ===
    op.create_table(
        "learning_units",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "path_id",
            sa.UUID(),
            sa.ForeignKey("learning_paths.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "concept_id",
            sa.UUID(),
            sa.ForeignKey("concepts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="locked",
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "path_id", "order_index", name="uq_learning_units_path_order"
        ),
        sa.CheckConstraint(
            f"status IN {_LEARNING_UNIT_STATUSES}",
            name="ck_learning_units_status_enum",
        ),
        sa.CheckConstraint(
            "order_index >= 0", name="ck_learning_units_order_non_negative"
        ),
    )
    op.create_index("ix_learning_units_path_id", "learning_units", ["path_id"])
    op.create_index("ix_learning_units_concept_id", "learning_units", ["concept_id"])


def downgrade() -> None:
    op.drop_index("ix_learning_units_concept_id", table_name="learning_units")
    op.drop_index("ix_learning_units_path_id", table_name="learning_units")
    op.drop_table("learning_units")
    op.drop_index("ix_learning_paths_user_id", table_name="learning_paths")
    op.drop_table("learning_paths")
