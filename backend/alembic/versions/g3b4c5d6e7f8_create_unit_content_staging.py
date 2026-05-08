"""create unit_content_staging table

Revision ID: g3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-05-08 00:00:00.000000

Phase 6-2b：unit content 批次生成的中介存放區。

設計：
- 1 row 對應 1 concept（UNIQUE(concept_id)）。Learning_units 是 per-user 多對 concept 的 row；
  教材內容 grounded 在 video，與用戶無關 → 1 concept 1 staging。
- `content` JSON shape = `services.learning.content_generator.UnitContent`
  (concept_explanation / code_examples / summary 三 section)。
- `status` (pending/approved/rejected)：6-4 教授抽查介面用；approved 後 promote 到
  `learning_units.content`。
- `needs_more_source` Bool：3 section 任一 needs_more_source=true 即標 true，方便 6-4 篩選。
- `notes`：彙整 LLM 各 section 的 reason 字串，給審查者一眼看出缺什麼。
- `attempt_count` / `model_used`：tracked 給 6-4 抽查時判斷是否需重生。

idempotency：concept_id UNIQUE → 重跑 batch 用 ON CONFLICT 更新（caller 處理）。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g3b4c5d6e7f8"
down_revision: Union[str, Sequence[str], None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STAGING_STATUSES = ("pending", "approved", "rejected")


def upgrade() -> None:
    op.create_table(
        "unit_content_staging",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "concept_id",
            sa.UUID(),
            sa.ForeignKey("concepts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "needs_more_source",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "attempt_count", sa.Integer(), nullable=False, server_default="1"
        ),
        sa.Column("model_used", sa.String(50), nullable=False, server_default=""),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("concept_id", name="uq_unit_content_staging_concept"),
        sa.CheckConstraint(
            f"status IN {_STAGING_STATUSES}",
            name="ck_unit_content_staging_status_enum",
        ),
        sa.CheckConstraint(
            "attempt_count >= 1", name="ck_unit_content_staging_attempt_positive"
        ),
    )
    op.create_index(
        "ix_unit_content_staging_status", "unit_content_staging", ["status"]
    )
    op.create_index(
        "ix_unit_content_staging_needs_more_source",
        "unit_content_staging",
        ["needs_more_source"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_unit_content_staging_needs_more_source",
        table_name="unit_content_staging",
    )
    op.drop_index(
        "ix_unit_content_staging_status", table_name="unit_content_staging"
    )
    op.drop_table("unit_content_staging")
