"""教材 ingest 介面：文字 → IngestionPipeline → 寫入向量表 + 更新 documents.indexed_at。"""

from uuid import UUID

from llama_index.core import Document
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from services.rag.pipeline import get_ingestion_pipeline


async def ingest_document(
    db: AsyncSession,
    doc_id: UUID,
    text: str,
    metadata: dict | None = None,
) -> int:
    """將教材文字餵入 IngestionPipeline，回傳產出的 chunk 數。

    流程：Document → SentenceSplitter → OpenAIEmbedding → PGVectorStore。
    成功後更新 documents.indexed_at = NOW()。

    Args:
        db: SQLAlchemy async session（用於更新 documents.indexed_at）
        doc_id: documents 表的 PK，會寫入向量表 metadata 供回查
        text: 教材純文字內容
        metadata: 額外 metadata（會合併進 chunk node 的 metadata）

    Returns:
        產出並寫入向量表的 chunk node 數量
    """
    pipeline = get_ingestion_pipeline()
    doc = Document(
        text=text,
        metadata={"doc_id": str(doc_id), **(metadata or {})},
    )
    nodes = await pipeline.arun(documents=[doc])

    await db.execute(
        sa_text("UPDATE documents SET indexed_at = NOW() WHERE id = :doc_id").bindparams(
            doc_id=doc_id
        )
    )
    await db.commit()
    return len(nodes)
