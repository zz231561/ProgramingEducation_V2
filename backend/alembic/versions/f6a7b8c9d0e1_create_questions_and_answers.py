"""create questions + student_answers tables

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-04 00:00:00.000000

對應 roadmap 2-4a：智慧出題基礎 schema（Module 6）。

設計取捨：
- enum 類欄位（type / source / bloom_level）改用 `String + CHECK` 或 `SmallInteger + CHECK`，
  不用 PG ENUM。理由：先前 user_role / message_role / concept_edge_type 三次踩過
  enum.value vs enum.name 的坑，且 SQLite 測試需要相容。
- `concept_tags` 用 JSON（list of strings）而非 PG `text[]`：避免 PG-only 型別讓 SQLite 測試壞；
  目前題庫規模 < 1000，全表掃可接受；未來若需要 GIN index 再 migrate。
- `content` / `answer` 用 JSON：題幹/選項/答案的形狀依 type 不同（multiple_choice / fill_blank /
  coding），JSON 容納各形狀；application 層驗證 shape（2-4d）。
- Post-Solution Comprehension（2-6）的擴充欄位（comprehension_*）留給後續 migration，本次不加。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 合法值 — 建表時用 CHECK 保證；ORM 層也定義一致的字串列舉
_QUESTION_TYPES = ("multiple_choice", "fill_blank", "coding")
_QUESTION_SOURCES = ("generated", "imported", "leetcode")


def upgrade() -> None:
    # === questions ===
    op.create_table(
        "questions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("type", sa.String(20), nullable=False),
        # concept_tags：JSON list of strings（不用 PG ARRAY 確保 SQLite 測試相容）
        sa.Column("concept_tags", sa.JSON(), nullable=False),
        sa.Column("bloom_level", sa.SmallInteger(), nullable=False),
        sa.Column("difficulty", sa.SmallInteger(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False, server_default=""),
        sa.Column("source", sa.String(20), nullable=False, server_default="generated"),
        sa.Column("validated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            f"type IN {_QUESTION_TYPES}", name="ck_questions_type_enum"
        ),
        sa.CheckConstraint(
            f"source IN {_QUESTION_SOURCES}", name="ck_questions_source_enum"
        ),
        sa.CheckConstraint(
            "bloom_level BETWEEN 1 AND 6", name="ck_questions_bloom_range"
        ),
        sa.CheckConstraint(
            "difficulty BETWEEN 1 AND 5", name="ck_questions_difficulty_range"
        ),
    )
    op.create_index("ix_questions_type", "questions", ["type"])
    op.create_index("ix_questions_bloom_level", "questions", ["bloom_level"])
    op.create_index("ix_questions_difficulty", "questions", ["difficulty"])

    # === student_answers ===
    op.create_table(
        "student_answers",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.UUID(),
            sa.ForeignKey("questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("answer", sa.JSON(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=True),
        sa.Column("hint_level_used", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("feedback", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "answered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "hint_level_used BETWEEN 0 AND 5",
            name="ck_student_answers_hint_range",
        ),
        sa.CheckConstraint(
            "time_spent_seconds IS NULL OR time_spent_seconds >= 0",
            name="ck_student_answers_time_non_negative",
        ),
    )
    op.create_index(
        "ix_student_answers_user_answered",
        "student_answers",
        ["user_id", "answered_at"],
    )
    op.create_index("ix_student_answers_question", "student_answers", ["question_id"])


def downgrade() -> None:
    op.drop_index("ix_student_answers_question", table_name="student_answers")
    op.drop_index("ix_student_answers_user_answered", table_name="student_answers")
    op.drop_table("student_answers")
    op.drop_index("ix_questions_difficulty", table_name="questions")
    op.drop_index("ix_questions_bloom_level", table_name="questions")
    op.drop_index("ix_questions_type", table_name="questions")
    op.drop_table("questions")
