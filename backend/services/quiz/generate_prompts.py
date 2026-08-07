"""出題 Generate 階段的 prompt 組裝（自 `generate.py` 拆出，2026-08-07 code-health）。

拆分理由：prompt 內容與生成流程是**兩個獨立的變更軸**——7-C 期間大量調整 prompt
措辭時完全不需要動 LLM 呼叫與 DB 寫入流程，反之亦然。命名沿用專案既有慣例
（`comprehension/variation_prompts.py`、`edf/prompt_blocks.py`）。
"""

from typing import Any

from models.concept import Concept
from models.quiz import QuestionType

_SCHEMA_HINT_BY_TYPE = {
    QuestionType.MULTIPLE_CHOICE: (
        '{"stem": "題幹", "options": ["A...", "B...", ...], '
        '"answer_index": 正解 index (0-based), "explanation": "為何正解"}'
    ),
    QuestionType.FILL_BLANK: (
        '{"stem": "題幹（用 ___ 標示空格）", "answers": ["...", ...], '
        '"explanation": "為何此填法正確"}'
    ),
    QuestionType.CODING: (
        '{"stem": "題目敘述", "starter_code": "起始程式碼（可空）", '
        '"expected_output": "預期 stdout 或 null", "explanation": "解題思路"}'
    ),
}

_GROUNDING_RULES = """\

【Grounding 規則 - 不可違反】（本題以教授實際 YouTube 教學影片字幕為依據）
1. 題目情境（變數名稱、輸入輸出、舉例 scenario）必須與 TRANSCRIPT 出現的範例 / 命名一致
2. 嚴禁發明字幕未提到的程式碼；coding 題 starter_code 須沿用字幕示範的識別字
3. 若字幕資訊不足 → 仍須出題，但降難度回到 transcript 明確涵蓋的概念
"""


def build_system_prompt(
    concept: Concept,
    question_type: QuestionType,
    difficulty: int,
    bloom_level: int,
    grounded: bool = False,
    knowledge_point: str | None = None,
    extra_concepts: list[Concept] | None = None,
) -> str:
    """組出題 system prompt；`grounded` 時附字幕 grounding 規則。"""
    grounding_block = _GROUNDING_RULES if grounded else ""
    focus_block = (
        f"\n【本題聚焦知識點】\n{knowledge_point}\n"
        "題目必須直接測驗此知識點的理解，不可偏題。\n"
        if knowledge_point
        else ""
    )
    # 6-3d 綜合題：要求同時運用目標概念與相關概念，而非各自獨立可解
    combine_block = ""
    if extra_concepts:
        related = "、".join(f"{c.name_zh}（{c.tag}）" for c in extra_concepts)
        combine_block = (
            f"\n【綜合概念】本題須「同時」測驗目標概念與以下相關概念的關聯運用：\n"
            f"{related}\n"
            "情境要自然整合，需綜合運用這些概念才能作答；"
            "不可只是把多個獨立小題拼在一起。\n"
        )

    return f"""\
你是 C++ 程式教學題目生成助手。為以下概念生成**一題**測驗題。

目標概念：
- tag: {concept.tag}
- 名稱：{concept.name_zh} / {concept.name_en}
- 分類：{concept.category}
- 描述：{concept.description}
{combine_block}
題目參數：
- 題型：{question_type.value}
- 難度：{difficulty}/5（1=最簡單，5=最進階）
- Bloom 認知層級：{bloom_level} (1=記憶, 2=理解, 3=應用, 4=分析, 5=評估, 6=創造)

回傳**嚴格 JSON**，欄位 schema：
{_SCHEMA_HINT_BY_TYPE[question_type]}

撰寫規則：
- 全部用繁體中文，C++ 技術名詞保留英文
- 題幹具體、可單獨閱讀無需額外脈絡
- 難度與 Bloom 必須匹配（高難度配高 Bloom）
- 不可洩漏完整解答程式碼（coding 題的 starter_code 限骨架 + TODO）
- 選擇題：每個選項 < 30 字、誘答合理（不可有明顯錯選項）
- explanation 解釋為何正解（2-3 句）
- **考點必須有意義**：測驗概念理解、語法規則或程式行為；嚴禁考操作細節
  （軟體安裝步驟、介面按鈕位置、「左上角/右下角」等畫面資訊）或無關緊要的瑣碎資訊
{focus_block}{grounding_block}"""


def build_user_prompt(rag_chunks: list[Any], grounded: bool = False) -> str:
    """把 RAG chunks 組成 user prompt；無 chunks 時回退為純參數出題。"""
    if not rag_chunks:
        return "請依目標概念與題目參數出題。"
    if grounded:
        header = (
            "以下 TRANSCRIPT 為教授實際 YouTube 影片字幕（依時間順序），"
            "請以這些字幕為唯一依據出題：\n"
        )
    else:
        header = (
            "以下教材片段可供參考（請以教材內容為依據出題，避免自編未驗證的細節）：\n"
        )
    parts = [header]
    for i, chunk in enumerate(rag_chunks, 1):
        parts.append(f"[{i}] {chunk.text.strip()}")
    return "\n\n".join(parts)
