"""6-3c 測試：影片知識點萃取。"""

import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.errors import AppError
from models.concept import Concept
from services.quiz.knowledge_points import extract_knowledge_points
from services.rag.retrieve import RetrievedChunk


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
    client = AsyncMock()
    if isinstance(content, Exception):
        client.chat.completions.create = AsyncMock(side_effect=content)
    else:
        client.chat.completions.create = AsyncMock(
            return_value=_mock_completion(content)
        )
    with patch(
        "services.quiz.knowledge_points._get_client", return_value=client
    ):
        yield client


def _concept() -> Concept:
    return Concept(
        tag="cpp-08-variables",
        name_zh="C++的變數",
        name_en="Variables",
        description="",
        difficulty_level=2,
        category="基礎",
        video_order=8,
    )


def _chunks() -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            text="[00:09] 變數是可以儲存資料的地方",
            score=1.0,
            doc_id="d1",
            metadata={"video_order": 8},
        ),
    ]


@pytest.mark.asyncio
async def test_extracts_points_list():
    payload = {"points": ["變數需先宣告再使用", "指定運算子把右值存入左邊變數"]}
    with patched_llm(json.dumps(payload)):
        points = await extract_knowledge_points(_concept(), _chunks())
    assert points == ["變數需先宣告再使用", "指定運算子把右值存入左邊變數"]


@pytest.mark.asyncio
async def test_caps_at_max_points():
    payload = {"points": [f"點{i}" for i in range(12)]}
    with patched_llm(json.dumps(payload)):
        points = await extract_knowledge_points(_concept(), _chunks())
    assert len(points) <= 8


@pytest.mark.asyncio
async def test_strips_blank_points():
    payload = {"points": ["有效知識點", "   "]}
    with patched_llm(json.dumps(payload)):
        points = await extract_knowledge_points(_concept(), _chunks())
    assert points == ["有效知識點"]


@pytest.mark.asyncio
async def test_llm_failure_raises_503():
    with patched_llm(RuntimeError("network")):
        with pytest.raises(AppError) as exc:
            await extract_knowledge_points(_concept(), _chunks())
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_invalid_json_raises_502():
    with patched_llm("not json"):
        with pytest.raises(AppError) as exc:
            await extract_knowledge_points(_concept(), _chunks())
    assert exc.value.status_code == 502
