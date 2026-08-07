"""Feedback 層 — `build_system_prompt` 單元測試（含 RAG block 注入）。"""

from services.edf.prompt_blocks import build_system_prompt
from tests.feedback_factories import make_chunk, make_evidence, make_strategy

# === 基本 prompt 結構 ===

def test_system_prompt_contains_preamble():
    prompt = build_system_prompt(make_evidence(), make_strategy())
    assert "RULE-1" in prompt
    assert "RULE-5" in prompt


def test_system_prompt_contains_strategy():
    prompt = build_system_prompt(make_evidence(), make_strategy(reveal=3))
    assert "揭露等級 3/5" in prompt
    assert "說明深度：" in prompt


def test_low_reveal_guard_targets_the_learning_objective():
    """7-C4：低揭露等級要守的是「目標概念的推理」，不是「凡規則都不能講」。

    實測依據：閏年題屬 if-else 章節，閏年定義是背景設定——原措辭「禁止把所有
    判斷條件一次寫完」與教學意圖衝突，Coddy 照做反而增加無關的認知負荷。
    """
    prompt = build_system_prompt(make_evidence(), make_strategy(reveal=1))
    assert "control-flow" in prompt  # 目標概念要出現在防線裡
    assert "背景知識" in prompt
    assert "所有判斷條件" not in prompt  # 舊措辭已移除


def test_preamble_requires_layered_sources_and_plain_corrections():
    """7-C2b：規範來源要分層講、認錯要第一句就講。"""
    prompt = build_system_prompt(make_evidence(), make_strategy())
    assert "C++ 標準" in prompt and "本平台的判定" in prompt
    assert "禁止" in prompt and "通常" in prompt  # 明文禁用含糊帶過的措辭
    assert "我前面說錯了" in prompt


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


# Reflection block 注入


def test_system_prompt_without_reflection_has_no_block():
    prompt = build_system_prompt(make_evidence(), make_strategy())
    assert "下列反思" not in prompt


def test_system_prompt_with_reflection_includes_block():
    block = (
        "學生在動手寫程式前提交了下列反思（反思品質分數：80%）：\n"
        "- 對問題的理解：找最大值\n"
        "引導建議：可引用學生計畫做蘇格拉底式提問。"
    )
    prompt = build_system_prompt(
        make_evidence(), make_strategy(), reflection_block=block
    )
    assert "找最大值" in prompt
    assert "蘇格拉底式提問" in prompt


def test_reflection_block_appears_before_rag_block():
    """規範要求 prompt 順序：context → reflection → rag。"""
    chunks = [make_chunk("教材片段：迴圈定義")]
    prompt = build_system_prompt(
        make_evidence(),
        make_strategy(),
        rag_chunks=chunks,
        reflection_block="REFLECTION_MARKER",
    )
    assert prompt.index("REFLECTION_MARKER") < prompt.index("教材參考片段")
