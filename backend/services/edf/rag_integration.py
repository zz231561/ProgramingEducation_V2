"""EDF Feedback 層 ↔ RAG 檢索整合 helper。

職責：
- 把 EvidenceResult 轉成適合向量檢索的自然語言 query
- 安全包裝 `retrieve_chunks`：失敗回傳空 list，不阻擋教學回應

設計原則（CLAUDE.md「最小可用」）：
- RAG 是教學回應的「增強」而非「必要」— 任何錯誤都不該讓學生收不到回覆
"""

import logging

from services.edf.models import EvidenceResult
from services.rag import RetrievedChunk, retrieve_chunks

logger = logging.getLogger(__name__)

# 注入 prompt 的教材片段數 — 3 筆兼顧召回與 token 預算
RAG_TOP_K = 3


def build_rag_query(evidence: EvidenceResult) -> str:
    """從 Evidence 結果組裝 RAG 檢索 query。

    結合三類訊號讓 embedding 同時抓到關鍵字（concept tags）與語境（error / analysis）：
    error_message + concept_tags + code_analysis
    """
    parts: list[str] = []
    if evidence.error_message:
        parts.append(evidence.error_message)
    if evidence.concept_tags:
        parts.append(f"涉及概念：{', '.join(evidence.concept_tags)}")
    if evidence.code_analysis:
        parts.append(evidence.code_analysis)
    return ". ".join(parts) or "C++ 程式設計"


async def fetch_rag_chunks_safe(evidence: EvidenceResult) -> list[RetrievedChunk]:
    """安全地檢索教材片段。任何異常（網路、空索引、API key 失效）都吞掉並回傳空 list。"""
    try:
        return await retrieve_chunks(build_rag_query(evidence), top_k=RAG_TOP_K)
    except Exception as e:
        logger.warning("RAG retrieval failed, continuing without RAG: %r", e)
        return []
