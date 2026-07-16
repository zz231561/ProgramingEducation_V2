"""create code_files

Revision ID: r4a5b6c7d8e9
Revises: q3f4a5b6c7d8
Create Date: 2026-07-16 00:00:00.000000

對應 roadmap U2e：Workspace 程式碼存檔（自動草稿 + 命名檔案）。

設計取捨：
- 單表兩用：`name IS NULL` 為自動草稿（每人一份，partial unique index 保證）；
  有 name 為命名檔案（UNIQUE(user_id, name)，同名儲存＝覆蓋 upsert）。
- code 長度上限 100_000 字元（CHECK，與 model MAX_CODE_CHARS 一致），
  防單筆灌爆；每人命名檔案數量上限由 service 層把關（DB 不易表達）。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "r4a5b6c7d8e9"
down_revision: Union[str, Sequence[str], None] = "q3f4a5b6c7d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_MAX_CODE_CHARS = 100_000


def upgrade() -> None:
    op.create_table(
        "code_files",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id", sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("code", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.UniqueConstraint("user_id", "name", name="uq_code_files_user_name"),
        sa.CheckConstraint(
            f"char_length(code) <= {_MAX_CODE_CHARS}",
            name="ck_code_files_code_len",
        ),
    )
    # 草稿（name IS NULL）每人至多一份
    op.create_index(
        "uq_code_files_draft",
        "code_files",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("name IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_code_files_draft", table_name="code_files")
    op.drop_table("code_files")
