"""EPL service unit tests（roadmap 2-6b）— prompt 組裝 + LLM fallback + parsing。

整合（HTTP）測試見 test_comprehension_epl_route.py。
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.quiz import Question, StudentAnswer
from services.comprehension.epl import (
    EPL_PASS_THRESHOLD,
    generate_epl_prompt,
    grade_epl_answer,
)
from services.comprehension.epl_prompts import (
    build_generate_prompt,
    build_grade_prompt,
    format_student_answer,
)


def _make_question(qtype: str = "coding", **content_overrides) -> Question:
    base_content = {
        "coding": {"stem": "找出最大值", "starter_code": ""},
        "multiple_choice": {
            "stem": "選 int 大小",
            "options": ["2", "4", "8"],
            "answer_index": 1,
        },
        "fill_blank": {"stem": "補 main 函式", "blanks": ["___"], "answers": ["int"]},
    }
    return Question(
        type=qtype,
        concept_tags=["arrays-strings"],
        bloom_level=3,
        difficulty=2,
        content={**base_content[qtype], **content_overrides},
        explanation="",
        source="generated",
        validated=True,
    )


def _make_answer(payload: dict, *, is_correct: bool = True) -> StudentAnswer:
    """建 StudentAnswer 物件（不入 DB，純 in-memory 測試）。"""
    a = StudentAnswer(
        question_id=None,  # 測試不用
        user_id=None,
        answer=payload,
        is_correct=is_correct,
        time_spent_seconds=10,
        hint_level_used=0,
        feedback="",
    )
    return a


def _llm_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# === format_student_answer ===


def test_format_coding_includes_code_block():
    q = _make_question("coding")
    a = _make_answer({"code": "int x = 1;"})
    out = format_student_answer(q, a)
    assert "```cpp" in out
    assert "int x = 1;" in out
    assert "是否答對：True" in out


def test_format_mc_resolves_selected_to_option_text():
    q = _make_question("multiple_choice")
    a = _make_answer({"selected": 1})
    out = format_student_answer(q, a)
    assert "第 1 項 — 4" in out


def test_format_mc_invalid_index_falls_back():
    q = _make_question("multiple_choice")
    a = _make_answer({"selected": 99})
    out = format_student_answer(q, a)
    assert "（無）" in out


def test_format_fill_blank():
    q = _make_question("fill_blank")
    a = _make_answer({"answers": ["int"]})
    out = format_student_answer(q, a)
    assert '"int"' in out


# === build_generate_prompt / build_grade_prompt ===


def test_generate_prompt_mentions_concept_and_bloom():
    q = _make_question("coding")
    a = _make_answer({"code": "..."})
    s = build_generate_prompt(q, a)
    assert "arrays-strings" in s
    assert "Bloom 等級：3" in s
    assert "JSON" in s


def test_grade_prompt_includes_epl_question_and_answer():
    q = _make_question("coding")
    a = _make_answer({"code": "..."})
    s = build_grade_prompt(q, a, epl_prompt="解釋你的程式做了什麼", epl_answer="從頭跑迴圈")
    assert "解釋你的程式做了什麼" in s
    assert "從頭跑迴圈" in s
    assert "conceptual_correctness" in s


# === generate_epl_prompt LLM ===


@pytest.mark.asyncio
async def test_generate_returns_prompt_on_success():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"prompt": "請用自己的話解釋你的解法"}))
    )
    with patch("services.comprehension.epl._get_client", return_value=client):
        result = await generate_epl_prompt(_make_question(), _make_answer({"code": "x"}))
    assert result.prompt == "請用自己的話解釋你的解法"


@pytest.mark.asyncio
async def test_generate_no_client_returns_none():
    with patch("services.comprehension.epl._get_client", return_value=None):
        result = await generate_epl_prompt(_make_question(), _make_answer({"code": "x"}))
    assert result.prompt is None


@pytest.mark.asyncio
async def test_generate_llm_exception_returns_none():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(side_effect=RuntimeError("openai down"))
    with patch("services.comprehension.epl._get_client", return_value=client):
        result = await generate_epl_prompt(_make_question(), _make_answer({"code": "x"}))
    assert result.prompt is None


@pytest.mark.asyncio
async def test_generate_invalid_json_returns_none():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value=_llm_response("not json"))
    with patch("services.comprehension.epl._get_client", return_value=client):
        result = await generate_epl_prompt(_make_question(), _make_answer({"code": "x"}))
    assert result.prompt is None


@pytest.mark.asyncio
async def test_generate_empty_prompt_returns_none():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"prompt": "  "}))
    )
    with patch("services.comprehension.epl._get_client", return_value=client):
        result = await generate_epl_prompt(_make_question(), _make_answer({"code": "x"}))
    assert result.prompt is None


# === grade_epl_answer LLM ===


@pytest.mark.asyncio
async def test_grade_passed_when_avg_above_threshold():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({
            "conceptual_correctness": 0.8,
            "specificity": 0.7,
            "causality": 0.6,
            "feedback": "概念清楚",
        }))
    )
    with patch("services.comprehension.epl._get_client", return_value=client):
        result = await grade_epl_answer(
            _make_question(), _make_answer({"code": "x"}), "提示", "回答"
        )
    assert result.passed is True
    assert result.conceptual_correctness == 0.8
    assert result.feedback == "概念清楚"
    assert (0.8 + 0.7 + 0.6) / 3 >= EPL_PASS_THRESHOLD


@pytest.mark.asyncio
async def test_grade_failed_when_avg_below_threshold():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({
            "conceptual_correctness": 0.4,
            "specificity": 0.3,
            "causality": 0.5,
            "feedback": "再具體一點",
        }))
    )
    with patch("services.comprehension.epl._get_client", return_value=client):
        result = await grade_epl_answer(
            _make_question(), _make_answer({"code": "x"}), "提示", "我寫了程式"
        )
    assert result.passed is False
    assert result.feedback == "再具體一點"


@pytest.mark.asyncio
async def test_grade_no_client_returns_fallback():
    with patch("services.comprehension.epl._get_client", return_value=None):
        result = await grade_epl_answer(
            _make_question(), _make_answer({"code": "x"}), "提示", "回答"
        )
    assert result.passed is None
    assert result.conceptual_correctness is None
    assert result.feedback is None


@pytest.mark.asyncio
async def test_grade_validation_error_returns_fallback():
    """LLM 回的 JSON 缺欄位 / 超界 → ValidationError → fallback。"""
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({"conceptual_correctness": 1.5}))  # 超界
    )
    with patch("services.comprehension.epl._get_client", return_value=client):
        result = await grade_epl_answer(
            _make_question(), _make_answer({"code": "x"}), "提示", "回答"
        )
    assert result.passed is None


@pytest.mark.asyncio
async def test_grade_empty_feedback_normalized_to_none():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        return_value=_llm_response(json.dumps({
            "conceptual_correctness": 0.9,
            "specificity": 0.9,
            "causality": 0.9,
            "feedback": "",
        }))
    )
    with patch("services.comprehension.epl._get_client", return_value=client):
        result = await grade_epl_answer(
            _make_question(), _make_answer({"code": "x"}), "提示", "回答"
        )
    assert result.passed is True
    assert result.feedback is None
