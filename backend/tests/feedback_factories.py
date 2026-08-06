"""Feedback 測試共用 factory — Evidence / Strategy / RetrievedChunk / OpenAI mock。"""

from unittest.mock import MagicMock

from services.edf.decision import TeachingStrategy
from services.edf.models import BloomLevel, ErrorType, EvidenceResult
from services.rag import RetrievedChunk


def make_evidence() -> EvidenceResult:
    return EvidenceResult(
        error_type=ErrorType.LOGIC,
        error_message="infinite loop",
        concept_tags=["control-flow"],
        bloom_level=BloomLevel.APPLY,
        bloom_reasoning="applying loops",
        code_analysis="while condition never becomes false",
    )


def make_strategy(reveal: int = 2, allow_code: bool = True) -> TeachingStrategy:
    return TeachingStrategy(
        reveal_level=reveal,
        instruction="L0：回答學生實際問的問題。\nL1：＋指出問題區域。\nL2：＋指出精確位置。",
        bloom_guidance="學生停在應用層：說明這個概念適用什麼情境。",
        allow_code_snippet=allow_code,
    )


def make_chunk(text: str, score: float = 0.8, doc_id: str = "doc-1") -> RetrievedChunk:
    return RetrievedChunk(text=text, score=score, doc_id=doc_id, metadata={})


def mock_openai_response(content: str) -> MagicMock:
    """模擬 openai.AsyncOpenAI.chat.completions.create 的回應結構。"""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response
