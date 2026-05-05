"""Post-Solution Comprehension Check service — 2-6 Phase。

2-6a 範圍：CRUD（讀取 / upsert 持久化欄位）。
2-6b/c/d 將補：EPL / 預測輸出 / 變體題的 LLM 生成與評分。
"""

from services.comprehension.crud import (
    ComprehensionUpdate,
    get_comprehension,
    upsert_comprehension,
)
from services.comprehension.mastery_hook import apply_comprehension_mastery
from services.comprehension.trigger import (
    HIGH_PASS_THRESHOLD,
    LOOKBACK_LIMIT,
    MID_HIGH_PASS_THRESHOLD,
    MID_LOW_PASS_THRESHOLD,
    TriggerDecision,
    decide_trigger,
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
    start_predict_for_answer,
    submit_epl_for_answer,
    submit_predict_for_answer,
)
from services.comprehension.predict_output import (
    PredictGenerationResult,
    PredictGradeResult,
    generate_predict_test,
    grade_predict_answer,
)
from services.comprehension.variation import (
    VariationGenerationResult,
    VariationGradeResult,
    generate_variation,
    grade_variation,
    start_variation_for_answer,
    submit_variation_for_answer,
)

__all__ = [
    "EPL_PASS_THRESHOLD",
    "HIGH_PASS_THRESHOLD",
    "LOOKBACK_LIMIT",
    "MID_HIGH_PASS_THRESHOLD",
    "MID_LOW_PASS_THRESHOLD",
    "ComprehensionUpdate",
    "EplGenerationResult",
    "EplGradeResult",
    "PredictGenerationResult",
    "PredictGradeResult",
    "TriggerDecision",
    "VariationGenerationResult",
    "VariationGradeResult",
    "apply_comprehension_mastery",
    "decide_trigger",
    "generate_epl_prompt",
    "generate_predict_test",
    "generate_variation",
    "get_comprehension",
    "grade_epl_answer",
    "grade_predict_answer",
    "grade_variation",
    "start_epl_for_answer",
    "start_predict_for_answer",
    "start_variation_for_answer",
    "submit_epl_for_answer",
    "submit_predict_for_answer",
    "submit_variation_for_answer",
    "upsert_comprehension",
]
