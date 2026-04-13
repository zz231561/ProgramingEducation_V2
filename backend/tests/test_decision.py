"""Decision 層單元測試 — 驗證策略矩陣查表邏輯。"""

import pytest

from services.edf.decision import decide_strategy, TeachingStrategy
from services.edf.models import EvidenceResult, BloomLevel, ErrorType


def _make_evidence(bloom: int) -> EvidenceResult:
    """建立指定 Bloom 等級的 EvidenceResult。"""
    return EvidenceResult(
        error_type=ErrorType.LOGIC,
        error_message="test error",
        concept_tags=["control-flow"],
        bloom_level=bloom,
        bloom_reasoning="test",
        code_analysis="test analysis",
    )


# === 基本查表 ===

def test_low_bloom_low_hint():
    """Bloom 1 + Hint 0 → 提問引導，不給程式碼。"""
    result = decide_strategy(_make_evidence(1), hint_level=0)
    assert isinstance(result, TeachingStrategy)
    assert result.hint_level == 0
    assert result.allow_code_snippet is False
    assert result.use_rag is False


def test_low_bloom_high_hint():
    """Bloom 1 + Hint 5 → 完整解釋 + 程式碼。"""
    result = decide_strategy(_make_evidence(1), hint_level=5)
    assert result.allow_code_snippet is True
    assert result.hint_level == 5


def test_high_bloom_low_hint():
    """Bloom 6 + Hint 0 → 開放式提問。"""
    result = decide_strategy(_make_evidence(6), hint_level=0)
    assert result.allow_code_snippet is False
    assert result.use_rag is False


def test_high_bloom_high_hint():
    """Bloom 5 + Hint 3 → 允許程式碼 + 觸發 RAG。"""
    result = decide_strategy(_make_evidence(5), hint_level=3)
    assert result.allow_code_snippet is True
    assert result.use_rag is True


# === RAG 觸發條件 ===

def test_rag_triggered_analyze_hint2():
    """Bloom ANALYZE + Hint 2 → 觸發 RAG。"""
    result = decide_strategy(_make_evidence(BloomLevel.ANALYZE), hint_level=2)
    assert result.use_rag is True


def test_rag_not_triggered_apply_hint2():
    """Bloom APPLY + Hint 2 → 不觸發 RAG（Bloom 不夠高）。"""
    result = decide_strategy(_make_evidence(BloomLevel.APPLY), hint_level=2)
    assert result.use_rag is False


def test_rag_not_triggered_analyze_hint1():
    """Bloom ANALYZE + Hint 1 → 不觸發 RAG（hint 不夠高）。"""
    result = decide_strategy(_make_evidence(BloomLevel.ANALYZE), hint_level=1)
    assert result.use_rag is False


# === 邊界值 ===

def test_hint_clamped_below_zero():
    """hint_level < 0 → clamp 為 0。"""
    result = decide_strategy(_make_evidence(1), hint_level=-1)
    assert result.hint_level == 0


def test_hint_clamped_above_five():
    """hint_level > 5 → clamp 為 5。"""
    result = decide_strategy(_make_evidence(1), hint_level=10)
    assert result.hint_level == 5


# === 所有 36 格都有定義 ===

def test_all_matrix_cells_defined():
    """確認 6×6 = 36 個策略矩陣格子全部有對應結果。"""
    for bloom in range(1, 7):
        for hint in range(0, 6):
            result = decide_strategy(_make_evidence(bloom), hint_level=hint)
            assert result.instruction, f"({bloom}, {hint}) instruction is empty"
