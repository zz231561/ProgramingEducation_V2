"""6-3c：questions.source 加入 'batch'（知識點批次預生成，LEARN 單元題組專用）。

設計意圖：LEARN 題組只列批次預生成題；QUIZ 弱項現生題（source='generated'）
繼續進大題庫但不進單元題組。以 CHECK constraint 更新支援新值。

Revision ID: k7f8a9b0c1d2
Revises: j6e7f8a9b0c1
"""

from typing import Sequence, Union

from alembic import op

revision: str = "k7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = "j6e7f8a9b0c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CONSTRAINT = "ck_questions_source_enum"


def upgrade() -> None:
    op.drop_constraint(_CONSTRAINT, "questions", type_="check")
    op.create_check_constraint(
        _CONSTRAINT,
        "questions",
        "source IN ('generated', 'batch', 'imported', 'leetcode')",
    )


def downgrade() -> None:
    op.drop_constraint(_CONSTRAINT, "questions", type_="check")
    op.create_check_constraint(
        _CONSTRAINT,
        "questions",
        "source IN ('generated', 'imported', 'leetcode')",
    )
