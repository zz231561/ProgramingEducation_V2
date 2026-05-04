"""create student_mastery table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-04 00:00:00.000000

對應 roadmap 2-3a：精熟度追蹤基礎 schema（Module 5 部分）。
- 每個 (user, concept) 一筆 mastery 記錄
- confidence 0-1 由 pyBKT 在 2-3b 維護；exposure/success/error 計數由 EDF Pipeline 累加
- bloom_level 紀錄學生在此概念曾達到的最高認知層級（IntEnum 1-6 對應 services/edf/models.py BloomLevel）
- 不存 created_at（last_practiced_at 已足夠）；seed 為 0 筆，rows 在學生互動時 lazy 建立
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "student_mastery",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "concept_id",
            sa.UUID(),
            sa.ForeignKey("concepts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "confidence",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "exposure_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "success_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "error_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        # bloom_level 用 SmallInteger + CHECK 1-6，與 services/edf/models.py BloomLevel(IntEnum) 對齊。
        # 不用 PG ENUM 避免再踩 enum.value/.name 同款坑；初次互動前可為 NULL。
        sa.Column("bloom_level", sa.SmallInteger(), nullable=True),
        sa.Column(
            "last_practiced_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "user_id", "concept_id", name="uq_student_mastery_user_concept"
        ),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1", name="ck_student_mastery_confidence_range"
        ),
        sa.CheckConstraint(
            "bloom_level IS NULL OR bloom_level BETWEEN 1 AND 6",
            name="ck_student_mastery_bloom_range",
        ),
        sa.CheckConstraint(
            "exposure_count >= 0 AND success_count >= 0 AND error_count >= 0",
            name="ck_student_mastery_counts_non_negative",
        ),
    )
    op.create_index("ix_student_mastery_user_id", "student_mastery", ["user_id"])
    op.create_index("ix_student_mastery_concept_id", "student_mastery", ["concept_id"])


def downgrade() -> None:
    op.drop_index("ix_student_mastery_concept_id", table_name="student_mastery")
    op.drop_index("ix_student_mastery_user_id", table_name="student_mastery")
    op.drop_table("student_mastery")
