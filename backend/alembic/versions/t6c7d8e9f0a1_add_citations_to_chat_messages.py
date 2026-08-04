"""add citations to chat_messages

學生要能當場核對 Coddy 引用的教材出處（防幻覺第三層）。引用資料必須隨訊息一起
持久化，否則重新開啟對話時 citation 就消失，可驗證性只存在於當次回應。

不塞進既有的 `evidence` 欄位：那是 EDF Evidence 層的輸出，語意不同。

Revision ID: t6c7d8e9f0a1
Revises: s5b6c7d8e9f0
Create Date: 2026-08-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "t6c7d8e9f0a1"
down_revision: Union[str, Sequence[str], None] = "s5b6c7d8e9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chat_messages", sa.Column("citations", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("chat_messages", "citations")
