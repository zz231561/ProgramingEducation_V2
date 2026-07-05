"""K6a/K6b 單元測試：訊號分級 BKT 參數 + 遺忘曲線惰性衰減。

涵蓋：
- half_life_days 隨 success_count 成長且有上限
- effective_confidence：無練習記錄 / 低於 floor 不動；剛練完 ≈ 原值；
  一個半衰期後恰為中點；長期趨近 floor 不歸零
- is_due_for_review 邊界（超過一個半衰期才提示）
- K6a：BKT_CHAT_PARAMS 單次更新幅度顯著小於 quiz 強證據參數
"""

from datetime import datetime, timedelta, timezone

import pytest

from services.mastery.decay import (
    BASE_HALF_LIFE_DAYS,
    DECAY_FLOOR,
    MAX_HALF_LIFE_DAYS,
    days_since,
    effective_confidence,
    half_life_days,
    is_due_for_review,
)
from services.mastery.updater import (
    BKT_CHAT_PARAMS,
    BKT_DEFAULT_PARAMS,
    bkt_online_update,
)

NOW = datetime(2026, 7, 6, 12, 0, 0, tzinfo=timezone.utc)


def _ago(days: float) -> datetime:
    return NOW - timedelta(days=days)


# === half_life_days ===


def test_half_life_grows_with_success():
    assert half_life_days(0) == BASE_HALF_LIFE_DAYS
    assert half_life_days(2) == BASE_HALF_LIFE_DAYS * 2.0  # 1 + 0.5*2
    assert half_life_days(4) > half_life_days(1)


def test_half_life_capped():
    assert half_life_days(1000) == MAX_HALF_LIFE_DAYS


# === effective_confidence ===


def test_no_last_practiced_no_decay():
    assert effective_confidence(0.8, None, 0, now=NOW) == 0.8


def test_below_floor_untouched():
    assert effective_confidence(0.2, _ago(100), 0, now=NOW) == 0.2


def test_fresh_practice_no_decay():
    assert effective_confidence(0.8, _ago(0), 0, now=NOW) == pytest.approx(0.8)


def test_one_half_life_halves_above_floor():
    """一個半衰期後，高於 floor 的部分恰剩一半。"""
    stored = 0.85
    eff = effective_confidence(stored, _ago(BASE_HALF_LIFE_DAYS), 0, now=NOW)
    expected = DECAY_FLOOR + (stored - DECAY_FLOOR) / 2
    assert eff == pytest.approx(expected)


def test_long_absence_approaches_floor_not_zero():
    eff = effective_confidence(0.95, _ago(365), 0, now=NOW)
    assert DECAY_FLOOR < eff < DECAY_FLOOR + 0.02


def test_more_successes_decay_slower():
    """FSRS 穩定度：練得越熟（success 多）同天數衰減越少。"""
    novice = effective_confidence(0.8, _ago(14), 0, now=NOW)
    veteran = effective_confidence(0.8, _ago(14), 6, now=NOW)
    assert veteran > novice


def test_naive_datetime_treated_as_utc():
    """SQLite 測試 DB 回 naive datetime 不應 crash。"""
    naive = (NOW - timedelta(days=7)).replace(tzinfo=None)
    eff = effective_confidence(0.8, naive, 0, now=NOW)
    assert 0.25 < eff < 0.8


# === days_since ===


def test_days_since_none():
    assert days_since(None, now=NOW) is None


def test_days_since_clamped_non_negative():
    assert days_since(NOW + timedelta(days=1), now=NOW) == 0.0


# === is_due_for_review ===


def test_due_after_one_half_life():
    assert is_due_for_review(0.8, _ago(BASE_HALF_LIFE_DAYS + 0.1), 0, now=NOW) is True


def test_not_due_before_half_life():
    assert is_due_for_review(0.8, _ago(BASE_HALF_LIFE_DAYS / 2), 0, now=NOW) is False


def test_not_due_when_below_floor():
    assert is_due_for_review(0.2, _ago(100), 0, now=NOW) is False


def test_not_due_without_record():
    assert is_due_for_review(0.8, None, 0, now=NOW) is False


# === K6a 訊號分級 ===


def test_chat_params_weaker_update_on_correct():
    """同一 prior、同樣答對：chat 弱證據的增幅應顯著小於 quiz 強證據。"""
    prior = 0.4
    strong = bkt_online_update(prior, True, BKT_DEFAULT_PARAMS)
    weak = bkt_online_update(prior, True, BKT_CHAT_PARAMS)
    assert strong > weak > prior


def test_chat_params_weaker_update_on_incorrect():
    """答錯時 chat 弱證據的降幅也應較小（甚至可能因 learn 而近持平）。"""
    prior = 0.6
    strong = bkt_online_update(prior, False, BKT_DEFAULT_PARAMS)
    weak = bkt_online_update(prior, False, BKT_CHAT_PARAMS)
    # 兩者都不高於 prior + learn 轉移；弱證據離 prior 更近
    assert abs(weak - prior) < abs(strong - prior)
