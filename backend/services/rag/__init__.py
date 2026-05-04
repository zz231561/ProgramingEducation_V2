"""RAG 知識檢索 service — LlamaIndex IngestionPipeline + PGVectorStore。"""

from services.rag.ingest import ingest_document
from services.rag.pipeline import (
    EMBEDDING_DIM,
    VECTOR_TABLE_NAME,
    get_ingestion_pipeline,
)

__all__ = [
    "EMBEDDING_DIM",
    "VECTOR_TABLE_NAME",
    "get_ingestion_pipeline",
    "ingest_document",
]
