"""add dialogue_act to chat_messages

Revision ID: p2e3f4a5b6c7
Revises: o1d2e3f4a5b6
Create Date: 2026-07-07 03:00:00.000000

對應 roadmap 5-2c / db-schema.md §Module 9：學生訊息對話行為分類（StudyChat schema）。

設計取捨：
- String(24) + CHECK（非 PG ENUM），與 coding_events.event_type 同款，避開 enum 雙寫坑。
- nullable：啟發式分類，訊號不足留 NULL；既有列一律 NULL（不回填）。
- 合法值＝StudyChat 6 類（asking_hint/clarification_request/debugging/off_topic/
  acknowledgment/verification）。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "p2e3f4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "o1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_messages",
        sa.Column("dialogue_act", sa.String(24), nullable=True),
    )
    op.create_check_constraint(
        "ck_chat_messages_dialogue_act_enum",
        "chat_messages",
        "dialogue_act IS NULL OR dialogue_act IN ("
        "'asking_hint', 'clarification_request', 'debugging', "
        "'off_topic', 'acknowledgment', 'verification')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_chat_messages_dialogue_act_enum",
        "chat_messages",
        type_="check",
    )
    op.drop_column("chat_messages", "dialogue_act")
