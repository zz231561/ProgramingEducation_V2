"""Predict-Output service unit tests（roadmap 2-6c）。

涵蓋：
- normalize_output：trim / 折疊空白 / 多行 / 空行去除
- generate_predict_test：LLM 成功 / 各類 fallback
- grade_predict_answer：exact 通過 / semantic fallback 通過 / 完全不符 / LLM 失敗 fallback
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.quiz import Question
from services.comprehension.predict_output import (
    generate_predict_test,
    grade_predict_answer,
    normalize_output,
)


def _make_coding_question() -> Question:
    return Question(
        type="coding",
        concept_tags=["arrays-strings"],
        bloom_level=3,
        difficulty=2,
        content={
            "stem": "讀整數 N，輸出 1..N",
            "starter_code": "",
            "test_cases": [{"input": "3\n", "expected": "1\n2\n3\n"}],
        },
        explanation="",
        source="generated",
        validated=True,
    )


def _llm_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# === normalize_output ===


def test_normalize_strips_trailing_whitespace():
    assert normalize_output("  hello  \n") == "hello"


def test_normalize_collapses_internal_whitespace():
    assert normalize_output("a   b\tc") == "a b c"


def test_normalize_preserves_line_separation():
    assert normalize_output("1\n2\n3") == "1\n2\n3"


def test_normalize_drops_empty_lines():
    assert normalize_output("1\n\n2\n   \n3") == "1\n2\n3"


def test_normalize_handles_empty_string():
    assert normalize_output("") == ""


# === generate_predict_test ===


@pytest.mark.asyncio
async def test_generate_returns_input_and_expected_on_success():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({"input": "5\n", "expected": "1\n2\n3\n4\n5\n"})
        )
    )
    with patch("services.comprehension.predict_output._get_client", return_value=client):
        result = await generate_predict_test(_make_coding_question(), "int main() {}")
    assert result.test_input == "5\n"
    assert result.expected_output == "1\n2\n3\n4\n5\n"


@pytest.mark.asyncio
async def test_generate_no_client_returns_none():
    with patch("services.comprehension.predict_output._get_client", return_value=None):
        result = await generate_predict_test(_make_coding_question(), "x")
    assert result.test_input is None
    assert result.expected_output is None


@pytest.mark.asyncio
async def test_generate_llm_exception_returns_none():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(side_effect=RuntimeError("openai down"))
    with patch("services.comprehension.predict_output._get_client", return_value=client):
        result = await generate_predict_test(_make_coding_question(), "x")
    assert result.test_input is None


@pytest.mark.asyncio
async def test_generate_invalid_json_returns_none():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value=_llm_response("not json"))
    with patch("services.comprehension.predict_output._get_client", return_value=client):
        result = await generate_predict_test(_make_coding_question(), "x")
    assert result.test_input is None


@pytest.mark.asyncio
async def test_generate_missing_fields_returns_none():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"input": "5\n"}))  # 缺 expected
    )
    with patch("services.comprehension.predict_output._get_client", return_value=client):
        result = await generate_predict_test(_make_coding_question(), "x")
    assert result.test_input is None


# === grade_predict_answer ===


@pytest.mark.asyncio
async def test_grade_exact_match_passes_without_llm():
    """完全相同 → exact 通過，不應呼叫 LLM。"""
    client = AsyncMock()  # 給但不應被呼叫
    with patch("services.comprehension.predict_output._get_client", return_value=client):
        result = await grade_predict_answer(
            student_code="x",
            test_input="5\n",
            expected_output="1\n2\n3\n4\n5\n",
            student_predicted="1\n2\n3\n4\n5\n",
        )
    assert result.passed is True
    assert result.match_method == "exact"
    client.chat.completions.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_grade_normalized_match_passes_as_exact():
    """空白差異 → normalize 後相同 → exact。"""
    client = AsyncMock()
    with patch("services.comprehension.predict_output._get_client", return_value=client):
        result = await grade_predict_answer(
            student_code="x",
            test_input="3\n",
            expected_output="1 2 3",
            student_predicted="  1   2 3   ",
        )
    assert result.passed is True
    assert result.match_method == "exact"


@pytest.mark.asyncio
async def test_grade_semantic_fallback_passes():
    """嚴格不符 → LLM 判斷語意一致 → semantic 通過。"""
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({"semantically_equal": True, "feedback": "格式略異但結果對"})
        )
    )
    with patch("services.comprehension.predict_output._get_client", return_value=client):
        result = await grade_predict_answer(
            student_code="x",
            test_input="3\n",
            expected_output="1\n2\n3",
            student_predicted="1, 2, 3",
        )
    assert result.passed is True
    assert result.match_method == "semantic"
    assert result.feedback == "格式略異但結果對"


@pytest.mark.asyncio
async def test_grade_semantic_says_no_results_in_mismatch():
    """嚴格不符 + LLM 也說不一致 → mismatch。"""
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({"semantically_equal": False, "feedback": "輸出順序錯了"})
        )
    )
    with patch("services.comprehension.predict_output._get_client", return_value=client):
        result = await grade_predict_answer(
            student_code="x",
            test_input="3\n",
            expected_output="1\n2\n3",
            student_predicted="3\n2\n1",
        )
    assert result.passed is False
    assert result.match_method == "mismatch"
    assert result.feedback == "輸出順序錯了"


@pytest.mark.asyncio
async def test_grade_semantic_llm_unavailable_falls_back_to_mismatch():
    """嚴格不符 + LLM 不可用 → fallback 為 mismatch（不擋學生）。"""
    with patch("services.comprehension.predict_output._get_client", return_value=None):
        result = await grade_predict_answer(
            student_code="x",
            test_input="3\n",
            expected_output="1\n2\n3",
            student_predicted="完全不同",
        )
    assert result.passed is False
    assert result.match_method == "mismatch"
    assert result.feedback is None


@pytest.mark.asyncio
async def test_grade_semantic_llm_exception_falls_back_to_mismatch():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(side_effect=RuntimeError("openai down"))
    with patch("services.comprehension.predict_output._get_client", return_value=client):
        result = await grade_predict_answer(
            student_code="x",
            test_input="3\n",
            expected_output="1\n2\n3",
            student_predicted="completely off",
        )
    assert result.passed is False
    assert result.match_method == "mismatch"
