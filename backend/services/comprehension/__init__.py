"""Post-Solution Comprehension Check service — 2-6 Phase。

2-6a 範圍：CRUD（讀取 / upsert 持久化欄位）。
2-6b/c/d 將補：EPL / 預測輸出 / 變體題的 LLM 生成與評分。
"""

from services.comprehension.crud import (
    ComprehensionUpdate,
    get_comprehension,
    upsert_comprehension,
)
from services.comprehension.epl import (
    EPL_PASS_THRESHOLD,
    EplGenerationResult,
    EplGradeResult,
    generate_epl_prompt,
    grade_epl_answer,
)
from services.comprehension.orchestrator import (
    start_epl_for_answer,
    submit_epl_for_answer,
)

__all__ = [
    "EPL_PASS_THRESHOLD",
    "ComprehensionUpdate",
    "EplGenerationResult",
    "EplGradeResult",
    "generate_epl_prompt",
    "get_comprehension",
    "grade_epl_answer",
    "start_epl_for_answer",
    "submit_epl_for_answer",
    "upsert_comprehension",
]
