"""Feedback 層單元測試 — prompt 組裝 + 輸出驗證 + LLM 呼叫。"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from services.edf.feedback import (
    build_system_prompt,
    validate_output,
    generate_feedback,
    PREAMBLE,
)
from services.edf.models import EvidenceResult, BloomLevel, ErrorType
from services.edf.decision import TeachingStrategy
from core.errors import AppError


def _evidence() -> EvidenceResult:
    return EvidenceResult(
        error_type=ErrorType.LOGIC,
        error_message="infinite loop",
        concept_tags=["control-flow"],
        bloom_level=BloomLevel.APPLY,
        bloom_reasoning="applying loops",
        code_analysis="while condition never becomes false",
    )


def _strategy(hint: int = 2, allow_code: bool = True) -> TeachingStrategy:
    return TeachingStrategy(
        hint_level=hint,
        instruction="指出具體位置 + 概念名稱",
        allow_code_snippet=allow_code,
        use_rag=False,
    )


# === build_system_prompt ===

def test_system_prompt_contains_preamble():
    prompt = build_system_prompt(_evidence(), _strategy())
    assert "RULE-1" in prompt
    assert "RULE-5" in prompt


def test_system_prompt_contains_strategy():
    prompt = build_system_prompt(_evidence(), _strategy(hint=3))
    assert "3/5" in prompt


def test_system_prompt_contains_evidence():
    prompt = build_system_prompt(_evidence(), _strategy())
    assert "infinite loop" in prompt
    assert "control-flow" in prompt
    assert "APPLY" in prompt


# === validate_output ===

def test_validate_removes_code_when_not_allowed():
    text = "看看這個：\n```cpp\nint x = 1;\n```\n試試看"
    result = validate_output(text, allow_code=False)
    assert "int x" not in result
    assert "已移除" in result


def test_validate_keeps_short_code():
    text = "提示：\n```cpp\nif (p != nullptr) {\n    // TODO: 處理 p\n}\n```"
    result = validate_output(text, allow_code=True)
    assert "TODO" in result
    assert result == text


def test_validate_truncates_long_code_without_guard():
    lines = "\n".join([f"int x{i} = {i};" for i in range(12)])
    text = f"看這個：\n```cpp\n{lines}\n```"
    result = validate_output(text, allow_code=True)
    assert "請自己完成" in result
    assert "int x11" not in result


def test_validate_keeps_long_code_with_todo():
    lines = "\n".join([f"int x{i} = {i};" for i in range(12)])
    lines += "\n// TODO: 補上回傳值"
    text = f"框架：\n```cpp\n{lines}\n```"
    result = validate_output(text, allow_code=True)
    assert "TODO" in result
    assert result == text


def test_validate_no_code_blocks():
    text = "你覺得第 6 行會發生什麼？試著追蹤變數 x 的值。"
    result = validate_output(text, allow_code=True)
    assert result == text


# === generate_feedback ===

def _mock_openai_response(content: str) -> MagicMock:
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.mark.asyncio
async def test_generate_feedback_success():
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_mock_openai_response("你的迴圈條件有問題，想想什麼時候會停？"),
    )

    with patch("services.edf.feedback._get_client", return_value=mock_client):
        result = await generate_feedback(
            evidence=_evidence(),
            strategy=_strategy(allow_code=False),
            student_message="為什麼我的程式跑不停？",
        )

    assert "迴圈" in result
    mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_feedback_with_history():
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_mock_openai_response("很好的追問！"),
    )

    history = [
        {"role": "user", "content": "怎麼修？"},
        {"role": "assistant", "content": "先看看迴圈條件。"},
    ]

    with patch("services.edf.feedback._get_client", return_value=mock_client):
        result = await generate_feedback(
            evidence=_evidence(),
            strategy=_strategy(),
            student_message="我看了，但還是不懂",
            chat_history=history,
        )

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    # system + 2 history + 1 user = 4
    assert len(messages) == 4


@pytest.mark.asyncio
async def test_generate_feedback_llm_error():
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("timeout"))

    with patch("services.edf.feedback._get_client", return_value=mock_client):
        with pytest.raises(AppError) as exc_info:
            await generate_feedback(
                evidence=_evidence(),
                strategy=_strategy(),
                student_message="help",
            )

    assert exc_info.value.status_code == 502
