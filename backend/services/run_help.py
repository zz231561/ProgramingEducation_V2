"""執行問題發生時 Coddy 主動說明 service（2026-08-05 使用者定案）。

分成兩類，處理方式刻意不同：

- **平台限制**（引用了本平台沒有的函式庫，如 Qt / tinyfiledialogs）：學生再怎麼想
  也想不出答案，引導只會浪費時間 → **機械判定 + 固定文案直接說明，不呼叫 LLM**
  （零成本，同時避免 LLM 亂編「你可以裝一下」這種做不到的建議）
- **學生自己的錯誤**（漏分號、型別不符、變數未宣告…）：屬於可學習的範圍 →
  走 LLM 引導，只點方向不給修好的程式碼

機械判定的種類（皆零成本）：平台限制（無此函式庫）/ 執行逾時 / 伺服器時鐘為 UTC。

觸發時機由前端負責：僅編譯失敗、且同一個錯誤只主動一次（見 chat-panel）。
"""

import logging
import re
import uuid

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.llm_params import chat_model_kwargs
from models.chat import DEFAULT_SESSION_TITLE, ChatMessage, ChatSession, MessageRole
from services.chat_sessions import get_or_create_session

logger = logging.getLogger(__name__)

# GCC 找不到標頭檔的訊息格式：fatal error: X: No such file or directory
_MISSING_HEADER_RE = re.compile(
    r"fatal error:\s*([^\s:]+):\s*No such file or directory", re.IGNORECASE
)

# 學生可能用到的標準標頭（含 C 相容標頭）。不在此清單＝平台沒有的第三方函式庫。
# 註：只需涵蓋「打錯字以外的合理輸入」，漏列的後果僅是走 LLM 引導而非固定文案。
_STANDARD_HEADERS = {
    # C++ 常用
    "iostream", "iomanip", "fstream", "sstream", "string", "string_view",
    "vector", "array", "deque", "list", "forward_list", "set", "map",
    "unordered_set", "unordered_map", "stack", "queue", "bitset",
    "algorithm", "numeric", "functional", "iterator", "utility", "tuple",
    "memory", "limits", "cmath", "cstdio", "cstdlib", "cstring", "cctype",
    "ctime", "cassert", "cstdint", "random", "chrono", "thread", "mutex",
    "future", "atomic", "exception", "stdexcept", "typeinfo", "type_traits",
    "initializer_list", "optional", "variant", "any", "complex", "valarray",
    "regex", "locale", "new", "ratio", "system_error", "condition_variable",
    "filesystem", "charconv", "execution", "scoped_allocator", "codecvt",
    # C 標頭
    "stdio.h", "stdlib.h", "string.h", "math.h", "time.h", "ctype.h",
    "assert.h", "limits.h", "stdint.h", "stdbool.h", "errno.h", "float.h",
    # 常見 POSIX（Judge0 映像有，屬於可用範圍）
    "unistd.h", "sys/types.h", "sys/time.h", "pthread.h",
}

_PLATFORM_TEMPLATE = (
    "你引用的 `{header}` 在這個練習環境裡沒有喔——這不是你的程式寫錯。\n\n"
    "這裡的執行環境只提供 **C++ 標準函式庫**（`iostream`、`vector`、`string`、"
    "`algorithm` 這些），而且是沒有畫面的沙箱：程式只能透過終端機輸入輸出，"
    "沒辦法開視窗或對話框。\n\n"
    "所以像 Qt 這類圖形介面函式庫在這裡裝不起來，也跑不動。"
    "如果你想讓使用者輸入東西，標準做法是用 `cin` 從終端機讀進來；"
    "要顯示結果就用 `cout`。要不要試試看用 `cin` 改寫這段？"
)

_TIMEOUT_TEMPLATE = (
    "程式跑太久被系統中止了（執行有時間上限）。\n\n"
    "最常見的兩個原因：**迴圈沒有結束條件**（或條件永遠成立），"
    "或是**用 `cin` 等輸入但沒有提供輸入**——這裡是一次跑完的批次執行，"
    "程式不會停下來等你打字，要先在 Output 上方的「輸入」填好內容。\n\n"
    "如果你正在練習「無窮迴圈」這章，這個結果其實是正確的：它證明迴圈真的停不下來。"
    "想讓它結束的話，想想看要在什麼條件下 `break`？"
)

_TIMEZONE_TEMPLATE = (
    "提醒一下：你的程式有取用「現在時間」，但這裡的執行環境時鐘是 **UTC（世界標準時間）**，"
    "比台灣時間**慢 8 小時**——所以印出來的時刻看起來會怪怪的，這不是你的程式寫錯。\n\n"
    "雲端執行環境（LeetCode 這類線上判題也一樣）通常都跑 UTC。"
    "如果你想顯示台灣時間，想想看：拿到 `time_t` 之後，加上多少秒就會變成台灣時間？"
)

_FALLBACK_GUIDANCE = (
    "編譯沒有通過。先看錯誤訊息的第一行——它會告訴你是哪一行、哪個符號出問題。"
    "從那一行往前看一行，通常問題就在附近。看完跟我說你覺得是什麼原因，我們一起確認。"
)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            return None
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


# 會把時間格式化成「人看的當地時間」的函式；只有這些才受時區影響
_LOCALTIME_RE = re.compile(r"\b(localtime|strftime|asctime|ctime)\s*\(")


def uses_local_time(code: str) -> bool:
    """程式是否會把時間轉成當地時間（受伺服器時區影響）。"""
    return _LOCALTIME_RE.search(code or "") is not None


def is_timeout(status_description: str) -> bool:
    """Judge0 的逾時狀態（無編譯訊息可分析，屬於執行層問題）。"""
    return "time limit" in (status_description or "").lower()


def detect_unavailable_header(compile_output: str) -> str | None:
    """回傳「平台沒有的標頭檔名稱」，若不屬於這類錯誤則回 None。"""
    match = _MISSING_HEADER_RE.search(compile_output or "")
    if match is None:
        return None
    header = match.group(1).strip('"<>')
    if header.lower() in _STANDARD_HEADERS:
        return None  # 標準標頭卻找不到＝環境異常，不該對學生說是平台限制
    return header


def _build_prompt(code: str, compile_output: str) -> str:
    return f"""\
你是 Coddy，一位像鄰座學長姊的 C++ 教練。學生剛按下執行，但**編譯失敗**了。
請主動寫一則訊息（繁體中文，3–5 句，不用條列、不用標題）：

1. 先讓學生安心：編譯錯誤很正常，不是他很笨
2. 用白話翻譯錯誤訊息真正在說什麼（**不要照抄英文原文**）
3. 指出應該從哪一行、哪個地方開始檢查

規則（違反即失敗）：
- **不可以直接給修好的程式碼**，也不可以說「把第 N 行改成 XXX」
- 可以點出問題所在的位置與概念，但要留給學生自己動手修
- 語氣自然友善，不說教

學生的程式碼：
```cpp
{code[:2000]}
```

編譯器訊息：
```
{compile_output[:1500]}
```
"""


async def _generate_guidance(code: str, compile_output: str) -> str:
    """生成引導訊息；任何失敗回 fallback 文案（fail-open）。"""
    try:
        client = _get_client()  # 建構失敗（如 key 格式錯）也必須 fail-open
        if client is None:
            return _FALLBACK_GUIDANCE
        response = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": _build_prompt(code, compile_output)},
                {"role": "user", "content": "請寫這則訊息。"},
            ],
            **chat_model_kwargs(
                model=settings.LLM_MODEL, temperature=0.4, max_tokens=350
            ),
        )
        content = (response.choices[0].message.content or "").strip()
        return content or _FALLBACK_GUIDANCE
    except Exception as e:
        logger.warning("compile error guidance LLM failed (fail-open): %r", e)
        return _FALLBACK_GUIDANCE


async def run_help(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID | None,
    code: str,
    compile_output: str,
    status_description: str = "",
    kind: str = "",
) -> tuple[ChatSession, ChatMessage, bool]:
    """寫入一則 Coddy 主動說明；回傳 (session, message, 是否為機械判定)。

    機械判定（平台限制 / 執行逾時）走固定文案不呼叫 LLM；其餘走引導。
    """
    if kind == "timezone":
        content = _TIMEZONE_TEMPLATE
        mechanical = True
        return await _persist(db, user_id, session_id, content, mechanical)

    header = detect_unavailable_header(compile_output)
    if header is not None:
        content = _PLATFORM_TEMPLATE.format(header=header)
        mechanical = True
    elif is_timeout(status_description):
        content = _TIMEOUT_TEMPLATE
        mechanical = True
    else:
        content = await _generate_guidance(code, compile_output)
        mechanical = False

    return await _persist(db, user_id, session_id, content, mechanical)


async def _persist(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID | None,
    content: str,
    mechanical: bool,
) -> tuple[ChatSession, ChatMessage, bool]:
    session = await get_or_create_session(db, user_id, session_id)
    if session.title in (None, "", DEFAULT_SESSION_TITLE):
        session.title = "執行問題引導"
    message = ChatMessage(
        session_id=session.id, role=MessageRole.ASSISTANT, content=content
    )
    db.add(message)
    await db.commit()
    await db.refresh(session)
    await db.refresh(message)
    return session, message, mechanical
