"""add opened_name to code_files

Revision ID: s5b6c7d8e9f0
Revises: r4a5b6c7d8e9
Create Date: 2026-07-16 08:00:00.000000

U2e 回饋：重整/重新登入後 Workspace 應停留在最後開啟的命名檔案。
草稿列（name IS NULL）以 opened_name 記錄目前開啟的檔名；命名檔案列不使用此欄。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s5b6c7d8e9f0"
down_revision: Union[str, Sequence[str], None] = "r4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "code_files", sa.Column("opened_name", sa.String(100), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("code_files", "opened_name")
