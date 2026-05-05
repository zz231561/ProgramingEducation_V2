"""add comprehension columns to student_answers

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-05-05 00:00:00.000000

對應 roadmap 2-6a：Post-Solution Comprehension Check 持久化欄位（Module 6 擴充）。

設計取捨：
- 4 欄位皆 nullable：comprehension 為「解題後選擇性驗證」，多數 student_answers
  不會觸發；nullable 比另開 1:1 表更省 join。
- `comprehension_type` 用 String + CHECK：與 quiz.type / source 慣例一致，避開 PG ENUM
  的 enum.value/.name 雙重寫法 + SQLite 測試相容。
- 不加 `comprehension_completed_at`：`answered_at` 與 comprehension 邏輯解耦，
  動態觸發頻率（2-6e）需要時再 migrate，遵守「不加沒被要求的欄位」。
- CHECK 改用 `comprehension_type IS NULL OR ...`：允許 NULL 同時限制合法值。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_COMPREHENSION_TYPES = ("epl", "predict_output", "variation")


def upgrade() -> None:
    op.add_column(
        "student_answers",
        sa.Column("comprehension_type", sa.String(20), nullable=True),
    )
    op.add_column(
        "student_answers",
        sa.Column("comprehension_prompt", sa.Text(), nullable=True),
    )
    op.add_column(
        "student_answers",
        sa.Column("comprehension_answer", sa.Text(), nullable=True),
    )
    op.add_column(
        "student_answers",
        sa.Column("comprehension_passed", sa.Boolean(), nullable=True),
    )
    op.create_check_constraint(
        "ck_student_answers_comprehension_type_enum",
        "student_answers",
        f"comprehension_type IS NULL OR comprehension_type IN {_COMPREHENSION_TYPES}",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_student_answers_comprehension_type_enum",
        "student_answers",
        type_="check",
    )
    op.drop_column("student_answers", "comprehension_passed")
    op.drop_column("student_answers", "comprehension_answer")
    op.drop_column("student_answers", "comprehension_prompt")
    op.drop_column("student_answers", "comprehension_type")
