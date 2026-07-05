"""K6b 遺忘曲線惰性衰減 — 讀取時計算 effective confidence，不改寫 DB。

設計（2026-07-06 session 定案；理論依據見 docs/references.md §5.1）：
- **Ebbinghaus 指數衰減**：`effective = floor + (stored − floor) × exp(−ln2 × days / half_life)`
- **FSRS 記憶穩定度**：半衰期隨成功練習次數線性成長（練得越熟、忘得越慢），
  對應 FSRS「stability 隨成功複習成長」概念的最簡化版
- **floor 下限**：衰減不歸零——避免懲罰到打擊信心，且「學過但生疏」
  與「從未接觸」（無 mastery row）在語意上必須可區分
- **惰性計算**：套用點在讀取端（/concepts/mastery、quiz Select、K3 診斷），
  DB 儲存值不變、不需排程 job；BKT 更新仍以 stored confidence 為 prior
  （衰減表達的是「提取強度」下降，非「習得狀態」倒退——BKT 語意不受污染）

參數初始值（K6 實測後可調）：
- BASE_HALF_LIFE_DAYS=14：兩週未練習掉一半（高於 floor 的部分）
- HALF_LIFE_SUCCESS_BONUS=0.5：每次成功練習半衰期 +50% 基準值
- MAX_HALF_LIFE_DAYS=180：半衰期上限（半年）
- DECAY_FLOOR=0.25：衰減下限
"""

import math
from datetime import datetime, timezone

DECAY_FLOOR = 0.25
BASE_HALF_LIFE_DAYS = 14.0
HALF_LIFE_SUCCESS_BONUS = 0.5
MAX_HALF_LIFE_DAYS = 180.0

_LN2 = math.log(2.0)


def half_life_days(success_count: int) -> float:
    """半衰期（天）— 隨成功練習次數成長，上限 MAX_HALF_LIFE_DAYS。"""
    half_life = BASE_HALF_LIFE_DAYS * (1.0 + HALF_LIFE_SUCCESS_BONUS * success_count)
    return min(half_life, MAX_HALF_LIFE_DAYS)


def days_since(last_practiced_at: datetime | None, now: datetime | None = None) -> float | None:
    """距上次練習天數；無記錄（舊資料）回 None = 不衰減。"""
    if last_practiced_at is None:
        return None
    now = now or datetime.now(timezone.utc)
    # SQLite 測試 DB 可能回 naive datetime；一律視為 UTC
    if last_practiced_at.tzinfo is None:
        last_practiced_at = last_practiced_at.replace(tzinfo=timezone.utc)
    return max(0.0, (now - last_practiced_at).total_seconds() / 86400.0)


def effective_confidence(
    stored: float,
    last_practiced_at: datetime | None,
    success_count: int,
    now: datetime | None = None,
) -> float:
    """讀取端的 effective confidence（惰性衰減後）。

    stored <= floor 或無 last_practiced_at → 原值不動。
    """
    if stored <= DECAY_FLOOR:
        return stored
    days = days_since(last_practiced_at, now)
    if days is None:
        return stored
    factor = math.exp(-_LN2 * days / half_life_days(success_count))
    return DECAY_FLOOR + (stored - DECAY_FLOOR) * factor


def is_due_for_review(
    stored: float,
    last_practiced_at: datetime | None,
    success_count: int,
    now: datetime | None = None,
) -> bool:
    """K6c 複習提示：距上次練習已超過一個半衰期（且原本有掌握度可流失）。

    framing 為「該複習了」而非扣分——前端據此顯示提示與節點變暗。
    """
    if stored <= DECAY_FLOOR:
        return False
    days = days_since(last_practiced_at, now)
    if days is None:
        return False
    return days >= half_life_days(success_count)
