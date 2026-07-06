"""create classes and class_members tables

Revision ID: l8a9b0c1d2e3
Revises: k7f8a9b0c1d2
Create Date: 2026-07-07 00:00:00.000000

對應 roadmap 5-1a / db-schema.md §Module 8：教師端班級管理資料基礎。

設計取捨：
- `teacher_id` / `user_id` 皆 ON DELETE CASCADE：教師刪除連帶清班級，
  學生刪除連帶清成員關聯，避免孤兒 row。
- `invite_code` 長度 12、unique + index：學生以短碼加入；產生與碰撞重試
  屬 API 層（5-1b），migration 只保證唯一性。
- `class_members` 用複合主鍵 (class_id, user_id)：一位學生同班只能一筆，
  天然去重，不另設 UNIQUE。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "l8a9b0c1d2e3"
down_revision: Union[str, Sequence[str], None] = "k7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "classes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column(
            "teacher_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("invite_code", sa.String(12), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("invite_code", name="uq_classes_invite_code"),
    )
    op.create_index("ix_classes_invite_code", "classes", ["invite_code"])
    op.create_index("ix_classes_teacher_id", "classes", ["teacher_id"])

    op.create_table(
        "class_members",
        sa.Column(
            "class_id",
            sa.UUID(),
            sa.ForeignKey("classes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_class_members_user_id", "class_members", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_class_members_user_id", table_name="class_members")
    op.drop_table("class_members")
    op.drop_index("ix_classes_teacher_id", table_name="classes")
    op.drop_index("ix_classes_invite_code", table_name="classes")
    op.drop_table("classes")
