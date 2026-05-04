"""reflection_context 格式化測試（roadmap 2-5e）。

純函式測試 — 確認 Reflection → prompt block 的兩種視圖（Evidence 簡短 / Feedback 詳細）。
"""

import uuid

from models.reflection import Reflection, ReflectionSourceType
from services.edf.reflection_context import (
    format_reflection_for_evidence,
    format_reflection_for_feedback,
)


def _make_reflection(
    *,
    problem_understanding: str = "找第 K 大的整數",
    planned_steps: list[str] | None = None,
    expected_concepts: str = "迴圈、排序",
    followup_answer: str | None = None,
    quality_score: float | None = 0.78,
) -> Reflection:
    return Reflection(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        source_type=ReflectionSourceType.QUIZ.value,
        source_id=uuid.uuid4(),
        problem_understanding=problem_understanding,
        planned_steps=planned_steps if planned_steps is not None else ["讀入 N", "排序", "輸出第 K"],
        expected_concepts=expected_concepts,
        followup_answer=followup_answer,
        quality_score=quality_score,
    )


# === None / 空輸入 ===


def test_evidence_format_none_returns_empty():
    assert format_reflection_for_evidence(None) == ""


def test_feedback_format_none_returns_empty():
    assert format_reflection_for_feedback(None) == ""


def test_evidence_empty_steps_and_concepts_returns_empty():
    """步驟全空且無 expected_concepts → 不注入（避免無意義佔 prompt）。"""
    r = _make_reflection(planned_steps=["", "  "], expected_concepts="")
    assert format_reflection_for_evidence(r) == ""


def test_feedback_empty_all_returns_empty():
    r = _make_reflection(
        problem_understanding="",
        planned_steps=[""],
        expected_concepts="",
    )
    assert format_reflection_for_feedback(r) == ""


# === Evidence 簡短版 ===


def test_evidence_includes_steps_and_concepts():
    block = format_reflection_for_evidence(_make_reflection())
    assert "解題步驟" in block
    assert "1. 讀入 N" in block
    assert "2. 排序" in block
    assert "3. 輸出第 K" in block
    assert "迴圈、排序" in block
    # Evidence 簡短版不含品質分數 / followup（避免稀釋程式碼分析）
    assert "78%" not in block
    assert "對問題的理解" not in block


def test_evidence_skips_empty_steps_in_list():
    """中間有空字串時應 trim 並重新編號。"""
    r = _make_reflection(planned_steps=["第一步", "", "  ", "第二步"])
    block = format_reflection_for_evidence(r)
    assert "1. 第一步" in block
    assert "2. 第二步" in block
    # 不應該有「3.」因為只有兩個有效步驟
    assert "3. " not in block


# === Feedback 詳細版 ===


def test_feedback_includes_full_content():
    block = format_reflection_for_feedback(_make_reflection())
    assert "對問題的理解：找第 K 大的整數" in block
    assert "解題步驟" in block
    assert "1. 讀入 N" in block
    assert "預期會用到的概念：迴圈、排序" in block
    # 含品質分數
    assert "78%" in block
    # 含蘇格拉底式提問引導建議
    assert "嚴禁直接幫學生補完計畫" in block


def test_feedback_includes_followup_when_present():
    r = _make_reflection(followup_answer="補充：要先檢查 K 是否合法")
    block = format_reflection_for_feedback(r)
    assert "對追問的補充回答：補充：要先檢查 K 是否合法" in block


def test_feedback_omits_followup_when_absent():
    r = _make_reflection(followup_answer=None)
    block = format_reflection_for_feedback(r)
    assert "對追問的補充回答" not in block


def test_feedback_no_quality_score_omits_label():
    """quality_score=None 時不顯示百分比（避免出現「（反思品質分數：%）」這種怪格式）。"""
    r = _make_reflection(quality_score=None)
    block = format_reflection_for_feedback(r)
    assert "%" not in block
    # 仍應有「下列反思」開頭
    assert "下列反思" in block


def test_feedback_quality_score_zero_displays_zero_percent():
    r = _make_reflection(quality_score=0.0)
    block = format_reflection_for_feedback(r)
    assert "0%" in block
