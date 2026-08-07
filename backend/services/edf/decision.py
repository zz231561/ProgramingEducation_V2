"""Decision 層 — 累積式揭露階梯與動態選層。

純邏輯，不呼叫 LLM。單調的維度是「**本題解法被揭露多少**」（reveal_level），
不是「講了多少話」——每升一級都是在前一級的基礎上多揭露一點，因此指令是
**累積**的，不是 6×6 = 36 格互斥的手寫矩陣（舊設計）。

選層：`reveal_level = min(5, base(error_type) + need)`
- `base`：無錯誤（純提問／查教材／程式正確）→ L0；syntax / compilation /
  runtime → L2（學生看不懂錯誤訊息，替他指出位置不算給答案）；
  logic / semantic → L1（找出邏輯錯在哪本身就是練習，直接指位置等於代寫）
- `need`：由 `services.chat_signals.compute_need` 估計「學生離自己解出來還差多少」。
  **不是追問次數**——實測證實那會讓索答施壓一路爬級（見該模組檔頭）

結構＝方案 B：**6 條等級指令 ＋ 6 條 Bloom 深度修飾（共 12 條）**，
由 Feedback 層組裝成「基底行為 ＋ 本級額外揭露 ＋ 依 Bloom 調整深度」。

⚠ RULE-1／RULE-2（不給完整解答程式碼、片段 ≤ 8 行且含 TODO）是階梯**之上**的
不變量，任何等級都不得突破：L5 的「完整」指**解釋**完整，不是**程式碼**完整。
"""

from pydantic import BaseModel, Field

from .models import BloomLevel, ErrorType, EvidenceResult

MAX_REVEAL_LEVEL = 5
# 到這一級才允許出現程式碼片段（L3 起才給骨架）
MIN_CODE_LEVEL = 3


class TeachingStrategy(BaseModel):
    """Decision 層輸出 — Feedback 層使用的教學指令。

    `use_rag` 已移除：RAG 注入改由 Feedback 層依檢索
    相似度分數決定（見 `rag_integration.RAG_MIN_SCORE`）。
    `hint_level` 改為 `reveal_level`（語意是「解法揭露程度」，
    且不再由前端送入）；新增 `bloom_guidance`（Bloom 深度修飾，與等級正交）。
    """

    reveal_level: int = Field(ge=0, le=MAX_REVEAL_LEVEL, description="本題解法揭露等級 0-5")
    instruction: str = Field(description="累積式揭露指令（L0 到本級全部允許）")
    bloom_guidance: str = Field(default="", description="依 Bloom 等級調整說明深度")
    allow_code_snippet: bool = Field(default=False, description="是否允許回應包含程式碼片段")


# === 六層累積式揭露階梯（每層只描述「比前一層多揭露什麼」）===

_LEVEL_REVEALS: tuple[str, ...] = (
    "回答學生實際問的問題、解釋他需要的概念，可以舉與本題無關的例子；本題解法揭露 0%。",
    "＋指出問題落在哪個區域或哪個概念（不給精確位置）。",
    "＋指出精確位置（行號）並說明為什麼錯。",
    "＋給出解法骨架，TODO 必須真的留白。",
    "＋逐步帶到只剩最後一步。",
    "＋逐行完整解釋，並給修正後的片段。",
)

# === Bloom 深度修飾（與等級正交：等級管揭露多少，Bloom 管講得多深）===

_BLOOM_DEPTH: dict[BloomLevel, str] = {
    BloomLevel.REMEMBER: "學生停在回憶層：直接給語法定義或關鍵字用途，別繞圈子。",
    BloomLevel.UNDERSTAND: "學生停在理解層：解釋概念含義，用正確／錯誤的對比幫他分辨。",
    BloomLevel.APPLY: "學生停在應用層：說明這個概念適用什麼情境、什麼時候該用它。",
    BloomLevel.ANALYZE: "學生停在分析層：給拆解問題的方法論（怎麼縮小範圍、怎麼追資料流），別替他拆完。",
    BloomLevel.EVALUATE: "學生停在評估層：給比較的面向（正確性／效能／可讀性），讓他自己下判斷。",
    BloomLevel.CREATE: "學生停在創造層：給幾個可選的設計方向，別替他決定選哪一個。",
}

# === 動態選層的起點 ===

_BASE_LEVEL: dict[ErrorType, int] = {
    ErrorType.NONE: 0,
    ErrorType.SYNTAX: 2,
    ErrorType.COMPILATION: 2,
    ErrorType.RUNTIME: 2,
    ErrorType.LOGIC: 1,
    ErrorType.SEMANTIC: 1,
}


def base_level(error_type: ErrorType) -> int:
    """錯誤類型決定的起始揭露等級（未知類型保守回 0）。"""
    return _BASE_LEVEL.get(error_type, 0)


def _cumulative_instruction(level: int) -> str:
    """組出 L0 到 `level` 的累積行為清單。"""
    lines = "\n".join(
        f"L{i}：{reveal}" for i, reveal in enumerate(_LEVEL_REVEALS[: level + 1])
    )
    return f"本次可揭露到 L{level}，以下每一層都允許（累積生效）：\n{lines}"


def decide_strategy(
    evidence: EvidenceResult,
    need: int = 0,
) -> TeachingStrategy:
    """依錯誤類型與學生需求量決定揭露等級與教學指令。

    `need` 由後端從對話歷史算出（`services.chat_signals.compute_need`），
    不接受前端送入的數字。
    """
    level = base_level(evidence.error_type) + max(0, need)
    level = min(MAX_REVEAL_LEVEL, level)

    return TeachingStrategy(
        reveal_level=level,
        instruction=_cumulative_instruction(level),
        bloom_guidance=_BLOOM_DEPTH[evidence.bloom_level],
        allow_code_snippet=level >= MIN_CODE_LEVEL,
    )
