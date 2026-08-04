"""離題分流測試 — 分流不是攔截：學生一律收到回應，只是走輕量路徑。"""

from unittest.mock import AsyncMock, patch

import pytest

from services.edf.decision import TeachingStrategy
from services.edf.feedback import generate_feedback
from services.edf.models import BloomLevel, ErrorType, EvidenceResult


def _evidence(on_topic: bool) -> EvidenceResult:
    return EvidenceResult(
        error_type=ErrorType.NONE,
        error_message="",
        concept_tags=["syntax-basic"],
        bloom_level=BloomLevel.APPLY,
        bloom_reasoning="",
        code_analysis="程式碼正常",
        is_on_topic=on_topic,
    )


def _strategy() -> TeachingStrategy:
    return TeachingStrategy(
        instruction="引導學生", allow_code_snippet=False, hint_level=0
    )


def _fake_completion(text: str):
    msg = type("M", (), {"content": text})()
    choice = type("C", (), {"message": msg})()
    return type("R", (), {"choices": [choice]})()


async def test_on_topic_uses_full_pipeline():
    """課程相關 → 走完整路徑（會檢索 RAG）。"""
    with (
        patch("services.edf.feedback._get_client") as get_client,
        patch(
            "services.edf.feedback.fetch_rag_chunks_safe", new=AsyncMock(return_value=[])
        ) as rag,
    ):
        get_client.return_value.chat.completions.create = AsyncMock(
            return_value=_fake_completion("完整教學回應")
        )
        out = await generate_feedback(
            evidence=_evidence(True),
            strategy=_strategy(),
            student_message="這個迴圈為什麼不會停？",
        )
    rag.assert_awaited_once()
    assert out == "完整教學回應"


async def test_off_topic_skips_rag_and_still_replies():
    """離題 → 跳過 RAG（省成本），但學生仍收到回應（不是攔截）。"""
    with (
        patch("services.edf.feedback._get_client") as get_client,
        patch(
            "services.edf.feedback.fetch_rag_chunks_safe", new=AsyncMock(return_value=[])
        ) as rag,
        patch("services.edf.off_topic.chat_model_kwargs", return_value={"model": "m"}),
    ):
        get_client.return_value.chat.completions.create = AsyncMock(
            return_value=_fake_completion("我專門幫你學 C++ 喔")
        )
        out = await generate_feedback(
            evidence=_evidence(False),
            strategy=_strategy(),
            student_message="今天天氣如何",
        )
    rag.assert_not_awaited()  # 關鍵：沒有檢索 = 沒有 embedding 成本
    assert "C++" in out


async def test_off_topic_falls_back_to_fixed_text_on_llm_failure():
    """離題路徑 LLM 失敗不拋錯——這種情境沒必要讓學生看到錯誤畫面。"""
    with (
        patch("services.edf.feedback._get_client") as get_client,
        patch("services.edf.feedback.fetch_rag_chunks_safe", new=AsyncMock(return_value=[])),
        patch("services.edf.off_topic.chat_model_kwargs", return_value={"model": "m"}),
    ):
        get_client.return_value.chat.completions.create = AsyncMock(
            side_effect=RuntimeError("boom")
        )
        out = await generate_feedback(
            evidence=_evidence(False),
            strategy=_strategy(),
            student_message="晚餐吃什麼",
        )
    assert "C++" in out
    assert len(out) > 10


def test_is_on_topic_defaults_true():
    """LLM 未回傳該欄位時預設為課程相關——寧可多花錢也不誤判成離題。"""
    ev = EvidenceResult(
        error_type=ErrorType.NONE,
        bloom_level=BloomLevel.APPLY,
    )
    assert ev.is_on_topic is True


@pytest.mark.parametrize("question", ["這題老師上課有講嗎", "?", "這是什麼意思"])
def test_ambiguous_questions_documented_as_on_topic(question: str):
    """文件化契約：這些看似模糊的提問屬課程相關，prompt 規則明列不得判為離題。

    （實際判定由 LLM 執行，此處鎖住 SYSTEM_PROMPT 中的規則不被誤刪。）
    """
    from services.edf.evidence import SYSTEM_PROMPT

    assert "老師上課有講嗎" in SYSTEM_PROMPT
    assert "極簡短但語境上在求助" in SYSTEM_PROMPT
