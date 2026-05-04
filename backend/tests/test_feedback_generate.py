"""Feedback 層 — `generate_feedback` 單元測試（LLM 呼叫 + RAG 注入路徑）。"""

from unittest.mock import AsyncMock, patch

import pytest

from core.errors import AppError
from services.edf.feedback import generate_feedback
from tests.feedback_factories import (
    make_chunk,
    make_evidence,
    make_strategy,
    mock_openai_response,
)


# === 基本 LLM 呼叫 ===

@pytest.mark.asyncio
async def test_generate_feedback_success():
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=mock_openai_response("你的迴圈條件有問題，想想什麼時候會停？"),
    )

    with patch("services.edf.feedback._get_client", return_value=mock_client):
        result = await generate_feedback(
            evidence=make_evidence(),
            strategy=make_strategy(allow_code=False),
            student_message="為什麼我的程式跑不停？",
        )

    assert "迴圈" in result
    mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_feedback_with_history():
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=mock_openai_response("很好的追問！"),
    )

    history = [
        {"role": "user", "content": "怎麼修？"},
        {"role": "assistant", "content": "先看看迴圈條件。"},
    ]

    with patch("services.edf.feedback._get_client", return_value=mock_client):
        await generate_feedback(
            evidence=make_evidence(),
            strategy=make_strategy(),
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
                evidence=make_evidence(),
                strategy=make_strategy(),
                student_message="help",
            )

    assert exc_info.value.status_code == 502


# === RAG 注入路徑 ===

@pytest.mark.asyncio
async def test_generate_feedback_fetches_rag_when_use_rag_true():
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=mock_openai_response("根據教材，先檢查迴圈條件。"),
    )
    mock_fetch = AsyncMock(return_value=[make_chunk("教材片段：迴圈三要素")])

    strategy = make_strategy(allow_code=False).model_copy(update={"use_rag": True})

    with (
        patch("services.edf.feedback._get_client", return_value=mock_client),
        patch("services.edf.feedback.fetch_rag_chunks_safe", mock_fetch),
    ):
        await generate_feedback(
            evidence=make_evidence(),
            strategy=strategy,
            student_message="為什麼跑不停？",
        )

    mock_fetch.assert_awaited_once()
    call_args = mock_client.chat.completions.create.call_args
    system_msg = call_args.kwargs["messages"][0]["content"]
    assert "教材參考片段" in system_msg
    assert "迴圈三要素" in system_msg


@pytest.mark.asyncio
async def test_generate_feedback_skips_rag_when_use_rag_false():
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=mock_openai_response("先看看迴圈條件。"),
    )
    mock_fetch = AsyncMock(return_value=[])

    with (
        patch("services.edf.feedback._get_client", return_value=mock_client),
        patch("services.edf.feedback.fetch_rag_chunks_safe", mock_fetch),
    ):
        await generate_feedback(
            evidence=make_evidence(),
            strategy=make_strategy(),  # use_rag=False (預設)
            student_message="為什麼跑不停？",
        )

    mock_fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_feedback_continues_when_rag_returns_empty():
    """RAG 失敗（fetch_rag_chunks_safe 已內部吞錯回傳空 list）時仍應正常出回覆。"""
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=mock_openai_response("沒有教材也能教。"),
    )
    mock_fetch = AsyncMock(return_value=[])  # 模擬 RAG 失敗已被吞掉

    strategy = make_strategy().model_copy(update={"use_rag": True})

    with (
        patch("services.edf.feedback._get_client", return_value=mock_client),
        patch("services.edf.feedback.fetch_rag_chunks_safe", mock_fetch),
    ):
        result = await generate_feedback(
            evidence=make_evidence(),
            strategy=strategy,
            student_message="help",
        )

    assert "沒有教材也能教" in result
    call_args = mock_client.chat.completions.create.call_args
    system_msg = call_args.kwargs["messages"][0]["content"]
    assert "教材參考片段" not in system_msg
