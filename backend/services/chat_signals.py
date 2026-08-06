"""從對話歷史推導的教學訊號 — 證據去重 + 學生堅持度（persistence）。

7-C2a（2026-08-06）：persistence 原本由前端 `lib/hint-escalation.ts` 追蹤、
隨請求送出，但「送得出來的數字就可能被寫死成 0」（7-C1 修的正是這個 bug）。
改為後端自算——歷史中每則學生訊息都帶 `code_snapshot` 與 `execution_result`，
連續追問次數與「上次成功執行」都能還原，前端無從影響。

本模組只吃純資料（`TurnSignal`），不依賴 ORM model，可單獨單元測試。
"""

import re
from dataclasses import dataclass

# 揭露階梯共 6 級（0-5），persistence 再高也無意義，先行截斷
MAX_PERSISTENCE = 5

# 每多一次同脈絡追問的加權；明確表示卡住則加倍（roadmap 7-C2a ②）
_FOLLOW_UP_STEP = 1
_STUCK_BONUS = 2

# 卡住訊號：學生明確表示無法理解或無法回答（保守列舉，避免誤傷一般提問）。
# 注意「不會」單獨列會誤中「會不會」，只收「我不會／還不會／不會寫／不會做」。
# 「直接告訴我／給我答案」不列入：那是索答施壓不是卡住，跳級反而幫答案索取型
# 學生快速爬到高揭露等級；施壓訊息走一般追問加權即可。
_STUCK_RE = re.compile(
    r"不懂|不明白|不知道|不理解|看不懂|聽不懂|沒辦法|無法回答|搞不清楚"
    r"|還是不|我不會|還不會|不會寫|不會做|學不會|卡住"
)


@dataclass(frozen=True)
class TurnSignal:
    """歷史中一則學生訊息的訊號來源（由 caller 從 ChatMessage 擷取）。"""

    content: str
    code_snapshot: str | None
    execution_result: dict | None


def is_successful_run(execution_result: dict | None) -> bool:
    """程式順利跑完（exit 0 且無編譯訊息）＝學生跨過了這一關。"""
    if not execution_result:
        return False
    if (execution_result.get("compile_output") or "").strip():
        return False
    return execution_result.get("exit_code") == 0


def is_repeat_evidence(
    prior_turns: list[TurnSignal],
    code: str,
    execution_result: dict | None,
) -> bool:
    """上一則學生訊息帶著完全相同的 code + 執行結果 → 同一份證據。

    學生對同一次執行連續追問時，程式碼與執行結果原封不動地隨每則訊息重送；
    BKT 若每輪都更新，等於同一個錯誤被懲罰 N 次。
    """
    if not prior_turns:
        return False
    last = prior_turns[-1]
    return (last.code_snapshot or "") == (code or "") and (
        last.execution_result or None
    ) == (execution_result or None)


def compute_persistence(
    prior_turns: list[TurnSignal],
    question: str,
    execution_result: dict | None,
) -> int:
    """算出學生在當前脈絡累積的堅持度（0-5）。

    規則（roadmap 7-C2a ②）：同脈絡每則追問 +1／明確表示卡住 +2／
    成功執行（exit 0）歸零。歸零是往回掃到最近一次成功執行為止——
    在那之前的挫折已經解決，不該繼續墊高揭露等級。
    """
    if is_successful_run(execution_result):
        return 0

    score = 0
    for turn in reversed(prior_turns):
        if is_successful_run(turn.execution_result):
            break
        score += _STUCK_BONUS if _STUCK_RE.search(turn.content) else _FOLLOW_UP_STEP

    if _STUCK_RE.search(question):
        score += _STUCK_BONUS

    return min(score, MAX_PERSISTENCE)
