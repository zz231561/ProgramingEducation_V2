"""EDF ↔ RAG 整合 helper 單元測試。

關鍵保證：
- query 組裝邏輯正確（concept tags + error_message + code_analysis）
- `fetch_rag_chunks_safe` 對任何異常回傳空 list（不阻擋教學回應）
"""

from unittest.mock import AsyncMock, patch

import pytest

from services.edf.models import BloomLevel, ErrorType, EvidenceResult
from services.edf.rag_integration import (
    RAG_TOP_K,
    build_rag_query,
    fetch_rag_chunks_safe,
)
from services.rag import RetrievedChunk


def _evidence(
    error_message: str = "",
    concept_tags: list[str] | None = None,
    code_analysis: str = "",
) -> EvidenceResult:
    return EvidenceResult(
        error_type=ErrorType.LOGIC,
        error_message=error_message,
        concept_tags=concept_tags or [],
        bloom_level=BloomLevel.ANALYZE,
        bloom_reasoning="",
        code_analysis=code_analysis,
    )


# === build_rag_query ===

def test_build_rag_query_combines_all_fields():
    q = build_rag_query(
        _evidence(
            error_message="無窮迴圈",
            concept_tags=["control-flow", "syntax-basic"],
            code_analysis="while 條件永遠為真",
        )
    )
    assert "無窮迴圈" in q
    assert "control-flow" in q
    assert "syntax-basic" in q
    assert "while 條件永遠為真" in q


def test_build_rag_query_skips_empty_fields():
    q = build_rag_query(_evidence(error_message="只有錯誤訊息"))
    assert q == "只有錯誤訊息"


def test_build_rag_query_fallback_when_all_empty():
    q = build_rag_query(_evidence())
    # 完全空的 evidence 應有 fallback 避免 embed 空字串
    assert q


# === fetch_rag_chunks_safe ===

@pytest.mark.asyncio
async def test_fetch_rag_chunks_safe_success_passes_through():
    chunks = [RetrievedChunk(text="教材片段", score=0.9, doc_id="d1", metadata={})]
    with patch(
        "services.edf.rag_integration.retrieve_chunks",
        AsyncMock(return_value=chunks),
    ) as mock:
        result = await fetch_rag_chunks_safe(_evidence(error_message="x"))

    assert result == chunks
    # top_k 應使用模組常數
    assert mock.call_args.kwargs["top_k"] == RAG_TOP_K


@pytest.mark.asyncio
async def test_fetch_rag_chunks_safe_swallows_exceptions():
    """任何異常都應被吞掉，回傳空 list — RAG 失敗不可阻擋教學回應。"""
    with patch(
        "services.edf.rag_integration.retrieve_chunks",
        AsyncMock(side_effect=RuntimeError("DB connection lost")),
    ):
        result = await fetch_rag_chunks_safe(_evidence(error_message="x"))

    assert result == []


# === K4b：相關性分數過濾 ===

@pytest.mark.asyncio
async def test_fetch_filters_low_score_chunks():
    """低於 RAG_MIN_SCORE 的 chunks 應被過濾。"""
    from services.edf.rag_integration import RAG_MIN_SCORE

    chunks = [
        RetrievedChunk(text="高相關", score=RAG_MIN_SCORE + 0.2, doc_id=None, metadata={}),
        RetrievedChunk(text="低相關", score=RAG_MIN_SCORE - 0.2, doc_id=None, metadata={}),
    ]
    with patch(
        "services.edf.rag_integration.retrieve_chunks",
        new_callable=AsyncMock,
        return_value=chunks,
    ):
        result = await fetch_rag_chunks_safe(_evidence(error_message="x"))

    assert [c.text for c in result] == ["高相關"]


@pytest.mark.asyncio
async def test_fetch_returns_empty_when_all_below_threshold():
    """全部低於門檻 → 空 list（prompt 不注入）。"""
    from services.edf.rag_integration import RAG_MIN_SCORE

    chunks = [
        RetrievedChunk(text="a", score=RAG_MIN_SCORE - 0.01, doc_id=None, metadata={}),
    ]
    with patch(
        "services.edf.rag_integration.retrieve_chunks",
        new_callable=AsyncMock,
        return_value=chunks,
    ):
        result = await fetch_rag_chunks_safe(_evidence(error_message="x"))

    assert result == []
