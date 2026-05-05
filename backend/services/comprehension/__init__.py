"""Post-Solution Comprehension Check service — 2-6 Phase。

2-6a 範圍：CRUD（讀取 / upsert 持久化欄位）。
2-6b/c/d 將補：EPL / 預測輸出 / 變體題的 LLM 生成與評分。
"""

from services.comprehension.crud import (
    ComprehensionUpdate,
    get_comprehension,
    upsert_comprehension,
)

__all__ = [
    "ComprehensionUpdate",
    "get_comprehension",
    "upsert_comprehension",
]
