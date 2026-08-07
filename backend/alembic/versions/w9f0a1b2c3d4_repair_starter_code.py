"""repair non-compiling coding question starter code

Revision ID: w9f0a1b2c3d4
Revises: v8e9f0a1b2c3
Create Date: 2026-08-08
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from data_migrations.starter_code_newline_repairs import STARTER_CODE_NEWLINE_REPAIRS
from data_migrations.starter_code_runtime_repairs import STARTER_CODE_RUNTIME_REPAIRS
from data_migrations.starter_code_syntax_repairs import STARTER_CODE_SYNTAX_REPAIRS

revision: str = "w9f0a1b2c3d4"
down_revision: str | Sequence[str] | None = "v8e9f0a1b2c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UPDATE_STARTER_CODE = sa.text("""
    UPDATE questions
    SET content = jsonb_set(
        content::jsonb,
        '{starter_code}',
        to_jsonb(CAST(:code AS text))
    )::json
    WHERE id = CAST(:question_id AS uuid)
""")


def upgrade() -> None:
    connection = op.get_bind()
    repairs = (
        STARTER_CODE_SYNTAX_REPAIRS
        | STARTER_CODE_NEWLINE_REPAIRS
        | STARTER_CODE_RUNTIME_REPAIRS
    )
    for question_id, code in repairs.items():
        connection.execute(
            _UPDATE_STARTER_CODE,
            {"question_id": question_id, "code": code},
        )


def downgrade() -> None:
    # 舊 starter code 無法編譯，不恢復已知壞資料。
    pass
