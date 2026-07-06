"""create student_profiles table

Revision ID: m9b0c1d2e3f4
Revises: l8a9b0c1d2e3
Create Date: 2026-07-07 00:30:00.000000

對應 roadmap 5-1b-1 / db-schema.md §Module 8：學生身分補填（校名/系所/學號/姓名）。

設計取捨：
- 1:1 對應 users：`user_id` 直接當主鍵，天然保證每位學生至多一份 profile，
  不另設 UNIQUE。
- 學號不設 unique（使用者決策）：校名可能跨校，全系統唯一會誤擋跨校撞號。
- email 沿用 `users.email`，不在此表重複。
- `updated_at` 用 onupdate=now()：學生日後可更正資料。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "m9b0c1d2e3f4"
down_revision: Union[str, Sequence[str], None] = "l8a9b0c1d2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "student_profiles",
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("school", sa.String(100), nullable=False),
        sa.Column("department", sa.String(100), nullable=False),
        sa.Column("student_id", sa.String(50), nullable=False),
        sa.Column("real_name", sa.String(100), nullable=False),
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


def downgrade() -> None:
    op.drop_table("student_profiles")
