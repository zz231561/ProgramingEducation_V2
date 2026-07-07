"""對話行為分類（StudyChat dialogue act schema，roadmap 5-2c）。

啟發式分類學生訊息的互動類型，寫入 `chat_messages.dialogue_act` 供行為分析（5-2d）。
純函式、零 LLM 呼叫（比照 5-2b `classify_execution` 慣例）；訊號不足回 None——欄位 nullable，
留待未來以 StudyChat 16k 標註語料訓練的分類器補值。
"""

from models.chat import DialogueAct

# 關鍵詞表（中英雙語）；比對前 text 已 strip + lower，中文不受 lower 影響、直接子字串比對
_ACK_KEYWORDS = (
    "謝謝", "感謝", "了解", "懂了", "知道了", "好的", "收到", "沒問題",
    "thanks", "thank you", "got it", "understood", "ok",
)
_VERIFY_KEYWORDS = (
    "對嗎", "對不對", "正確嗎", "是不是", "是嗎", "這樣對", "這樣寫對", "對吧",
    "right?", "correct?", "is this correct",
)
_HINT_KEYWORDS = (
    "提示", "幫我", "卡住", "不會", "該怎麼", "怎麼做", "怎麼寫",
    "help", "hint", "stuck", "give me a hint",
)
_CLARIFY_KEYWORDS = (
    "什麼是", "為什麼", "為何", "怎麼", "如何", "意思", "解釋", "差別", "區別",
    "what is", "why", "how ", "explain", "difference",
)

_ACK_MAX_LEN = 15  # acknowledgment 通常極短，避免長句誤判


def _has_execution_error(execution_result: dict | None) -> bool:
    """判定隨訊息附帶的執行結果是否含錯誤（stderr / 編譯輸出）。"""
    if not execution_result:
        return False
    return bool(
        (execution_result.get("stderr") or "").strip()
        or (execution_result.get("compile_output") or "").strip()
    )


def _matches(text: str, keywords: tuple[str, ...]) -> bool:
    return any(kw in text for kw in keywords)


def classify_dialogue_act(
    question: str,
    hint_level: int = 0,
    execution_result: dict | None = None,
) -> str | None:
    """依 StudyChat schema 啟發式分類學生訊息的 dialogue act；訊號不足回 None。

    優先序：明確 hint 請求 > 簡短致謝 > 求證 > 除錯（附執行錯誤）> 文字求助 > 澄清提問。
    `off_topic` 無可靠啟發式訊號，暫不主動判定（保留為合法值供未來分類器 / 人工標註使用）。
    """
    text = (question or "").strip().lower()
    if not text:
        return None

    if hint_level > 0:
        return DialogueAct.ASKING_HINT.value
    if len(text) <= _ACK_MAX_LEN and _matches(text, _ACK_KEYWORDS):
        return DialogueAct.ACKNOWLEDGMENT.value
    if _matches(text, _VERIFY_KEYWORDS):
        return DialogueAct.VERIFICATION.value
    if _has_execution_error(execution_result):
        return DialogueAct.DEBUGGING.value
    if _matches(text, _HINT_KEYWORDS):
        return DialogueAct.ASKING_HINT.value
    if _matches(text, _CLARIFY_KEYWORDS):
        return DialogueAct.CLARIFICATION_REQUEST.value
    return None
