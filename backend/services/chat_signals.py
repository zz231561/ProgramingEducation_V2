"""從對話歷史推導的教學訊號 — 證據去重 + 學生需求量（need）。

7-C2a（2026-08-06）：原本由前端 `lib/hint-escalation.ts` 追蹤的 hint 階梯搬到後端，
因為「送得出來的數字就可能被寫死成 0」（7-C1 修的正是這個 bug）。

7-C2a'（同日重寫）：後端版本一開始是「同脈絡追問次數」（persistence），實測發現
那是錯的代理變數——**堅持不等於值得**：索答型學生施壓四次就爬到 reveal 4，而
在對話中一直有進展的學生同樣被推高。改成估計「學生離自己解出來還差多少」：

    need_t = clamp(need_{t-1} + delta, 0, MAX_NEED)

delta 只認可觀測的訊號（理解與否、有沒有真的動手試），**單純追問與索答施壓皆為 0**。
歸零條件：程式跑成功 / 換卡點 / 閒置超時——都是事實或 LLM 的保守二元判定，不是關鍵字。

計算邏輯只吃純資料（`TurnSignal`）可單獨單元測試；`turns_from_history` 是唯一
接觸 ORM 的轉接層。
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from models.chat import ChatMessage, MessageRole
from services.edf.models import ComprehensionSignal, ErrorType, EvidenceResult

# 揭露階梯共 6 級（0-5），need 再高也無意義，先行截斷
MAX_NEED = 5

# 隔了這麼久才回來，前面的挫折已經不代表現在的狀態（純機械判定，零成本）
IDLE_RESET = timedelta(minutes=30)

_STEP = 1
# 顯式求助（「我卡住了」按鈕）權重高於推論訊號——學生自己說的最可信
_EXPLICIT_STEP = 2
# 單輪最多漲兩級：訊號可以疊加（按了求助 + 判定沒理解 + 改了還是失敗），
# 但一次跳三級以上會讓學生從「只給方向」直接掉到「逐行解釋」，階梯就失去意義
_MAX_TURN_RISE = 2


@dataclass(frozen=True)
class TurnSignal:
    """歷史中一輪學生互動的訊號來源（由 caller 從 ChatMessage 擷取）。

    `comprehension` / `continues_issue` 來自該輪 assistant 訊息存下的 evidence JSON；
    舊資料沒有這兩個欄位時取保守預設（UNCLEAR / True）＝該輪 delta 只剩努力訊號。
    """

    content: str
    code_snapshot: str | None
    execution_result: dict | None
    created_at: datetime | None = None
    comprehension: ComprehensionSignal = ComprehensionSignal.UNCLEAR
    continues_issue: bool = True
    explicit_help: bool = False
    error_type: str | None = None


def turns_from_history(rows: Sequence[ChatMessage]) -> list[TurnSignal]:
    """對話歷史 → 逐輪訊號。唯一接觸 ORM 的地方。

    每則學生訊息配對「緊接其後的 assistant 訊息」所存的 evidence JSON——
    那份 JSON 就是當輪的判定紀錄，need 因此可以無狀態重算，也可事後稽核。
    """
    turns: list[TurnSignal] = []
    for i, row in enumerate(rows):
        if row.role is not MessageRole.USER:
            continue
        reply = rows[i + 1] if i + 1 < len(rows) else None
        evidence = (
            reply.evidence
            if reply is not None
            and reply.role is MessageRole.ASSISTANT
            and isinstance(reply.evidence, dict)
            else {}
        )
        turns.append(
            TurnSignal(
                content=row.content,
                code_snapshot=row.code_snapshot,
                execution_result=row.execution_result,
                created_at=row.created_at,
                comprehension=_parse_comprehension(evidence.get("comprehension_signal")),
                # 舊資料沒這欄 → True（保守：不把歷史全切成新卡點）
                continues_issue=evidence.get("continues_previous_issue", True),
                explicit_help=bool(getattr(row, "explicit_help", False)),
                error_type=evidence.get("error_type"),
            )
        )
    return turns


def _parse_comprehension(value: object) -> ComprehensionSignal:
    """evidence JSON 的字串 → enum；非法值一律 UNCLEAR（不影響 need）。"""
    try:
        return ComprehensionSignal(value)
    except ValueError:
        return ComprehensionSignal.UNCLEAR


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


def stabilize_error_type(
    evidence: EvidenceResult,
    prior_turns: list[TurnSignal],
    code: str,
    execution_result: dict | None,
) -> EvidenceResult:
    """同一份 code + 執行結果 → 沿用上一輪的 `error_type`（tech-debt B8）。

    `error_type` 由 LLM 每輪重判，實測會在學生一個字沒改的情況下漂移
    （logic → none、runtime → semantic）。它決定 `base`，漂一次學生就看到
    揭露程度倒退。證據沒變時判定就不該變——這裡用的是既有的證據去重判斷，
    零成本、純機械，不引入新的推論。
    """
    if not is_repeat_evidence(prior_turns, code, execution_result):
        return evidence
    carried = prior_turns[-1].error_type
    if not carried or carried == evidence.error_type.value:
        return evidence
    try:
        return evidence.model_copy(update={"error_type": ErrorType(carried)})
    except ValueError:
        return evidence


def _made_failed_attempt(turn: TurnSignal, previous: TurnSignal | None) -> bool:
    """學生真的動手改了程式又跑失敗＝努力過但沒成功，該多給一點。

    只看「改了沒」而非改了多少：這裡要的是努力的存在證明，不是工作量。
    開場那一輪不算——那時還沒有「改」這回事，第一次貼失敗的程式只是描述現況。
    """
    if previous is None:
        return False
    if is_successful_run(turn.execution_result) or not turn.execution_result:
        return False
    return (turn.code_snapshot or "").strip() != (previous.code_snapshot or "").strip()


def _turn_delta(turn: TurnSignal, previous: TurnSignal | None) -> int:
    """單輪的 need 增減。純追問／索答施壓落在這裡＝0（兩者都是 UNCLEAR）。"""
    delta = 0
    if turn.comprehension is ComprehensionSignal.UNDERSTOOD:
        delta -= _STEP
    elif turn.comprehension is ComprehensionSignal.NOT_UNDERSTOOD:
        delta += _STEP
    if _made_failed_attempt(turn, previous):
        delta += _STEP
    if turn.explicit_help:
        delta += _EXPLICIT_STEP
    return min(delta, _MAX_TURN_RISE)


def _is_reset_point(turn: TurnSignal, previous: TurnSignal | None) -> bool:
    """本輪之前該不該把 need 清空。

    三種歸零：程式跑成功（客觀事實）／換了卡點（LLM 保守二元判定）／
    閒置超時（純時間）。全部與「學生講話的語氣」無關。
    """
    if is_successful_run(turn.execution_result):
        return True
    if not turn.continues_issue:
        return True
    if previous and turn.created_at and previous.created_at:
        return turn.created_at - previous.created_at > IDLE_RESET
    return False


def format_previous_exchange(rows: Sequence[ChatMessage], max_chars: int = 400) -> str:
    """上一輪問答摘要，供 Evidence 判 comprehension / 卡點延續。

    只取最後一組（學生說了什麼、Coddy 回了什麼），截斷長度控制 prompt 成本。
    """
    last_user = next((m for m in reversed(rows) if m.role is MessageRole.USER), None)
    last_reply = next(
        (m for m in reversed(rows) if m.role is MessageRole.ASSISTANT), None
    )
    if last_user is None and last_reply is None:
        return ""
    lines = ["上一輪對話（用來判斷學生這次的理解狀態與是否換了卡點）："]
    if last_user is not None:
        lines.append(f"學生：{last_user.content[:max_chars]}")
    if last_reply is not None:
        lines.append(f"Coddy：{last_reply.content[:max_chars]}")
    return "\n".join(lines)


def compute_need(turns: list[TurnSignal]) -> int:
    """重放整段對話，算出當前的 need（0-MAX_NEED）。

    `turns` 依時間排序，**最後一筆是本輪**。無狀態重算（與 mastery 同款）：
    每輪的判定都存在 assistant 訊息的 evidence JSON 裡，隨時可重現與稽核。
    """
    need = 0
    previous: TurnSignal | None = None
    for turn in turns:
        if _is_reset_point(turn, previous):
            need = 0
        need = max(0, min(MAX_NEED, need + _turn_delta(turn, previous)))
        previous = turn
    return need
