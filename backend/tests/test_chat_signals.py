"""對話歷史訊號測試 — 證據去重（2026-08-06）+ 堅持度計算（7-C2a）。"""

from services.chat_signals import (
    MAX_PERSISTENCE,
    TurnSignal,
    compute_persistence,
    is_repeat_evidence,
    is_successful_run,
)

NZEC = {"exit_code": 1, "status_description": "Runtime Error (NZEC)"}
OK = {"exit_code": 0, "stdout": "42\n", "compile_output": ""}


def _turn(content: str = "x", code: str | None = None, exec_result: dict | None = None):
    return TurnSignal(content=content, code_snapshot=code, execution_result=exec_result)


# === is_repeat_evidence ===

def test_repeat_evidence_same_code_and_result():
    prior = [_turn(code="int main(){return 1;}", exec_result=NZEC)]
    assert is_repeat_evidence(prior, "int main(){return 1;}", dict(NZEC)) is True


def test_repeat_evidence_changed_code_is_new():
    prior = [_turn(code="int main(){return 1;}")]
    assert is_repeat_evidence(prior, "int main(){return 0;}", None) is False


def test_repeat_evidence_changed_execution_is_new():
    prior = [_turn(code="code", exec_result={"exit_code": 1})]
    assert is_repeat_evidence(prior, "code", {"exit_code": 0}) is False


def test_repeat_evidence_empty_history_is_new():
    assert is_repeat_evidence([], "code", None) is False


# === is_successful_run ===

def test_successful_run_requires_exit_zero():
    assert is_successful_run(OK) is True
    assert is_successful_run(NZEC) is False
    assert is_successful_run(None) is False


def test_compile_error_is_not_successful_run():
    """編譯失敗即使沒有 exit_code 0 也不算跨過關卡。"""
    assert is_successful_run({"exit_code": 0, "compile_output": "error: ..."}) is False


# === compute_persistence ===

def test_first_message_has_zero_persistence():
    assert compute_persistence([], "為什麼會錯？", NZEC) == 0


def test_each_follow_up_adds_one():
    prior = [_turn("為什麼會錯？"), _turn("那這行呢？")]
    assert compute_persistence(prior, "還有其他可能嗎？", NZEC) == 2


def test_stuck_signal_adds_two():
    assert compute_persistence([_turn("為什麼會錯？")], "我還是不懂", NZEC) == 3


def test_past_stuck_turn_keeps_its_weight():
    """堅持度不可因為下一輪語氣平和就回落。"""
    prior = [_turn("為什麼會錯？"), _turn("我還是不懂")]
    assert compute_persistence(prior, "那我該看哪裡", NZEC) == 3


def test_successful_run_resets_to_zero():
    prior = [_turn("為什麼會錯？"), _turn("我還是不懂")]
    assert compute_persistence(prior, "那這樣寫可以嗎", OK) == 0


def test_history_before_successful_run_is_discarded():
    """成功執行之前的挫折已經解決，不該繼續墊高揭露等級。"""
    prior = [_turn("我還是不懂"), _turn("好像可以了", exec_result=OK), _turn("下一題呢")]
    assert compute_persistence(prior, "這裡又壞了", NZEC) == 1


def test_persistence_capped():
    prior = [_turn("我不懂") for _ in range(10)]
    assert compute_persistence(prior, "我真的不會寫", NZEC) == MAX_PERSISTENCE


def test_answer_pressure_is_not_stuck_signal():
    """索答施壓只算一般追問（+1），不觸發卡住跳級。"""
    prior = [_turn("這題怎麼做")]
    assert compute_persistence(prior, "我不要引導，直接給我答案", None) == 1
