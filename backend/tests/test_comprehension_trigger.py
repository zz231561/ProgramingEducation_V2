"""Trigger 決策邏輯 unit tests。

涵蓋純規則 _decide()：cold start / 高 / 中高 / 中 / 低 pass_rate；coding vs 非 coding fallback。
"""

from models.quiz import ComprehensionType
from services.comprehension.trigger import (
    HIGH_PASS_THRESHOLD,
    MID_HIGH_PASS_THRESHOLD,
    MID_LOW_PASS_THRESHOLD,
    MIN_SAMPLES_TO_SKIP,
    _decide,
)


def test_cold_start_triggers_epl():
    should, t, reason = _decide(pass_rate=None, is_coding=True)
    assert should is True
    assert t == ComprehensionType.EPL
    assert "cold start" in reason


def test_cold_start_non_coding_also_epl():
    should, t, _ = _decide(pass_rate=None, is_coding=False)
    assert should is True
    assert t == ComprehensionType.EPL


def test_high_pass_rate_skips():
    should, t, reason = _decide(pass_rate=0.9, is_coding=True, sample_size=5)
    assert should is False
    assert t is None
    assert "跳過" in reason


def test_high_pass_rate_at_threshold_skips():
    should, t, _ = _decide(
        pass_rate=HIGH_PASS_THRESHOLD, is_coding=True, sample_size=MIN_SAMPLES_TO_SKIP
    )
    assert should is False
    assert t is None


def test_single_pass_does_not_switch_the_mechanism_off():
    """7-C4 實測的吸收態：1 筆通過 → 100% → 永不再驗 → 樣本永遠停在 1 筆。

    樣本不足時不得走「跳過」分支，否則整個 comprehension 對該學生只會啟動一次。
    """
    should, t, _ = _decide(pass_rate=1.0, is_coding=True, sample_size=1)
    assert should is True
    assert t is not None


def test_skip_requires_minimum_samples():
    for n in range(MIN_SAMPLES_TO_SKIP):
        should, _, _ = _decide(pass_rate=1.0, is_coding=True, sample_size=n)
        assert should is True, f"樣本 {n} 筆就跳過＝樣本不足也敢下結論"
    should, _, _ = _decide(pass_rate=1.0, is_coding=True, sample_size=MIN_SAMPLES_TO_SKIP)
    assert should is False


def test_mid_high_coding_picks_variation():
    should, t, reason = _decide(pass_rate=0.7, is_coding=True)
    assert should is True
    assert t == ComprehensionType.VARIATION
    assert "挑戰升級" in reason


def test_mid_high_non_coding_falls_back_to_epl():
    """非 coding 題型 → VARIATION 不適用 → fallback EPL。"""
    should, t, reason = _decide(pass_rate=0.7, is_coding=False)
    assert should is True
    assert t == ComprehensionType.EPL
    assert "fallback EPL" in reason


def test_mid_high_at_threshold_picks_variation():
    should, t, _ = _decide(pass_rate=MID_HIGH_PASS_THRESHOLD, is_coding=True)
    assert should is True
    assert t == ComprehensionType.VARIATION


def test_mid_coding_picks_predict_output():
    should, t, reason = _decide(pass_rate=0.45, is_coding=True)
    assert should is True
    assert t == ComprehensionType.PREDICT_OUTPUT
    assert "驗證" in reason


def test_mid_non_coding_falls_back_to_epl():
    should, t, reason = _decide(pass_rate=0.45, is_coding=False)
    assert should is True
    assert t == ComprehensionType.EPL
    assert "fallback EPL" in reason


def test_mid_at_lower_threshold_picks_predict_output():
    should, t, _ = _decide(pass_rate=MID_LOW_PASS_THRESHOLD, is_coding=True)
    assert should is True
    assert t == ComprehensionType.PREDICT_OUTPUT


def test_low_pass_rate_picks_epl():
    should, t, reason = _decide(pass_rate=0.1, is_coding=True)
    assert should is True
    assert t == ComprehensionType.EPL
    assert "回基礎" in reason


def test_low_pass_rate_non_coding_picks_epl():
    """低通過率時不論題型都選 EPL。"""
    should, t, _ = _decide(pass_rate=0.0, is_coding=False)
    assert should is True
    assert t == ComprehensionType.EPL
