"""EDF 管線共用資料模型。"""

from enum import Enum, IntEnum

from pydantic import BaseModel, Field


class BloomLevel(IntEnum):
    """Bloom 認知等級（6 級）。"""

    REMEMBER = 1
    UNDERSTAND = 2
    APPLY = 3
    ANALYZE = 4
    EVALUATE = 5
    CREATE = 6


class ComprehensionSignal(str, Enum):
    """學生本則訊息顯示他吸收了上一輪說明沒有（7-C2a'）。

    這是 `need` 狀態機的主要輸入：理解 → 下修揭露、沒理解 → 上修。
    **索答施壓不算沒理解**——那是意願問題不是理解問題，一律 UNCLEAR。
    """

    UNDERSTOOD = "understood"
    NOT_UNDERSTOOD = "not_understood"
    UNCLEAR = "unclear"


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
    # 7-C2a'（2026-08-06）：Decision 層 `need` 狀態機的兩個輸入，同樣搭在本次
    # Evidence 呼叫上（零額外請求）。預設值一律偏保守：判不出來就維持現狀，
    # 不會把卡住的學生打回 L0，也不會替索答者加碼。
    comprehension_signal: ComprehensionSignal = Field(
        default=ComprehensionSignal.UNCLEAR,
        description="學生是否吸收了上一輪說明（understood 下修 / not_understood 上修）",
    )
    continues_previous_issue: bool = Field(
        default=True, description="是否延續上一輪的同一個卡點（False = 換題目，need 歸零）"
    )

    @classmethod
    def from_llm(cls, data: dict, execution_failed: bool = False) -> "EvidenceResult":
        """容錯解析 LLM 輸出——單一欄位越界不該毀掉整次教學互動。

        2026-08-06 實測：LLM 把 ConceptTag 寫進 `error_type`（"undefined-behavior"），
        pydantic 直接 raise，學生收到的是「AI 服務暫時不可用」。JSON 本身是完整的，
        毀掉整輪並不合理。

        越界值一律退回**保守**預設；`error_type` 沒有無害的預設值（它決定 base），
        因此改用機械事實：平台判定執行失敗 → runtime，否則 none。
        """
        clean = dict(data)

        if _as_enum(ErrorType, clean.get("error_type")) is None:
            clean["error_type"] = ErrorType.RUNTIME if execution_failed else ErrorType.NONE

        bloom = clean.get("bloom_level")
        if not isinstance(bloom, int) or bloom not in range(1, 7):
            clean["bloom_level"] = BloomLevel.APPLY  # 中位數，不偏袒任何鷹架強度

        tags = clean.get("concept_tags")
        clean["concept_tags"] = (
            [t for t in tags if t in CONCEPT_TAGS][:3] if isinstance(tags, list) else []
        )

        if _as_enum(ComprehensionSignal, clean.get("comprehension_signal")) is None:
            clean["comprehension_signal"] = ComprehensionSignal.UNCLEAR
        for flag, default in (("is_on_topic", True), ("continues_previous_issue", True)):
            if not isinstance(clean.get(flag), bool):
                clean[flag] = default

        return cls(**clean)


def _as_enum(enum_cls, value):
    """字串 → enum；非法值回 None（呼叫端決定退回什麼預設）。"""
    try:
        return enum_cls(value)
    except (ValueError, TypeError):
        return None
