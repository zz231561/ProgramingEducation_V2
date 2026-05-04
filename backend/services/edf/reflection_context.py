"""Reflection → prompt block 格式化（Phase 2-5e）。

把 `Reflection` model 渲染成可注入 EDF Pipeline 各層的字串：
- `format_reflection_for_evidence`：簡短版，給 Evidence LLM 判斷 Bloom / concept_tags 用
- `format_reflection_for_feedback`：詳細版，給 Feedback LLM 引用學生計畫做蘇格拉底式提問

設計取捨：
- 純函式（無 DB / LLM 呼叫），方便單元測試
- `None` / 缺欄位 → 回 `""`，caller 直接 `if block: ...` 判斷是否注入
- 不帶 `quality_score` 過低的 fallback：即使學生反思品質差，AI 也應該知道內容
  以便「指出問題」，而不是假裝沒這份反思
"""

from models.reflection import Reflection


def _planned_steps_block(steps: list[str]) -> str:
    """步驟列表渲染成多行 1./2./3. 格式；空列表回空字串。"""
    cleaned = [s.strip() for s in steps if s and s.strip()]
    if not cleaned:
        return ""
    return "\n".join(f"  {i}. {s}" for i, s in enumerate(cleaned, 1))


def format_reflection_for_evidence(reflection: Reflection | None) -> str:
    """Evidence 層用簡短版 — 只給「步驟 + 預期概念」協助 LLM 判斷學生意圖。

    在 user prompt 結尾注入；過長會稀釋 LLM 對程式碼的關注。
    """
    if reflection is None:
        return ""

    steps_block = _planned_steps_block(reflection.planned_steps)
    expected = (reflection.expected_concepts or "").strip()
    if not steps_block and not expected:
        return ""

    parts = ["學生在動手前提交了反思計畫，可協助你判斷其 Bloom 等級與意圖："]
    if steps_block:
        parts.append("解題步驟：\n" + steps_block)
    if expected:
        parts.append(f"預期會用到的概念：{expected}")
    return "\n".join(parts)


def format_reflection_for_feedback(reflection: Reflection | None) -> str:
    """Feedback 層用詳細版 — 含完整反思內容，供 AI 引用。

    回傳的 block 會被 caller 直接放進 system prompt 的 reflection 區塊。
    """
    if reflection is None:
        return ""

    understanding = (reflection.problem_understanding or "").strip()
    expected = (reflection.expected_concepts or "").strip()
    steps_block = _planned_steps_block(reflection.planned_steps)
    followup_answer = (reflection.followup_answer or "").strip()

    if not understanding and not expected and not steps_block:
        return ""

    score = reflection.quality_score
    score_label = (
        f"（反思品質分數：{int(round(score * 100))}%）" if score is not None else ""
    )

    lines = [
        f"學生在動手寫程式前提交了下列反思{score_label}：",
    ]
    if understanding:
        lines.append(f"- 對問題的理解：{understanding}")
    if steps_block:
        lines.append("- 解題步驟：\n" + steps_block)
    if expected:
        lines.append(f"- 預期會用到的概念：{expected}")
    if followup_answer:
        lines.append(f"- 對追問的補充回答：{followup_answer}")

    lines.append(
        "引導建議：可引用學生計畫做蘇格拉底式提問（例如「你前面說要用 X，可以更具體嗎？」"
        "或「你規劃用 X，但實作上看起來是 Y，差在哪？」）。"
        "嚴禁直接幫學生補完計畫；繼續用提問引導其自主思考。"
    )
    return "\n".join(lines)
