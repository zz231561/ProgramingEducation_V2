"""Decision 層單元測試 — 累積式揭露階梯 + 動態選層（7-C2a）。"""

import pytest

from services.edf.decision import (
    MAX_REVEAL_LEVEL,
    MIN_CODE_LEVEL,
    TeachingStrategy,
    base_level,
    decide_strategy,
)
from services.edf.models import BloomLevel, ErrorType, EvidenceResult


def _make_evidence(
    bloom: int = BloomLevel.APPLY,
    error_type: ErrorType = ErrorType.LOGIC,
) -> EvidenceResult:
    return EvidenceResult(
        error_type=error_type,
        error_message="test error",
        concept_tags=["control-flow"],
        bloom_level=bloom,
        bloom_reasoning="test",
        code_analysis="test analysis",
    )


# === 動態選層：base(error_type) ===

@pytest.mark.parametrize(
    "error_type,expected",
    [
        (ErrorType.NONE, 0),      # 純提問／程式正確：不揭露本題解法
        (ErrorType.SYNTAX, 2),    # 看不懂錯誤訊息，指出位置不算給答案
        (ErrorType.COMPILATION, 2),
        (ErrorType.RUNTIME, 2),
        (ErrorType.LOGIC, 1),     # 找出邏輯錯在哪本身就是練習
        (ErrorType.SEMANTIC, 1),
    ],
)
def test_base_level_by_error_type(error_type: ErrorType, expected: int):
    assert base_level(error_type) == expected
    assert decide_strategy(_make_evidence(error_type=error_type)).reveal_level == expected


def test_need_raises_reveal_level():
    """需求量直接加在 base 之上。"""
    ev = _make_evidence(error_type=ErrorType.LOGIC)  # base 1
    assert decide_strategy(ev, need=0).reveal_level == 1
    assert decide_strategy(ev, need=2).reveal_level == 3


def test_reveal_level_capped_at_max():
    ev = _make_evidence(error_type=ErrorType.RUNTIME)  # base 2
    assert decide_strategy(ev, need=99).reveal_level == MAX_REVEAL_LEVEL


def test_negative_need_treated_as_zero():
    ev = _make_evidence(error_type=ErrorType.NONE)
    assert decide_strategy(ev, need=-3).reveal_level == 0


# === 累積式指令 ===

def test_instruction_is_cumulative():
    """L3 的指令必須含 L0-L3 全部行為，不是只有第 3 級那一句。"""
    ev = _make_evidence(error_type=ErrorType.NONE)
    result = decide_strategy(ev, need=3)
    assert isinstance(result, TeachingStrategy)
    for level in range(4):
        assert f"L{level}：" in result.instruction
    assert "L4：" not in result.instruction


def test_level_zero_instruction_has_no_reveal():
    result = decide_strategy(_make_evidence(error_type=ErrorType.NONE))
    assert "L0：" in result.instruction
    assert "L1：" not in result.instruction


# === 程式碼片段閘門 ===

@pytest.mark.parametrize("need,allowed", [(0, False), (1, False), (2, False), (3, True), (5, True)])
def test_allow_code_snippet_gate(need: int, allowed: bool):
    """L3（給骨架）起才允許程式碼片段。"""
    ev = _make_evidence(error_type=ErrorType.NONE)  # base 0 → reveal == need
    result = decide_strategy(ev, need=need)
    assert result.allow_code_snippet is allowed
    assert (result.reveal_level >= MIN_CODE_LEVEL) is allowed


# === Bloom 深度修飾（與等級正交）===

def test_every_bloom_level_has_guidance():
    for bloom in BloomLevel:
        result = decide_strategy(_make_evidence(bloom=bloom))
        assert result.bloom_guidance, f"bloom {bloom} 沒有深度修飾"


def test_bloom_does_not_affect_reveal_level():
    """Bloom 只管講多深，不管揭露多少。"""
    levels = {
        decide_strategy(_make_evidence(bloom=b, error_type=ErrorType.LOGIC), 2).reveal_level
        for b in BloomLevel
    }
    assert levels == {3}


def test_strategy_has_no_use_rag_field():
    """K4b：RAG 注入改由 Feedback 層依分數決定，策略不再帶 use_rag。"""
    assert not hasattr(decide_strategy(_make_evidence()), "use_rag")


def test_strategy_has_no_hint_level_field():
    """7-C2a：hint_level 是 Quiz 的語意（學生按了幾次提示鈕），chat 端不再有。"""
    assert not hasattr(decide_strategy(_make_evidence()), "hint_level")
