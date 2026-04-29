"""enable pgvector extension and create documents table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-29 00:00:00.000000

對應 roadmap 2-1a：RAG 知識檢索基礎建設。
- 啟用 pgvector extension（LlamaIndex PGVectorStore 必要前置）
- 建立 documents 業務表：教材檔案 metadata（檔名、來源、上傳者、版本）
- chunks 與向量資料由 LlamaIndex IngestionPipeline 於 2-1b 自動建表，本 migration 不處理
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("uri", sa.String(1000), nullable=True),
        sa.Column(
            "uploader_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("doc_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_documents_source", "documents", ["source"])
    op.create_index("ix_documents_uploader_id", "documents", ["uploader_id"])


def downgrade() -> None:
    op.drop_index("ix_documents_uploader_id", table_name="documents")
    op.drop_index("ix_documents_source", table_name="documents")
    op.drop_table("documents")
    op.execute("DROP EXTENSION IF EXISTS vector")
