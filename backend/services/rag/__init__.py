"""RAG 知識檢索 service — LlamaIndex IngestionPipeline + PGVectorStore。"""

from services.rag.ingest import ingest_document
from services.rag.pipeline import (
    EMBEDDING_DIM,
    VECTOR_TABLE_NAME,
    build_vector_store,
    get_ingestion_pipeline,
)
from services.rag.retrieve import RetrievedChunk, retrieve_chunks

__all__ = [
    "EMBEDDING_DIM",
    "VECTOR_TABLE_NAME",
    "RetrievedChunk",
    "build_vector_store",
    "get_ingestion_pipeline",
    "ingest_document",
    "retrieve_chunks",
]
