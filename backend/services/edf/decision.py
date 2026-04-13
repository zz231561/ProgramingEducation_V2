"""Decision 層 — Bloom × Hint Ladder 策略矩陣。

純邏輯查表，不呼叫 LLM。根據 Evidence 分析結果和當前 hint_level
決定 Feedback 層應使用的教學策略。
"""

from pydantic import BaseModel, Field

from .models import BloomLevel, EvidenceResult


class TeachingStrategy(BaseModel):
    """Decision 層輸出 — Feedback 層使用的教學指令。"""

    hint_level: int = Field(ge=0, le=5, description="當前提示等級 0-5")
    instruction: str = Field(description="給 Feedback 層的策略指令")
    allow_code_snippet: bool = Field(default=False, description="是否允許回應包含程式碼片段")
    use_rag: bool = Field(default=False, description="是否觸發 RAG 檢索")


# === 6×6 策略矩陣 ===
# 行 = Bloom level (1-6)，列 = Hint level (0-5)
# 值 = (instruction, allow_code_snippet)

_STRATEGY_MATRIX: dict[tuple[int, int], tuple[str, bool]] = {
    # --- REMEMBER (Bloom 1) ---
    (1, 0): ("用提問引導學生回憶相關語法或定義，不給任何提示。", False),
    (1, 1): ("指出錯誤與哪個語法規則有關，但不指出具體位置。", False),
    (1, 2): ("指出具體出錯的行號和相關的語法概念名稱。", False),
    (1, 3): ("給出正確語法的部分框架，用 TODO 標記需要填寫的部分。", True),
    (1, 4): ("逐步引導語法修正，只剩最後一步讓學生完成。", True),
    (1, 5): ("完整解釋語法規則並提供修正後的程式碼片段。", True),
    # --- UNDERSTAND (Bloom 2) ---
    (2, 0): ("請學生用自己的話解釋這段程式碼的行為，不給提示。", False),
    (2, 1): ("指出理解偏差的方向，例如「問題在於你對迴圈條件的理解」。", False),
    (2, 2): ("指出具體的概念誤解，並提供概念名稱。", False),
    (2, 3): ("用類比或簡單範例解釋概念，附帶框架程式碼讓學生填空。", True),
    (2, 4): ("提供詳細的概念解釋，用對比說明正確與錯誤的差異。", True),
    (2, 5): ("完整解釋概念並展示正確用法。", True),
    # --- APPLY (Bloom 3) ---
    (3, 0): ("問學生打算如何應用已知概念來解決這個問題。", False),
    (3, 1): ("提示應該使用哪類概念，但不說具體怎麼用。", False),
    (3, 2): ("指出需要用到的具體概念，並提示應用方向。", False),
    (3, 3): ("給出解題框架（含 TODO），讓學生填入關鍵邏輯。", True),
    (3, 4): ("逐步引導實作，每步確認學生理解後再進入下一步。", True),
    (3, 5): ("展示完整的應用方式並解釋每一步的原因。", True),
    # --- ANALYZE (Bloom 4) ---
    (4, 0): ("請學生分析程式碼的結構，辨識各部分的職責。", False),
    (4, 1): ("提示問題出在程式的哪個結構層面（如資料流、控制流）。", False),
    (4, 2): ("指出具體的結構問題和涉及的設計模式或概念。", False),
    (4, 3): ("提供重構框架，標記需要學生分析和填入的部分。", True),
    (4, 4): ("引導學生逐步拆解問題，比較不同結構方案。", True),
    (4, 5): ("完整分析程式結構並提供改進方案。", True),
    # --- EVALUATE (Bloom 5) ---
    (5, 0): ("請學生比較目前的解法和其他可能的做法。", False),
    (5, 1): ("指出評估的方向（效能？可讀性？正確性？）。", False),
    (5, 2): ("提供具體的評估標準和當前解法的弱點。", False),
    (5, 3): ("給出兩種方案的框架，讓學生分析優劣。", True),
    (5, 4): ("引導逐項比較，協助學生建立評估框架。", True),
    (5, 5): ("完整比較多種方案的優劣並給出建議。", True),
    # --- CREATE (Bloom 6) ---
    (6, 0): ("請學生構思一個新的解決方案，不給方向限制。", False),
    (6, 1): ("提示可以從哪個方向思考新方案。", False),
    (6, 2): ("指出可以結合哪些概念來建構解決方案。", False),
    (6, 3): ("給出高層架構框架，讓學生設計具體實作。", True),
    (6, 4): ("引導學生逐步設計方案，提供每步的選項。", True),
    (6, 5): ("展示完整的設計方案並解釋綜合運用的概念。", True),
}


def decide_strategy(
    evidence: EvidenceResult,
    hint_level: int,
) -> TeachingStrategy:
    """根據 Evidence 分析結果和 hint_level 查表決定教學策略。

    hint_level 由前端追蹤（學生同一問題連續求助次數）。
    """
    clamped_hint = max(0, min(5, hint_level))
    bloom = evidence.bloom_level

    instruction, allow_code = _STRATEGY_MATRIX[(bloom, clamped_hint)]

    # RAG 觸發條件：hint_level >= 2 且 bloom_level 屬於高階認知
    use_rag = clamped_hint >= 2 and bloom >= BloomLevel.ANALYZE

    return TeachingStrategy(
        hint_level=clamped_hint,
        instruction=instruction,
        allow_code_snippet=allow_code,
        use_rag=use_rag,
    )
