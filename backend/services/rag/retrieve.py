"""RAG 檢索 service — 對 PGVectorStore 做向量相似度查詢。

設計原則（CLAUDE.md 守則 #7）：
- 直接用 LlamaIndex `VectorStoreIndex.from_vector_store` 包現有 pgvector 表
- 不重新 ingest，只查詢
- 回傳簡化過的 `RetrievedChunk`，避免 LlamaIndex 型別擴散到上層（EDF Feedback 層）

兩種檢索策略：
- `retrieve_chunks(query, top_k)`：語意相似度檢索（EDF Feedback / Quiz generate）
- `get_chunks_by_video_order(video_order)`：6-2b 用，依 video_order metadata 取出該影片
  完整字幕 chunks（按時間順序），不做語意排序
"""

from sqlalchemy import text as sa_text

from llama_index.core import VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from pydantic import BaseModel, Field

from core.config import settings
from core.database import async_session
from services.rag.pipeline import VECTOR_TABLE_NAME, build_vector_store


class RetrievedChunk(BaseModel):
    """RAG 檢索回傳的單筆 chunk。"""

    text: str = Field(..., description="chunk 純文字內容")
    score: float = Field(..., description="相似度分數（cosine，越高越相似）")
    doc_id: str | None = Field(None, description="來源 document UUID（ingest 時寫入 metadata）")
    metadata: dict = Field(default_factory=dict, description="完整 chunk metadata")


async def retrieve_chunks(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    """以自然語言 query 對向量庫做相似度檢索，回傳 top-k chunks。

    Args:
        query: 自然語言查詢字串（會被 embed 後與 chunks 比對 cosine 相似度）
        top_k: 回傳前 k 筆（預設 5）

    Returns:
        依相似度排序的 `RetrievedChunk` 列表（高 → 低）
    """
    embed_model = OpenAIEmbedding(
        model=settings.EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY,
    )
    index = VectorStoreIndex.from_vector_store(
        build_vector_store(),
        embed_model=embed_model,
    )
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = await retriever.aretrieve(query)

    return [
        RetrievedChunk(
            text=n.node.get_content(),
            score=n.score or 0.0,
            doc_id=n.node.metadata.get("doc_id"),
            metadata=dict(n.node.metadata),
        )
        for n in nodes
    ]


async def get_chunks_by_video_order(video_order: int) -> list[RetrievedChunk]:
    """取出指定 video_order 的所有字幕 chunks，依 start_time_seconds 由早到晚排序。

    Phase 6-2b 用：批次生成 unit content 時需要該 video 完整字幕（不是語意 top-k），
    避免跨 video 污染與順序錯亂。直接 SQL 查 `data_codedge_rag.metadata_` 而非
    走 LlamaIndex retriever — 不做 embedding，純 metadata filter。

    Args:
        video_order: 影片編號（concepts.video_order）

    Returns:
        該 video 全部 chunks（時間順序）；無資料時回 `[]`
    """
    actual_table = f"data_{VECTOR_TABLE_NAME}"
    async with async_session() as db:
        result = await db.execute(
            sa_text(
                f"""
                SELECT text, metadata_
                FROM {actual_table}
                WHERE (metadata_->>'video_order')::int = :order
                ORDER BY (metadata_->>'start_time_seconds')::float
                """  # noqa: S608
            ).bindparams(order=video_order)
        )
        rows = result.all()

    return [
        RetrievedChunk(
            text=row.text,
            score=1.0,  # 非語意檢索，分數僅佔位
            doc_id=row.metadata_.get("doc_id") if row.metadata_ else None,
            metadata=dict(row.metadata_ or {}),
        )
        for row in rows
    ]
