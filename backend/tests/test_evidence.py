"""Evidence 層單元測試 — mock OpenAI 驗證結構化分析流程。"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from services.edf.evidence import analyze_evidence, _build_user_prompt, SYSTEM_PROMPT
from services.edf.models import EvidenceResult, BloomLevel, ErrorType, CONCEPT_TAGS
from core.errors import AppError


# === _build_user_prompt ===

def test_user_prompt_with_error():
    prompt = _build_user_prompt("int main(){}", "", "segfault", "")
    assert "```cpp" in prompt
    assert "segfault" in prompt


def test_user_prompt_success():
    prompt = _build_user_prompt("int main(){}", "Hello", "", "")
    assert "Hello" in prompt
    assert "程式執行成功" in prompt


# === SYSTEM_PROMPT ===

def test_system_prompt_contains_concept_tags():
    for tag in CONCEPT_TAGS[:5]:
        assert tag in SYSTEM_PROMPT


# === EvidenceResult model ===

def test_evidence_result_parse():
    data = {
        "error_type": "syntax",
        "error_message": "missing semicolon",
        "concept_tags": ["syntax-basic"],
        "bloom_level": 1,
        "bloom_reasoning": "student recalls syntax",
        "code_analysis": "line 5 missing semicolon",
    }
    result = EvidenceResult(**data)
    assert result.error_type == ErrorType.SYNTAX
    assert result.bloom_level == BloomLevel.REMEMBER
    assert result.concept_tags == ["syntax-basic"]


def test_evidence_result_no_error():
    data = {
        "error_type": "none",
        "error_message": "",
        "concept_tags": ["control-flow", "arrays-strings"],
        "bloom_level": 3,
        "bloom_reasoning": "applying loops to array",
        "code_analysis": "correct usage of for loop",
    }
    result = EvidenceResult(**data)
    assert result.error_type == ErrorType.NONE
    assert result.bloom_level == BloomLevel.APPLY


# === analyze_evidence ===

def _mock_openai_response(content: dict) -> MagicMock:
    """建立 mock OpenAI chat completion response。"""
    message = MagicMock()
    message.content = json.dumps(content)
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.mark.asyncio
async def test_analyze_evidence_success():
    """正常分析流程。"""
    evidence_data = {
        "error_type": "logic",
        "error_message": "infinite loop",
        "concept_tags": ["control-flow"],
        "bloom_level": 3,
        "bloom_reasoning": "applying loop construct",
        "code_analysis": "while condition never false",
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_mock_openai_response(evidence_data),
    )

    with patch("services.edf.evidence._get_client", return_value=mock_client):
        result = await analyze_evidence("while(true){}", stdout="", stderr="timeout")

    assert isinstance(result, EvidenceResult)
    assert result.error_type == ErrorType.LOGIC
    assert result.bloom_level == BloomLevel.APPLY
    assert "control-flow" in result.concept_tags


@pytest.mark.asyncio
async def test_analyze_evidence_llm_error():
    """LLM 呼叫失敗拋出 AppError 502。"""
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API down"))

    with patch("services.edf.evidence._get_client", return_value=mock_client):
        with pytest.raises(AppError) as exc_info:
            await analyze_evidence("int main(){}")

    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_analyze_evidence_bad_json():
    """LLM 回傳非 JSON 時拋出 AppError。"""
    message = MagicMock()
    message.content = "not json"
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=response)

    with patch("services.edf.evidence._get_client", return_value=mock_client):
        with pytest.raises(AppError) as exc_info:
            await analyze_evidence("int main(){}")

    assert exc_info.value.status_code == 502
