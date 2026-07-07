"""create assignments / submissions / attachments

Revision ID: q3f4a5b6c7d8
Revises: p2e3f4a5b6c7
Create Date: 2026-07-07 04:00:00.000000

對應 roadmap 5-5a-1 / db-schema.md §Module 8：TronClass 式文件繳交作業。

設計取捨：
- 附件內容存 bytea（LargeBinary）——Zeabur 容器檔案系統 ephemeral，存 DB 才不遺失。
- 單檔 ≤ 10MB（CHECK size_bytes <= 10485760，與 model MAX_ATTACHMENT_BYTES 一致）。
- attachments 多型（owner_type assignment/submission）無 FK cascade，刪除由 service 層顯式處理。
- submissions UNIQUE(assignment_id, student_id)：每生每作業一份，重繳覆蓋。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "q3f4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "p2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_MAX_BYTES = 10 * 1024 * 1024


def upgrade() -> None:
    op.create_table(
        "assignments",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "class_id", sa.UUID(),
            sa.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "teacher_id", sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
    )
    op.create_index("ix_assignments_class_id", "assignments", ["class_id"])

    op.create_table(
        "assignment_submissions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "assignment_id", sa.UUID(),
            sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "student_id", sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False, server_default=""),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=False, server_default=""),
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "submitted_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.UniqueConstraint(
            "assignment_id", "student_id", name="uq_submission_assignment_student"
        ),
        sa.CheckConstraint(
            "score IS NULL OR score >= 0", name="ck_submission_score_non_negative"
        ),
    )
    op.create_index(
        "ix_submissions_assignment_id", "assignment_submissions", ["assignment_id"]
    )
    op.create_index(
        "ix_submissions_student_id", "assignment_submissions", ["student_id"]
    )

    op.create_table(
        "attachments",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("owner_type", sa.String(20), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column(
            "uploaded_by", sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.CheckConstraint(
            "owner_type IN ('assignment', 'submission')",
            name="ck_attachments_owner_type_enum",
        ),
        sa.CheckConstraint(
            f"size_bytes >= 0 AND size_bytes <= {_MAX_BYTES}",
            name="ck_attachments_size_limit",
        ),
    )
    op.create_index(
        "ix_attachments_owner", "attachments", ["owner_type", "owner_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_attachments_owner", table_name="attachments")
    op.drop_table("attachments")
    op.drop_index("ix_submissions_student_id", table_name="assignment_submissions")
    op.drop_index("ix_submissions_assignment_id", table_name="assignment_submissions")
    op.drop_table("assignment_submissions")
    op.drop_index("ix_assignments_class_id", table_name="assignments")
    op.drop_table("assignments")
