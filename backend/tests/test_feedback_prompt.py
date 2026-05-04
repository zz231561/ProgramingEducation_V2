"""Feedback 層 — `build_system_prompt` 單元測試（含 RAG block 注入）。"""

from services.edf.feedback import build_system_prompt
from tests.feedback_factories import make_chunk, make_evidence, make_strategy


# === 基本 prompt 結構 ===

def test_system_prompt_contains_preamble():
    prompt = build_system_prompt(make_evidence(), make_strategy())
    assert "RULE-1" in prompt
    assert "RULE-5" in prompt


def test_system_prompt_contains_strategy():
    prompt = build_system_prompt(make_evidence(), make_strategy(hint=3))
    assert "3/5" in prompt


def test_system_prompt_contains_evidence():
    prompt = build_system_prompt(make_evidence(), make_strategy())
    assert "infinite loop" in prompt
    assert "control-flow" in prompt
    assert "APPLY" in prompt


# === RAG block 注入 ===

def test_system_prompt_without_rag_has_no_rag_block():
    prompt = build_system_prompt(make_evidence(), make_strategy())
    assert "教材參考片段" not in prompt


def test_system_prompt_with_rag_includes_chunks():
    chunks = [
        make_chunk("迴圈條件需在某個時間點變為 false 才會停止。"),
        make_chunk("常見的無窮迴圈成因：忘記在迴圈體內更新計數器。"),
    ]
    prompt = build_system_prompt(make_evidence(), make_strategy(), rag_chunks=chunks)
    assert "教材參考片段" in prompt
    assert "[1]" in prompt and "[2]" in prompt
    assert "迴圈條件需在某個時間點變為 false" in prompt
    assert "忘記在迴圈體內更新計數器" in prompt


def test_system_prompt_with_empty_rag_list_omits_block():
    """空 list 應視為「沒有 RAG」，不要印出空白 RAG 區塊。"""
    prompt = build_system_prompt(make_evidence(), make_strategy(), rag_chunks=[])
    assert "教材參考片段" not in prompt
