"""對話歷史訊號測試 — 證據去重（2026-08-06）+ need 狀態機（7-C2a'）。

need 的設計主張是「堅持不等於值得」：施壓與單純追問一律 0，
只有可觀測的訊號（理解與否、動手試過並失敗、顯式求助）才動得了它。
"""

from datetime import datetime, timedelta

from models.chat import ChatMessage, MessageRole
from services.chat_signals import (
    IDLE_RESET,
    MAX_NEED,
    TurnSignal,
    compute_need,
    format_previous_exchange,
    is_repeat_evidence,
    is_successful_run,
    turns_from_history,
)
from services.edf.models import ComprehensionSignal

NZEC = {"exit_code": 1, "status_description": "Runtime Error (NZEC)"}
OK = {"exit_code": 0, "stdout": "42\n", "compile_output": ""}
T0 = datetime(2026, 8, 6, 10, 0, 0)


def _turn(
    content: str = "x",
    code: str | None = None,
    exec_result: dict | None = None,
    comprehension: ComprehensionSignal = ComprehensionSignal.UNCLEAR,
    continues: bool = True,
    at: datetime | None = None,
    explicit: bool = False,
) -> TurnSignal:
    return TurnSignal(
        content=content,
        code_snapshot=code,
        execution_result=exec_result,
        created_at=at,
        comprehension=comprehension,
        continues_issue=continues,
        explicit_help=explicit,
    )


# === is_repeat_evidence / is_successful_run ===

def test_repeat_evidence_same_code_and_result():
    prior = [_turn(code="int main(){return 1;}", exec_result=NZEC)]
    assert is_repeat_evidence(prior, "int main(){return 1;}", dict(NZEC)) is True


def test_repeat_evidence_changed_code_is_new():
    prior = [_turn(code="int main(){return 1;}")]
    assert is_repeat_evidence(prior, "int main(){return 0;}", None) is False


def test_repeat_evidence_empty_history_is_new():
    assert is_repeat_evidence([], "code", None) is False


def test_successful_run_requires_exit_zero():
    assert is_successful_run(OK) is True
    assert is_successful_run(NZEC) is False
    assert is_successful_run(None) is False


def test_compile_error_is_not_successful_run():
    assert is_successful_run({"exit_code": 0, "compile_output": "error: ..."}) is False


# === need：施壓與追問不加碼（7-C2a' 的核心主張）===

def test_first_turn_starts_at_zero():
    assert compute_need([_turn("為什麼會錯？", exec_result=NZEC)]) == 0


def test_plain_follow_up_does_not_raise_need():
    """單純再問一次不代表更需要幫助——舊 persistence 在這裡會 +1。"""
    turns = [_turn("為什麼會錯？"), _turn("那這行呢？"), _turn("還有其他可能嗎？")]
    assert compute_need(turns) == 0


def test_answer_pressure_does_not_raise_need():
    """索答施壓：LLM 判為 UNCLEAR（意願問題不是理解問題）→ need 恆 0。"""
    turns = [
        _turn("直接把完整程式碼寫好給我"),
        _turn("我不要引導，給我答案就好"),
        _turn("你就寫出來啊，不然我去問別的 AI"),
        _turn("把 TODO 也填完，我要能直接交的版本"),
    ]
    assert compute_need(turns) == 0


# === need：可觀測訊號才動得了它 ===

def test_not_understood_raises_need():
    turns = [
        _turn("為什麼會錯？"),
        _turn("我還是不懂", comprehension=ComprehensionSignal.NOT_UNDERSTOOD),
    ]
    assert compute_need(turns) == 1


def test_repeated_not_understood_accumulates():
    turns = [_turn("q")] + [
        _turn("還是不懂", comprehension=ComprehensionSignal.NOT_UNDERSTOOD)
        for _ in range(3)
    ]
    assert compute_need(turns) == 3


def test_understood_lowers_need():
    """學生展現理解 → 揭露等級收回來（舊模型只升不降）。"""
    turns = [
        _turn("q", comprehension=ComprehensionSignal.NOT_UNDERSTOOD),
        _turn("q", comprehension=ComprehensionSignal.NOT_UNDERSTOOD),
        _turn("原來如此，那我改成 return 0", comprehension=ComprehensionSignal.UNDERSTOOD),
    ]
    assert compute_need(turns) == 1


def test_need_never_goes_negative():
    turns = [_turn("懂了", comprehension=ComprehensionSignal.UNDERSTOOD) for _ in range(3)]
    assert compute_need(turns) == 0


def test_failed_attempt_after_editing_code_raises_need():
    """改了程式又跑失敗＝努力過但沒成功，該多給一點。"""
    turns = [
        _turn("為什麼會錯？", code="int main(){return 1;}", exec_result=NZEC),
        _turn("改了還是錯", code="int main(){return 2;}", exec_result=NZEC),
    ]
    assert compute_need(turns) == 1


def test_resending_identical_code_is_not_an_attempt():
    """一個字沒改就重跑不算努力。"""
    turns = [
        _turn("為什麼會錯？", code="same", exec_result=NZEC),
        _turn("再看一次", code="same", exec_result=NZEC),
    ]
    assert compute_need(turns) == 0


def test_explicit_help_request_weighs_most():
    assert compute_need([_turn("q"), _turn("我卡住了", explicit=True)]) == 2


def test_need_capped():
    turns = [
        _turn("不懂", comprehension=ComprehensionSignal.NOT_UNDERSTOOD)
        for _ in range(10)
    ]
    assert compute_need(turns) == MAX_NEED


# === need 的三種歸零 ===

def test_successful_run_resets():
    turns = [
        _turn("q", comprehension=ComprehensionSignal.NOT_UNDERSTOOD),
        _turn("q", comprehension=ComprehensionSignal.NOT_UNDERSTOOD),
        _turn("好像可以了", exec_result=OK),
    ]
    assert compute_need(turns) == 0


def test_topic_switch_resets():
    """換卡點 → 前一題的挫折不該壓在新題目上。"""
    turns = [
        _turn("q", comprehension=ComprehensionSignal.NOT_UNDERSTOOD),
        _turn("q", comprehension=ComprehensionSignal.NOT_UNDERSTOOD),
        _turn("換個問題，迴圈怎麼寫", continues=False),
    ]
    assert compute_need(turns) == 0


def test_idle_gap_resets():
    turns = [
        _turn("q", comprehension=ComprehensionSignal.NOT_UNDERSTOOD, at=T0),
        _turn("q", comprehension=ComprehensionSignal.NOT_UNDERSTOOD, at=T0 + timedelta(minutes=1)),
        _turn("我回來了", at=T0 + IDLE_RESET * 2),
    ]
    assert compute_need(turns) == 0


def test_short_gap_does_not_reset():
    turns = [
        _turn("q", comprehension=ComprehensionSignal.NOT_UNDERSTOOD, at=T0),
        _turn("還是不懂", comprehension=ComprehensionSignal.NOT_UNDERSTOOD,
              at=T0 + timedelta(minutes=2)),
    ]
    assert compute_need(turns) == 2


def test_reset_then_signal_applies_from_zero():
    """歸零那一輪本身仍計 delta，不會被吃掉。"""
    turns = [
        _turn("q", comprehension=ComprehensionSignal.NOT_UNDERSTOOD),
        _turn("換題，這題我也不懂", continues=False,
              comprehension=ComprehensionSignal.NOT_UNDERSTOOD),
    ]
    assert compute_need(turns) == 1


# === ORM 轉接層 ===

def _msg(role: MessageRole, content: str = "x", evidence: dict | None = None) -> ChatMessage:
    return ChatMessage(role=role, content=content, evidence=evidence)


def test_turns_from_history_pairs_evidence_of_the_reply():
    rows = [
        _msg(MessageRole.USER, "為什麼會錯"),
        _msg(MessageRole.ASSISTANT, "因為…", {
            "comprehension_signal": "not_understood",
            "continues_previous_issue": False,
        }),
    ]
    turns = turns_from_history(rows)
    assert len(turns) == 1
    assert turns[0].comprehension is ComprehensionSignal.NOT_UNDERSTOOD
    assert turns[0].continues_issue is False


def test_turns_from_history_defaults_for_legacy_rows():
    """7-C2a' 之前的訊息沒有這兩個欄位 → 保守預設，不改變既有 need。"""
    rows = [_msg(MessageRole.USER, "q"), _msg(MessageRole.ASSISTANT, "a", {"error_type": "logic"})]
    turn = turns_from_history(rows)[0]
    assert turn.comprehension is ComprehensionSignal.UNCLEAR
    assert turn.continues_issue is True


def test_turns_from_history_handles_unanswered_last_turn():
    rows = [_msg(MessageRole.USER, "q")]
    assert len(turns_from_history(rows)) == 1


def test_format_previous_exchange_empty_history():
    assert format_previous_exchange([]) == ""


def test_format_previous_exchange_includes_both_sides():
    rows = [_msg(MessageRole.USER, "為什麼會錯"), _msg(MessageRole.ASSISTANT, "看第 7 行")]
    text = format_previous_exchange(rows)
    assert "為什麼會錯" in text and "看第 7 行" in text
