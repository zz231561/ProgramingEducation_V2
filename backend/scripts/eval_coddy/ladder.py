"""前端 Hint Ladder 邏輯的 Python 對照移植（web/lib/hint-escalation.ts）。

harness 直接打後端 API，繞過了前端——為了讓模擬送出的 hint_level
與真實學生體驗一致，這裡逐條複製前端規則。**兩邊規則若改動必須同步。**
"""

import re

HINT_LEVEL_MAX = 5

_STUCK_RE = re.compile(
    r"不懂|不明白|不知道|不理解|看不懂|聽不懂|沒辦法|無法回答|搞不清楚"
    r"|還是不|我不會|還不會|不會寫|不會做|學不會|卡住"
)
_ACK_RE = re.compile(r"懂了|了解|瞭解|明白了|知道了|原來如此|謝謝|感謝|清楚了")


def compute_hint_level(prev: int, question: str, fresh_context: bool) -> int:
    """與 computeHintLevel 完全同構：追問 +1 / 卡住跳 2 級下限 2 / 致謝歸零。"""
    base = 0 if fresh_context else prev
    if _STUCK_RE.search(question):
        return max(0, min(max(base + 2, 2), HINT_LEVEL_MAX))
    if _ACK_RE.search(question):
        return 0
    return max(0, min(0 if fresh_context else prev + 1, HINT_LEVEL_MAX))
