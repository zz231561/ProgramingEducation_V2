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

# K4b：相關性門檻 — 只注入 cosine 分數達標的 chunks（取代原 hint/bloom 寫死觸發）。
# text-embedding-3-small 的相關 chunk 分數常落在 0.3-0.6 區間；
# 0.40 為初始值，K4d 真人驗收時依實際命中率調整。
RAG_MIN_SCORE = 0.40


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
    """安全地檢索教材片段，只回傳相關性達標的 chunks（K4b）。

    - 每次互動都檢索（embedding 成本可忽略），由分數決定是否注入 —
      「該查影片時就查」取代原 hint_level/bloom 門檻
    - 全部低於門檻 → 回空 list（prompt 不注入，Coddy 用自身知識回答）
    - 任何異常（網路、空索引、API key 失效）都吞掉並回傳空 list
    """
    try:
        chunks = await retrieve_chunks(build_rag_query(evidence), top_k=RAG_TOP_K)
    except Exception as e:
        logger.warning("RAG retrieval failed, continuing without RAG: %r", e)
        return []

    relevant = [c for c in chunks if c.score >= RAG_MIN_SCORE]
    if len(relevant) < len(chunks):
        logger.info(
            "RAG relevance filter: %d/%d chunks kept (min_score=%.2f)",
            len(relevant), len(chunks), RAG_MIN_SCORE,
        )
    return relevant
