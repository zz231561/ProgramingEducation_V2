"""Reflection 品質評估 LLM service（roadmap 2-5b）。

設計（理論基礎見 references.md：PRIMM、Polya 解題四步驟、Self-explanation effect）：
- 三面向評分（皆 0.0–1.0）：
  A. understanding：學生對「題目要什麼」的重述清楚度
  B. plan_quality：planned_steps 的具體性 / 順序合理性（不是「先想想看」這種空話）
  C. concept_recall：expected_concepts 是否切題（能呼應題目實際概念）
- quality_score = 三項的平均（簡單可解釋）
- 不足時生成 followup_question — 針對 **最弱的那一面向** 出 1 個蘇格拉底式追問
- 閾值：score < `QUALITY_THRESHOLD`（0.6）才回 followup；高於即放行（followup=None）
- LLM 失敗（API down / parse error）→ 回 fallback 評估（quality_score=None, followup=None），
  caller 在 service 層 swallow，不阻擋反思寫入（與 mastery 容錯哲學一致）
"""

import json
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

from core.config import settings
from models.quiz import Question
from models.reflection import Reflection, ReflectionSourceType

# 平均分 < 此閾值才回追問；其餘放行。0.6 是文獻常用「合格門檻」（PRIMM Modify 階段門檻）
QUALITY_THRESHOLD = 0.6

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    """無 API key 直接回 None，由 caller fallback；不丟 503（避免阻擋反思寫入）。"""
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            return None
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


class _EvaluatorResponse(BaseModel):
    understanding_score: float = Field(ge=0.0, le=1.0)
    understanding_reason: str = Field(default="")
    plan_quality_score: float = Field(ge=0.0, le=1.0)
    plan_quality_reason: str = Field(default="")
    concept_recall_score: float = Field(ge=0.0, le=1.0)
    concept_recall_reason: str = Field(default="")
    followup_question: str | None = Field(default=None)


@dataclass(frozen=True)
class ReflectionEvaluation:
    """LLM 評分結果。`quality_score` 為三面向平均；None 代表評估失敗（fallback）。"""

    quality_score: float | None
    understanding_score: float | None
    plan_quality_score: float | None
    concept_recall_score: float | None
    followup_question: str | None


def _empty_evaluation() -> ReflectionEvaluation:
    """LLM 不可用 / parse 失敗的 fallback。"""
    return ReflectionEvaluation(
        quality_score=None,
        understanding_score=None,
        plan_quality_score=None,
        concept_recall_score=None,
        followup_question=None,
    )


def _question_context(question: Question | None) -> str:
    if question is None:
        return "（無題目脈絡）"
    stem = (question.content or {}).get("stem", "")
    return (
        f"題型：{question.type}\n"
        f"涉及概念：{question.concept_tags}\n"
        f"Bloom 等級：{question.bloom_level}\n"
        f"題幹：{stem}"
    )


def _build_prompt(reflection: Reflection, question: Question | None) -> str:
    return f"""\
你是 C++ 學習教練，負責檢查學生「動手寫程式前」的反思品質，幫助他更清楚思考。
學生的反思包含三項：對問題的理解、解題步驟計畫、預期會用到的概念。

題目脈絡：
{_question_context(question)}

學生反思：
- 對問題的理解 (problem_understanding)：{reflection.problem_understanding!r}
- 解題步驟 (planned_steps)：{json.dumps(reflection.planned_steps or [], ensure_ascii=False)}
- 預期概念 (expected_concepts)：{reflection.expected_concepts!r}
- 學生對前一輪追問的補充 (followup_answer)：{reflection.followup_answer!r}

請從三面向評分（每項 0.0–1.0；越接近 1 越好），並在 quality_score 平均 < {QUALITY_THRESHOLD} 時，
針對 **得分最低的面向** 出 1 個蘇格拉底式追問（不可給答案，不可給程式碼，只能引導學生再想一次）：

A. understanding_score：學生重述的問題是否抓到核心？空話 / 抄題目原文 → 偏低；具體點出輸入/輸出/限制 → 偏高
B. plan_quality_score：planned_steps 是否具體可執行？「先寫程式再 debug」→ 0.2；
   「1. 讀入 N 2. 用 vector 存 3. 排序 4. 輸出第 K 大」→ 0.9
C. concept_recall_score：expected_concepts 是否與題目概念吻合？亂寫 / 太空 → 偏低；對應到題目 concept_tags → 偏高

回傳嚴格 JSON：
{{
  "understanding_score": 0.0–1.0,
  "understanding_reason": "...",
  "plan_quality_score": 0.0–1.0,
  "plan_quality_reason": "...",
  "concept_recall_score": 0.0–1.0,
  "concept_recall_reason": "...",
  "followup_question": "（若三項平均 >= {QUALITY_THRESHOLD} 則填 null；否則 1 句中文追問）"
}}
"""


async def evaluate_reflection(
    reflection: Reflection,
    question: Question | None = None,
) -> ReflectionEvaluation:
    """LLM 評分反思品質。

    Args:
        reflection: 已建立的 Reflection 物件（不需 commit）
        question: 對應的 Question（quiz 來源時傳入；learning_unit 來源傳 None）

    Returns:
        `ReflectionEvaluation` — 失敗（無 API key / LLM 異常 / parse error）時回 fallback，
        caller 應視為「未評分」並繼續流程。
    """
    if reflection.source_type == ReflectionSourceType.QUIZ.value and question is None:
        # quiz 反思預期 caller 提供 question；缺則仍嘗試評分但無題目脈絡
        pass

    client = _get_client()
    if client is None:
        return _empty_evaluation()

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _build_prompt(reflection, question)},
                {"role": "user", "content": "請評分並回傳 JSON。"},
            ],
            temperature=0.3,
            max_tokens=400,
        )
    except Exception:
        return _empty_evaluation()

    raw = response.choices[0].message.content or "{}"
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        return _empty_evaluation()

    try:
        parsed = _EvaluatorResponse(**data)
    except ValidationError:
        return _empty_evaluation()

    quality_score = round(
        (
            parsed.understanding_score
            + parsed.plan_quality_score
            + parsed.concept_recall_score
        )
        / 3,
        3,
    )
    # 高於門檻仍給了 followup 就丟掉（避免 LLM 多嘴干擾學生）
    followup = parsed.followup_question
    if quality_score >= QUALITY_THRESHOLD:
        followup = None
    elif followup is not None and not followup.strip():
        followup = None

    return ReflectionEvaluation(
        quality_score=quality_score,
        understanding_score=parsed.understanding_score,
        plan_quality_score=parsed.plan_quality_score,
        concept_recall_score=parsed.concept_recall_score,
        followup_question=followup,
    )
