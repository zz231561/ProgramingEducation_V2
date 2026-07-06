"""create coding_events table

Revision ID: o1d2e3f4a5b6
Revises: n0c1d2e3f4a5
Create Date: 2026-07-07 02:00:00.000000

對應 roadmap 5-2a / db-schema.md §Module 9：程式行為事件收集（ProgSnap2 schema）。

設計取捨：
- concept_tags / execution_result / event_metadata 用通用 JSON（非 PG ARRAY/JSONB），
  與 quiz/reflection 慣例一致以相容 SQLite 測試。
- event_type 用 String + CHECK（非 PG ENUM），避開 enum.value/.name 雙寫坑。
- session_id ON DELETE SET NULL：chat session 刪除時保留事件、僅清空關聯。
- (user_id, created_at) 複合索引供個人時序查詢（主要存取路徑）。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "o1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "n0c1d2e3f4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "coding_events",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.UUID(),
            sa.ForeignKey("chat_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("concept_tags", sa.JSON(), nullable=True),
        sa.Column("code_snapshot", sa.Text(), nullable=True),
        sa.Column("execution_result", sa.JSON(), nullable=True),
        sa.Column("hint_level", sa.SmallInteger(), nullable=True),
        sa.Column("event_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "event_type IN ('submit', 'compile_error', 'runtime_error', "
            "'success', 'hint_request', 'fix')",
            name="ck_coding_events_event_type_enum",
        ),
        sa.CheckConstraint(
            "hint_level IS NULL OR hint_level BETWEEN 0 AND 5",
            name="ck_coding_events_hint_level_range",
        ),
    )
    op.create_index(
        "ix_coding_events_user_created", "coding_events", ["user_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_coding_events_user_created", table_name="coding_events")
    op.drop_table("coding_events")
