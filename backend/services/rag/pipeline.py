"""LlamaIndex IngestionPipeline 配置 — chunking + OpenAI embedding + PGVectorStore。

設計原則（CLAUDE.md 守則 #7）：
- 不自寫 chunking / embedding，全部交給 LlamaIndex
- chunk_size / overlap 採用 LlamaIndex 推薦預設（適合教學文本）
- pgvector 表由 PGVectorStore 自動建立，無需 Alembic migration
"""

from urllib.parse import urlparse

from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore

from core.config import settings

# OpenAI text-embedding-3-small 的向量維度
EMBEDDING_DIM = 1536

# pgvector 表名 — LlamaIndex 會自動 prepend "data_" → 實際表為 "data_codedge_rag"
VECTOR_TABLE_NAME = "codedge_rag"

# Chunking 參數 — 512 tokens 對程式教學段落剛好（一段 1-2 個概念）
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64


def _build_vector_store() -> PGVectorStore:
    """從 DATABASE_URL 解析 pg 連線參數並建立 PGVectorStore。

    DATABASE_URL 含 `+asyncpg` driver suffix（給 SQLAlchemy 用），
    這裡需要拆解成乾淨的 host/port/user/password/database 給 LlamaIndex。
    """
    parsed = urlparse(settings.DATABASE_URL)
    return PGVectorStore.from_params(
        host=parsed.hostname or "localhost",
        port=parsed.port or 5432,
        database=(parsed.path or "/").lstrip("/"),
        user=parsed.username or "",
        password=parsed.password or "",
        table_name=VECTOR_TABLE_NAME,
        embed_dim=EMBEDDING_DIM,
    )


def get_ingestion_pipeline() -> IngestionPipeline:
    """回傳設定好的 IngestionPipeline（chunking → embedding → 寫入向量表）。

    Lazy 建構：每次呼叫產生新 instance，避免 import 時建立連線。
    """
    embed_model = OpenAIEmbedding(
        model=settings.EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY,
    )
    return IngestionPipeline(
        transformations=[
            SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP),
            embed_model,
        ],
        vector_store=_build_vector_store(),
    )
