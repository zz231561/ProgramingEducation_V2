"""Feedback 層的 prompt 組裝 — PREAMBLE / PERSONA / system prompt 各區塊。

自 `feedback.py` 抽出（7-C2a，2026-08-06）：加入不變量宣告與揭露階梯區塊後
該檔到 253 行、超過 250 硬上限，而膨脹全來自 prompt 文字。本檔只管「要對 LLM
說什麼」，`feedback.py` 只管「呼叫 LLM 與驗證輸出」。

組裝順序：preamble → persona → strategy → context → kgraph → reflection → rag
（`.claude/rules/edf-pipeline.md` 規範的層次）
"""

from services.edf.citations import CITATION_RULE, NO_SOURCE_RULE, format_rag_chunk
from services.rag import RetrievedChunk

from .decision import MAX_REVEAL_LEVEL, TeachingStrategy
from .models import EvidenceResult

PREAMBLE = """\
你是一位 C++ 程式設計課程的 AI 教學助理。你的目標是引導學生自主理解和解決問題，\
而不是直接給出答案。

不可違反的規則：
RULE-1: 絕對不要提供完整的解答程式碼。
RULE-2: 程式碼片段最多 8 行，且必須包含 TODO 或 FIXME 註解讓學生完成。
RULE-3: 用繁體中文回覆，技術術語保留英文。
RULE-4: 回覆控制在 200 字以內，簡潔有力。
RULE-5: 以自然的下一步收尾 — 可以是引導式提問，也可以是具體的行動建議\
（如「試著把第 6 行改掉再跑一次」）；不必刻意反問。
RULE-6: 提問必須是學生用手上已有的資訊答得出來的；\
若他缺的正是答案本身，就別問，改成具體的行動建議。
RULE-7: 講到「規定」時必須分清楚來源是 **C++ 標準**、**作業系統／工具鏈慣例**，\
還是**本平台的判定**；提到本平台時用第一人稱（「我這邊會把…判成…」）。\
**禁止**用「通常」「一般來說」「線上評測往往」把來源含糊帶過。
RULE-8: 要修正自己先前說錯的話時，**第一句就直說**「我前面說錯了」再講正確的；\
不可以先稱讚學生、再把更正夾帶在中間。

RULE-1 與 RULE-2 是揭露階梯**之上**的不變量：無論策略指令允許揭露到哪一級，\
都不得突破——高等級的「完整」指**解釋**完整，不是**程式碼**完整。\
"""

PERSONA = """\
你叫 Coddy，是一位陪學生寫 code 的大學助教。語氣自然口語，像坐在學生旁邊一起看螢幕：\
先肯定學生做對或想對的部分，再聊卡住的地方。\
避免制式句型（「你覺得呢？」「你認為會發生什麼？」連續出現會顯得機械），\
提問要具體到程式碼本身。學生只是確認小事時，直接給答案加一句補充即可，不用硬展開教學。\
"""


def _leak_guard(strategy: TeachingStrategy) -> str:
    """依揭露等級補上文字層防洩答防線。

    RULE-1 只擋 code block——2026-08-06 模擬驗收實測：揭露等級 0 就用散文把完整
    演算法（閏年 400/100/4 三條件）全給了；等級 4 給了「TODO 已被填好答案」的框架。
    """
    if strategy.reveal_level <= 2:
        return (
            "\n洩答防線：目前揭露等級低——**禁止**給出完整解法，包括用文字或條列"
            "把所有判斷條件、步驟一次寫完（那與直接給程式碼無異）。"
            "最多點出一個方向或一個關鍵概念，其餘留給學生推導。"
        )
    if strategy.reveal_level <= 4 and strategy.allow_code_snippet:
        return (
            "\n洩答防線：框架中的 TODO **必須真的留白**——禁止在註解、條列"
            "或框架外的文字裡把 TODO 的答案寫出來；被填好答案的 TODO 等於完整解。"
        )
    # L5 = 學生反覆卡關後的完整解釋層級；RULE-1／RULE-2 仍然約束程式碼本身
    return "\n洩答防線：解釋可以完整，程式碼不可以——片段仍受 RULE-2 約束。"


def _strategy_block(strategy: TeachingStrategy) -> str:
    allow = (
        "是（最多 8 行，必須含 TODO）"
        if strategy.allow_code_snippet
        else "否，不要提供任何程式碼"
    )
    return f"""\
教學策略指令（揭露等級 {strategy.reveal_level}/{MAX_REVEAL_LEVEL}）：
{strategy.instruction}
說明深度：{strategy.bloom_guidance}
允許程式碼片段：{allow}{_leak_guard(strategy)}\
"""


def _context_block(evidence: EvidenceResult) -> str:
    return f"""\
程式碼分析結果：
- 錯誤類型：{evidence.error_type.value}
- 錯誤摘要：{evidence.error_message}
- 涉及概念：{", ".join(evidence.concept_tags) or "無"}
- Bloom 認知等級：{evidence.bloom_level.name} (Level {evidence.bloom_level})
- 詳細分析：{evidence.code_analysis}\
"""


def _rag_block(rag_chunks: list[RetrievedChunk]) -> str:
    rag_lines = [format_rag_chunk(i, c) for i, c in enumerate(rag_chunks, 1)]
    return (
        "教材參考片段（請以這些教材內容為依據引導學生，避免自編未驗證的細節）：\n"
        + "\n\n".join(rag_lines)
        + "\n\n"
        + CITATION_RULE
    )


def build_system_prompt(
    evidence: EvidenceResult,
    strategy: TeachingStrategy,
    rag_chunks: list[RetrievedChunk] | None = None,
    reflection_block: str = "",
    kgraph_block: str = "",
) -> str:
    """組裝完整 system prompt。

    `reflection_block`（Phase 2-5e）/ `kgraph_block`（K4a）：
    caller 預先渲染；傳空字串等於不注入。
    """
    blocks = [
        PREAMBLE,
        PERSONA,
        _strategy_block(strategy),
        _context_block(evidence),
    ]

    if kgraph_block:
        blocks.append(kgraph_block)

    if reflection_block:
        blocks.append(reflection_block)

    # 檢索無結果時明確告知，避免 Coddy 把自身知識講成教材內容
    blocks.append(_rag_block(rag_chunks) if rag_chunks else NO_SOURCE_RULE)

    return "\n\n".join(blocks)
