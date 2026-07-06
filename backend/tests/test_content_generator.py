"""Phase 6-2a 單元測試：grounded prompt + Pydantic 模型。

涵蓋（U2b 移除 summary、U2g 2026-07-06 晚間移除 code_examples，相關測試同步刪除）：
- concept_explanation 正確解析 LLM JSON
- needs_more_source=true 路徑（transcript 不足時不 hallucinate）
- LLM 拋例外 → 503 LLM_UNAVAILABLE
- LLM 回非 JSON → 502 LLM_PARSE_ERROR
- LLM 回 schema 不符 → 502 LLM_PARSE_ERROR
- _build_context_block 確實注入 transcript chunks（grounding 機制驗證）
- generate_unit_content orchestrator 僅 1 LLM call
"""

import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.errors import AppError
from models.concept import Concept
from services.learning.content_generator import (
    Citation,
    ConceptExplanation,
    UnitContent,
    _build_context_block,
    generate_concept_explanation,
    generate_unit_content,
)
from services.rag.retrieve import RetrievedChunk


def _fake_concept() -> Concept:
    return Concept(
        tag="cpp-47-recursion",
        name_zh="C++的遞迴函式",
        name_en="Recursive Functions",
        description="",
        difficulty_level=4,
        category="函式",
        video_order=47,
    )


def _fake_chunks() -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            text="[00:01] 各位同學大家好,我是黃國豪老師\n[00:08] 今天介紹遞迴函式",
            score=0.9,
            doc_id="d1",
            metadata={"video_order": 47, "title_zh": "C++的遞迴函式"},
        ),
        RetrievedChunk(
            text="[02:03] 五階層就是五乘以四乘以三乘以二乘以一",
            score=0.85,
            doc_id="d1",
            metadata={"video_order": 47, "title_zh": "C++的遞迴函式"},
        ),
    ]


def _mock_completion(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@contextmanager
def patched_llm(content: str | Exception):
    mock_client = AsyncMock()
    if isinstance(content, Exception):
        mock_client.chat.completions.create = AsyncMock(side_effect=content)
    else:
        mock_client.chat.completions.create = AsyncMock(
            return_value=_mock_completion(content)
        )
    with patch(
        "services.learning.content_generator._get_client",
        return_value=mock_client,
    ):
        yield mock_client


# === 2 section 成功路徑 ===


@pytest.mark.asyncio
async def test_concept_explanation_success():
    payload = {
        "needs_more_source": False,
        "reason": "",
        "markdown": "遞迴是函式呼叫自己 [00:08]，結束條件很重要 [02:03]。",
        "citations": [
            {"timestamp": "00:08", "text_excerpt": "今天介紹遞迴函式"},
            {"timestamp": "02:03", "text_excerpt": "五階層就是五乘以四..."},
        ],
    }
    with patched_llm(json.dumps(payload)):
        result = await generate_concept_explanation(_fake_concept(), _fake_chunks())
    assert isinstance(result, ConceptExplanation)
    assert result.needs_more_source is False
    assert "遞迴" in result.markdown
    assert len(result.citations) == 2
    assert result.citations[0].timestamp == "00:08"


# === needs_more_source 路徑 ===


@pytest.mark.asyncio
async def test_concept_explanation_needs_more_source():
    payload = {
        "needs_more_source": True,
        "reason": "transcript 只有 2 句問候，無實質教學內容",
        "markdown": "",
        "citations": [],
    }
    with patched_llm(json.dumps(payload)):
        result = await generate_concept_explanation(_fake_concept(), _fake_chunks())
    assert result.needs_more_source is True
    assert "問候" in result.reason
    assert result.markdown == ""


# === 失敗路徑 ===


@pytest.mark.asyncio
async def test_llm_unavailable_raises_503():
    with patched_llm(RuntimeError("network error")):
        with pytest.raises(AppError) as exc:
            await generate_concept_explanation(_fake_concept(), _fake_chunks())
    assert exc.value.status_code == 503
    assert exc.value.error == "LLM_UNAVAILABLE"


@pytest.mark.asyncio
async def test_llm_returns_invalid_json_raises_502():
    with patched_llm("這不是 JSON"):
        with pytest.raises(AppError) as exc:
            await generate_concept_explanation(_fake_concept(), _fake_chunks())
    assert exc.value.status_code == 502
    assert exc.value.error == "LLM_PARSE_ERROR"


@pytest.mark.asyncio
async def test_llm_returns_wrong_schema_raises_502():
    # citation text_excerpt 超過 max_length=120 → ValidationError
    bad_payload = {
        "needs_more_source": False,
        "reason": "",
        "markdown": "x",
        "citations": [{"timestamp": "00:01", "text_excerpt": "x" * 121}],
    }
    with patched_llm(json.dumps(bad_payload)):
        with pytest.raises(AppError) as exc:
            await generate_concept_explanation(_fake_concept(), _fake_chunks())
    assert exc.value.error == "LLM_PARSE_ERROR"


# === Grounding 機制驗證 ===


def test_context_block_includes_transcript_chunks():
    """關鍵驗證：prompt 真的注入 transcript chunks（grounding 來源）。"""
    block = _build_context_block(_fake_concept(), _fake_chunks())
    assert "[chunk 1]" in block
    assert "[chunk 2]" in block
    assert "黃國豪老師" in block
    assert "五階層" in block
    assert "concept tag: cpp-47-recursion" in block
    assert "影片編號：47" in block


def test_context_block_empty_chunks_marked():
    """無 chunks → 標記引導 LLM 設 needs_more_source。"""
    block = _build_context_block(_fake_concept(), [])
    assert "needs_more_source=true" in block


@pytest.mark.asyncio
async def test_prompt_actually_passed_to_llm():
    """確認 chunks 內容真的進到 LLM call（end-to-end grounding chain）。"""
    payload = {
        "needs_more_source": False, "reason": "", "markdown": "x",
        "citations": [{"timestamp": "00:01", "text_excerpt": "y"}],
    }
    with patched_llm(json.dumps(payload)) as mock_client:
        await generate_concept_explanation(_fake_concept(), _fake_chunks())
        call_args = mock_client.chat.completions.create.call_args
        user_msg = call_args.kwargs["messages"][1]["content"]
        assert "黃國豪老師" in user_msg
        assert "五階層" in user_msg


# === Orchestrator ===


@pytest.mark.asyncio
async def test_generate_unit_content_single_section():
    """orchestrator 僅 1 LLM call（U2g 後只剩 concept_explanation）。"""
    concept_payload = {
        "needs_more_source": False, "reason": "", "markdown": "C",
        "citations": [{"timestamp": "00:01", "text_excerpt": "x"}],
    }
    with patched_llm(json.dumps(concept_payload)) as mock_client:
        result = await generate_unit_content(_fake_concept(), _fake_chunks())

    assert isinstance(result, UnitContent)
    assert result.concept_explanation.markdown == "C"
    assert mock_client.chat.completions.create.call_count == 1


# === Citation 模型 ===


def test_citation_text_excerpt_max_length():
    """Citation 的 excerpt 應限制 ≤120 字以避免吃太多 tokens。"""
    long_text = "x" * 121
    with pytest.raises(Exception):  # ValidationError
        Citation(timestamp="00:01", text_excerpt=long_text)
