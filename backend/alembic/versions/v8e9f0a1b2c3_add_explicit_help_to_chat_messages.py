"""add explicit_help to chat_messages

「我卡住了」按鈕（7-C2a'）：學生自己按下的求助是 need 狀態機最可信的訊號，
但它是純前端事件——後端無從從文字推論（「這個怎麼寫」不等於按了求助鈕）。

不借用 `dialogue_act`：那欄的 `asking_hint` 也會由關鍵字啟發式產生，
重放歷史時會把普通提問誤讀成按鈕，need 因此被追溯性灌高。

Revision ID: v8e9f0a1b2c3
Revises: u7d8e9f0a1b2
Create Date: 2026-08-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "v8e9f0a1b2c3"
down_revision: Union[str, Sequence[str], None] = "u7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_messages",
        sa.Column(
            "explicit_help",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("chat_messages", "explicit_help")
