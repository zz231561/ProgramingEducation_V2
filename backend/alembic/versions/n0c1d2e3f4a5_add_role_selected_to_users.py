"""add role_selected to users

Revision ID: n0c1d2e3f4a5
Revises: m9b0c1d2e3f4
Create Date: 2026-07-07 01:30:00.000000

對應 roadmap 5-1d-1：區分「使用者已在 onboarding 主動選擇身分」與「首登預設」。
現有列 server_default False → 既有帳號下次登入會被引導選擇身分（含測試者）。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "n0c1d2e3f4a5"
down_revision: Union[str, Sequence[str], None] = "m9b0c1d2e3f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role_selected",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "role_selected")
