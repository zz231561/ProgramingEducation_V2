"""Quiz grade 純判分邏輯單元測試。"""

from models.quiz import Question, QuestionType
from services.quiz import grade_answer


def _q(qtype: QuestionType, content: dict) -> Question:
    return Question(
        type=qtype.value,
        concept_tags=["x"],
        bloom_level=3,
        difficulty=1,
        content=content,
        explanation="",
        source="generated",
        validated=True,
    )


# === multiple_choice ===


def test_mc_correct_index():
    q = _q(
        QuestionType.MULTIPLE_CHOICE,
        {"stem": "...", "options": ["a", "b", "c"], "answer_index": 1},
    )
    is_correct, _ = grade_answer(q, {"selected_index": 1})
    assert is_correct is True


def test_mc_wrong_index():
    q = _q(
        QuestionType.MULTIPLE_CHOICE,
        {"stem": "...", "options": ["a", "b"], "answer_index": 0},
    )
    is_correct, _ = grade_answer(q, {"selected_index": 1})
    assert is_correct is False


def test_mc_missing_field_treated_as_wrong():
    q = _q(
        QuestionType.MULTIPLE_CHOICE,
        {"options": ["a"], "answer_index": 0},
    )
    is_correct, _ = grade_answer(q, {})
    assert is_correct is False


# === fill_blank ===


def test_fill_exact_match():
    q = _q(QuestionType.FILL_BLANK, {"stem": "___", "answers": ["nullptr"]})
    is_correct, _ = grade_answer(q, {"answers": ["nullptr"]})
    assert is_correct is True


def test_fill_case_insensitive_and_trimmed():
    q = _q(QuestionType.FILL_BLANK, {"stem": "___", "answers": ["Nullptr"]})
    is_correct, _ = grade_answer(q, {"answers": ["  NULLPTR  "]})
    assert is_correct is True


def test_fill_wrong_count_fails():
    q = _q(
        QuestionType.FILL_BLANK,
        {"stem": "___ ___", "answers": ["a", "b"]},
    )
    is_correct, _ = grade_answer(q, {"answers": ["a"]})
    assert is_correct is False


def test_fill_one_blank_wrong_makes_whole_wrong():
    q = _q(
        QuestionType.FILL_BLANK,
        {"stem": "___ ___", "answers": ["a", "b"]},
    )
    is_correct, _ = grade_answer(q, {"answers": ["a", "wrong"]})
    assert is_correct is False


# === coding ===


def test_coding_returns_false_with_review_hint():
    q = _q(
        QuestionType.CODING,
        {"stem": "...", "starter_code": ""},
    )
    is_correct, feedback = grade_answer(q, {"source": "int main(){}"})
    assert is_correct is False
    assert "Judge0" in feedback or "審核" in feedback or "提交已記錄" in feedback
