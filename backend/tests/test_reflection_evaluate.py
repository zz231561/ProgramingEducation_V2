"""Reflection evaluate.py 單元測試（roadmap 2-5b）。

Mock OpenAI client 與 settings；驗證 LLM 回應解析、threshold 行為、容錯路徑。
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from models.quiz import Question
from models.reflection import Reflection, ReflectionSourceType
from services.reflection import evaluate as eval_module
from services.reflection.evaluate import (
    QUALITY_THRESHOLD,
    ReflectionEvaluation,
    evaluate_reflection,
)


def _make_reflection(
    *,
    problem_understanding: str = "了解問題",
    planned_steps: list[str] | None = None,
    expected_concepts: str = "syntax-basic",
    followup_answer: str | None = None,
    source_type: ReflectionSourceType = ReflectionSourceType.QUIZ,
) -> Reflection:
    return Reflection(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        source_type=source_type.value,
        source_id=uuid.uuid4(),
        problem_understanding=problem_understanding,
        planned_steps=planned_steps or ["a", "b"],
        expected_concepts=expected_concepts,
        followup_answer=followup_answer,
    )


def _make_question(bloom_level: int = 3) -> Question:
    return Question(
        id=uuid.uuid4(),
        type="multiple_choice",
        concept_tags=["syntax-basic"],
        bloom_level=bloom_level,
        difficulty=1,
        content={"stem": "宣告整數變數？", "options": ["int x;"], "answer_index": 0},
        explanation="",
        source="generated",
        validated=True,
    )


def _mock_completion(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _mock_client(content: str) -> MagicMock:
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value=_mock_completion(content))
    return client


def _reset_client_cache() -> None:
    """每次測試前清快取 client，避免 fixture 殘留。"""
    eval_module._client = None


# === 評分行為 ===


async def test_evaluate_high_quality_drops_followup_even_if_llm_returns_one():
    """quality >= threshold → followup_question 一律被清成 None（避免 LLM 多嘴）。"""
    _reset_client_cache()
    payload = json.dumps({
        "understanding_score": 0.9,
        "understanding_reason": "ok",
        "plan_quality_score": 0.85,
        "plan_quality_reason": "ok",
        "concept_recall_score": 0.8,
        "concept_recall_reason": "ok",
        "followup_question": "（LLM 多嘴的追問）",
    })
    with patch.object(
        eval_module, "_get_client", return_value=_mock_client(payload)
    ):
        result = await evaluate_reflection(_make_reflection(), _make_question())

    expected_avg = round((0.9 + 0.85 + 0.8) / 3, 3)
    assert result.quality_score == expected_avg
    assert expected_avg >= QUALITY_THRESHOLD
    assert result.followup_question is None


async def test_evaluate_low_quality_keeps_followup():
    _reset_client_cache()
    payload = json.dumps({
        "understanding_score": 0.2,
        "understanding_reason": "空話",
        "plan_quality_score": 0.3,
        "plan_quality_reason": "缺步驟",
        "concept_recall_score": 0.1,
        "concept_recall_reason": "亂寫",
        "followup_question": "你能更具體說明步驟嗎？",
    })
    with patch.object(
        eval_module, "_get_client", return_value=_mock_client(payload)
    ):
        result = await evaluate_reflection(_make_reflection(), _make_question())
    assert result.quality_score is not None and result.quality_score < QUALITY_THRESHOLD
    assert result.followup_question == "你能更具體說明步驟嗎？"


async def test_evaluate_low_quality_blank_followup_normalized_to_none():
    """LLM 沒給 followup（空字串）→ None，方便 caller 判斷。"""
    _reset_client_cache()
    payload = json.dumps({
        "understanding_score": 0.2,
        "understanding_reason": "x",
        "plan_quality_score": 0.2,
        "plan_quality_reason": "x",
        "concept_recall_score": 0.2,
        "concept_recall_reason": "x",
        "followup_question": "   ",
    })
    with patch.object(
        eval_module, "_get_client", return_value=_mock_client(payload)
    ):
        result = await evaluate_reflection(_make_reflection(), _make_question())
    assert result.followup_question is None


async def test_evaluate_threshold_adapts_to_bloom():
    """Bloom 自適應：同一組分數（平均 0.42）低 Bloom 放行、高 Bloom 追問。"""
    payload = json.dumps({
        "understanding_score": 0.5,
        "understanding_reason": "ok",
        "plan_quality_score": 0.4,
        "plan_quality_reason": "ok",
        "concept_recall_score": 0.36,
        "concept_recall_reason": "ok",
        "followup_question": "追問",
    })
    # avg = 0.42：Bloom 1（門檻 0.4）→ 放行
    _reset_client_cache()
    with patch.object(
        eval_module, "_get_client", return_value=_mock_client(payload)
    ):
        low = await evaluate_reflection(_make_reflection(), _make_question(1))
    assert low.followup_question is None
    # Bloom 5（門檻 0.55）→ 保留追問
    _reset_client_cache()
    with patch.object(
        eval_module, "_get_client", return_value=_mock_client(payload)
    ):
        high = await evaluate_reflection(_make_reflection(), _make_question(5))
    assert high.followup_question == "追問"


# === 容錯 ===


async def test_evaluate_no_api_key_returns_fallback():
    """無 API key → fallback；不 raise（不擋反思寫入）。"""
    _reset_client_cache()
    with patch.object(eval_module.settings, "OPENAI_API_KEY", ""):
        result = await evaluate_reflection(_make_reflection(), _make_question())
    assert result == ReflectionEvaluation(None, None, None, None, None)


async def test_evaluate_llm_exception_returns_fallback():
    _reset_client_cache()
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(side_effect=RuntimeError("network down"))
    with patch.object(eval_module, "_get_client", return_value=client):
        result = await evaluate_reflection(_make_reflection(), _make_question())
    assert result.quality_score is None
    assert result.followup_question is None


async def test_evaluate_invalid_json_returns_fallback():
    _reset_client_cache()
    with patch.object(
        eval_module, "_get_client", return_value=_mock_client("not json {")
    ):
        result = await evaluate_reflection(_make_reflection(), _make_question())
    assert result.quality_score is None


async def test_evaluate_schema_violation_returns_fallback():
    """LLM 漏欄位 → Pydantic ValidationError → fallback。"""
    _reset_client_cache()
    payload = json.dumps({"understanding_score": 0.9})  # 缺 plan_quality_score 等
    with patch.object(
        eval_module, "_get_client", return_value=_mock_client(payload)
    ):
        result = await evaluate_reflection(_make_reflection(), _make_question())
    assert result.quality_score is None


async def test_evaluate_score_out_of_range_returns_fallback():
    """LLM 把分數寫超出 0–1 → Pydantic ge/le 校驗失敗 → fallback。"""
    _reset_client_cache()
    payload = json.dumps({
        "understanding_score": 1.5,  # 違反 le=1.0
        "understanding_reason": "x",
        "plan_quality_score": 0.5,
        "plan_quality_reason": "x",
        "concept_recall_score": 0.5,
        "concept_recall_reason": "x",
        "followup_question": None,
    })
    with patch.object(
        eval_module, "_get_client", return_value=_mock_client(payload)
    ):
        result = await evaluate_reflection(_make_reflection(), _make_question())
    assert result.quality_score is None


async def test_evaluate_learning_unit_works_without_question():
    """learning_unit 來源不需題目脈絡也能評分。"""
    _reset_client_cache()
    payload = json.dumps({
        "understanding_score": 0.7,
        "understanding_reason": "ok",
        "plan_quality_score": 0.7,
        "plan_quality_reason": "ok",
        "concept_recall_score": 0.7,
        "concept_recall_reason": "ok",
        "followup_question": None,
    })
    reflection = _make_reflection(source_type=ReflectionSourceType.LEARNING_UNIT)
    with patch.object(
        eval_module, "_get_client", return_value=_mock_client(payload)
    ):
        result = await evaluate_reflection(reflection, None)
    assert result.quality_score == 0.7
