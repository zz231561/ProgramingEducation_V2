"""EDF 管線共用資料模型。"""

from enum import IntEnum, Enum
from pydantic import BaseModel, Field


class BloomLevel(IntEnum):
    """Bloom 認知等級（6 級）。"""

    REMEMBER = 1
    UNDERSTAND = 2
    APPLY = 3
    ANALYZE = 4
    EVALUATE = 5
    CREATE = 6


class ErrorType(str, Enum):
    """程式碼錯誤分類。"""

    SYNTAX = "syntax"
    LOGIC = "logic"
    RUNTIME = "runtime"
    COMPILATION = "compilation"
    SEMANTIC = "semantic"
    NONE = "none"


# 20 個 ConceptTag（V1 定義）
CONCEPT_TAGS = [
    "syntax-basic", "io-streams", "control-flow", "function-design",
    "arrays-strings", "pointer-arithmetic", "memory-management", "references",
    "oop-encapsulation", "oop-inheritance", "oop-polymorphism",
    "stl-containers", "stl-algorithms", "template-meta", "recursion",
    "error-handling", "undefined-behavior", "algorithm-complexity",
    "concurrency", "namespaces",
]


class EvidenceResult(BaseModel):
    """Evidence 層分析結果 — LLM 結構化輸出。"""

    error_type: ErrorType = Field(description="錯誤分類")
    error_message: str = Field(default="", description="錯誤摘要（一句話）")
    concept_tags: list[str] = Field(default_factory=list, description="涉及的 ConceptTag")
    bloom_level: BloomLevel = Field(description="學生目前所處的 Bloom 認知等級")
    bloom_reasoning: str = Field(default="", description="Bloom 等級判斷依據")
    code_analysis: str = Field(default="", description="程式碼問題分析（供 Decision 層使用）")
    # 成本分流（2026-08-05）：搭在既有 Evidence 呼叫上判斷，零額外成本。
    # 離題時 Feedback 走輕量路徑（跳過 RAG + 精簡 prompt），仍會回應學生、不攔截。
    # 預設 True：舊資料與 LLM 未回傳此欄時一律當作課程相關，避免誤判成離題。
    is_on_topic: bool = Field(
        default=True, description="學生訊息是否與 C++ 程式學習相關"
    )
