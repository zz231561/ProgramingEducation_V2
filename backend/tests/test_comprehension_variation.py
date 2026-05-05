"""Variation Challenge service unit tests（roadmap 2-6d）。

涵蓋：
- generate_variation：LLM 成功 / 各類 fallback
- grade_variation：通過 / 不通過 / fallback
- prompt 模板組裝
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.quiz import Question
from services.comprehension.variation import (
    generate_variation,
    grade_variation,
)
from services.comprehension.variation_prompts import (
    build_generate_prompt,
    build_grade_prompt,
)


def _make_coding_question() -> Question:
    return Question(
        type="coding",
        concept_tags=["arrays-strings", "control-flow"],
        bloom_level=3,
        difficulty=2,
        content={"stem": "找最大值", "starter_code": "", "test_cases": []},
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


# === prompt builders ===


def test_generate_prompt_includes_concept_and_student_code():
    q = _make_coding_question()
    s = build_generate_prompt(q, "int main() { return 0; }")
    assert "arrays-strings" in s
    assert "int main()" in s
    assert "Variation Theory" in s or "變體" in s


def test_grade_prompt_includes_test_cases_and_concept_focus():
    s = build_grade_prompt(
        variation_stem="找最小值",
        test_cases=[{"input": "3 1 4", "expected": "1"}],
        concept_focus="是否能反向應用",
        student_code="for(int i;...)",
    )
    assert "找最小值" in s
    assert "1" in s
    assert "是否能反向應用" in s
    assert "for(int i" in s


# === generate_variation ===


@pytest.mark.asyncio
async def test_generate_returns_full_payload_on_success():
    payload = {
        "stem": "找最小值",
        "starter_code": "int main() {}",
        "test_cases": [{"input": "3 1 4", "expected": "1"}],
        "concept_focus": "反向應用",
    }
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps(payload))
    )
    with patch("services.comprehension.variation._get_client", return_value=client):
        result = await generate_variation(_make_coding_question(), "int main() {}")
    assert result.stem == "找最小值"
    assert result.starter_code == "int main() {}"
    assert result.test_cases == [{"input": "3 1 4", "expected": "1"}]
    assert result.concept_focus == "反向應用"


@pytest.mark.asyncio
async def test_generate_no_client_returns_fallback():
    with patch("services.comprehension.variation._get_client", return_value=None):
        result = await generate_variation(_make_coding_question(), "x")
    assert result.stem is None
    assert result.test_cases is None


@pytest.mark.asyncio
async def test_generate_llm_exception_returns_fallback():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(side_effect=RuntimeError("openai down"))
    with patch("services.comprehension.variation._get_client", return_value=client):
        result = await generate_variation(_make_coding_question(), "x")
    assert result.stem is None


@pytest.mark.asyncio
async def test_generate_invalid_json_returns_fallback():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value=_llm_response("not json"))
    with patch("services.comprehension.variation._get_client", return_value=client):
        result = await generate_variation(_make_coding_question(), "x")
    assert result.stem is None


@pytest.mark.asyncio
async def test_generate_missing_stem_returns_fallback():
    """ValidationError when stem missing → fallback。"""
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"starter_code": "x"}))
    )
    with patch("services.comprehension.variation._get_client", return_value=client):
        result = await generate_variation(_make_coding_question(), "x")
    assert result.stem is None


# === grade_variation ===


@pytest.mark.asyncio
async def test_grade_passed_with_feedback():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({"passed": True, "feedback": "邏輯正確且應用到變體"})
        )
    )
    with patch("services.comprehension.variation._get_client", return_value=client):
        result = await grade_variation(
            "找最小值", [{"input": "3 1", "expected": "1"}], "反向應用", "code"
        )
    assert result.passed is True
    assert result.feedback == "邏輯正確且應用到變體"


@pytest.mark.asyncio
async def test_grade_failed_with_feedback():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(
            json.dumps({"passed": False, "feedback": "邊界 case 沒處理"})
        )
    )
    with patch("services.comprehension.variation._get_client", return_value=client):
        result = await grade_variation("stem", [], "focus", "code")
    assert result.passed is False
    assert result.feedback == "邊界 case 沒處理"


@pytest.mark.asyncio
async def test_grade_no_client_returns_fallback_failed():
    """LLM 不可用 → passed=False（保守 fallback，避免錯給通過）。"""
    with patch("services.comprehension.variation._get_client", return_value=None):
        result = await grade_variation("stem", [], "focus", "code")
    assert result.passed is False
    assert result.feedback is None


@pytest.mark.asyncio
async def test_grade_validation_error_returns_fallback():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"passed": "yes"}))  # 非 bool
    )
    with patch("services.comprehension.variation._get_client", return_value=client):
        result = await grade_variation("stem", [], "focus", "code")
    assert result.passed is False
    assert result.feedback is None


@pytest.mark.asyncio
async def test_grade_empty_feedback_normalized_to_none():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"passed": True, "feedback": ""}))
    )
    with patch("services.comprehension.variation._get_client", return_value=client):
        result = await grade_variation("stem", [], "focus", "code")
    assert result.passed is True
    assert result.feedback is None
