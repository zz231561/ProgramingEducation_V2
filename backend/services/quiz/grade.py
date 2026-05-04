"""出題 Submit 階段判分 — 依題型比對學生答案與正解。

設計：
- multiple_choice：學生送 `{selected_index: int}`，比對 content.answer_index
- fill_blank：學生送 `{answers: list[str]}`，trim + casefold 後逐項比對 content.answers
- coding：MVP 暫不判分（is_correct=False，feedback 提示「需教師/Judge0 審核」），
  Judge0 整合留給後續 task；不阻擋寫入 student_answers
"""

from typing import Any

from models.quiz import Question, QuestionType


def _grade_multiple_choice(content: dict[str, Any], answer: dict[str, Any]) -> bool:
    selected = answer.get("selected_index")
    if not isinstance(selected, int):
        return False
    return selected == content.get("answer_index")


def _grade_fill_blank(content: dict[str, Any], answer: dict[str, Any]) -> bool:
    correct: list[str] = content.get("answers", [])
    submitted: list[Any] = answer.get("answers", [])
    if len(submitted) != len(correct):
        return False
    return all(
        isinstance(s, str) and s.strip().casefold() == c.strip().casefold()
        for s, c in zip(submitted, correct)
    )


def grade_answer(
    question: Question,
    answer: dict[str, Any],
) -> tuple[bool, str]:
    """判分。回傳 (is_correct, feedback)。

    feedback 為一句話的回饋（成功/失敗 + 簡短說明）；詳細 explanation
    由 caller 從 question.explanation 補上。
    """
    qtype = question.type
    content = question.content or {}

    if qtype == QuestionType.MULTIPLE_CHOICE.value:
        is_correct = _grade_multiple_choice(content, answer)
        return is_correct, "答對了！" if is_correct else "答錯了，再看看其他選項。"

    if qtype == QuestionType.FILL_BLANK.value:
        is_correct = _grade_fill_blank(content, answer)
        return is_correct, (
            "答對了！" if is_correct else "答錯了，請對照正解再思考。"
        )

    # coding：MVP 不自動判分（需要 Judge0 整合）
    return False, "程式撰寫題暫不自動判分；提交已記錄，後續會整合 Judge0 自動評分。"
