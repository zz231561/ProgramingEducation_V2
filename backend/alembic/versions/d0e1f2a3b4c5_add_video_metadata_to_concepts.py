"""add video metadata columns to concepts

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-05-05 00:00:00.000000

對應策略：教授提供 62 部 C++ YT 影片 → 每影片對應 1 個 concept node。
本 migration 只加欄位（純 schema），不動資料。資料替換見下個 migration `e1f2a3b4c5d6`。

設計取捨：
- 3 欄位皆 nullable：existing concept 沒有影片資料 → 不擋；新 seed 的 59 影片 concept
  會填齊（除 youtube_id 等使用者/教授後續補）
- `video_order > 0` CHECK：保證編號合理；nullable 兼容無影片的 concept
- `video_duration_seconds > 0` CHECK：防呆
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, Sequence[str], None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "concepts",
        sa.Column("video_youtube_id", sa.String(20), nullable=True),
    )
    op.add_column(
        "concepts",
        sa.Column("video_duration_seconds", sa.Integer(), nullable=True),
    )
    op.add_column(
        "concepts",
        sa.Column("video_order", sa.Integer(), nullable=True),
    )
    op.create_check_constraint(
        "ck_concepts_video_duration_positive",
        "concepts",
        "video_duration_seconds IS NULL OR video_duration_seconds > 0",
    )
    op.create_check_constraint(
        "ck_concepts_video_order_positive",
        "concepts",
        "video_order IS NULL OR video_order > 0",
    )
    op.create_index("ix_concepts_video_order", "concepts", ["video_order"])


def downgrade() -> None:
    op.drop_index("ix_concepts_video_order", table_name="concepts")
    op.drop_constraint(
        "ck_concepts_video_order_positive", "concepts", type_="check"
    )
    op.drop_constraint(
        "ck_concepts_video_duration_positive", "concepts", type_="check"
    )
    op.drop_column("concepts", "video_order")
    op.drop_column("concepts", "video_duration_seconds")
    op.drop_column("concepts", "video_youtube_id")
