"""EPL (Explain in Plain Language) — LLM 生成驗證題 + 評估學生回答（roadmap 2-6b）。

設計（理論基礎見 references.md：Self-explanation effect、Fowler et al. EPL）：
- 兩階段：先生成 EPL prompt（看題目+學生答案 → 出「請用自己的話解釋」題），
  再評分學生回答。
- 評分 3 面向：conceptual_correctness / specificity / causality；
  passed = (avg ≥ EPL_PASS_THRESHOLD)
- LLM 失敗（API down / parse error）→ fallback（passed=None / prompt=None），
  caller swallow 不擋學生流程；passed=None 持久化也存 None，避免錯判。

Prompt 模板獨立於 epl_prompts.py，本檔聚焦於 LLM client + dataclass + async 流程。
"""

import json
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

from core.config import settings
from models.quiz import Question, StudentAnswer
from services.comprehension.epl_prompts import (
    build_generate_prompt,
    build_grade_prompt,
)

EPL_PASS_THRESHOLD = 0.6  # 與 reflection QUALITY_THRESHOLD 一致

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    """無 API key 直接回 None；caller fallback，不丟 503（避免擋學生流程）。"""
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            return None
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


@dataclass(frozen=True)
class EplGenerationResult:
    """LLM 生成的 EPL 題目。`prompt=None` 代表生成失敗（fallback）。"""

    prompt: str | None


@dataclass(frozen=True)
class EplGradeResult:
    """LLM 對學生 EPL 回答的評分。`passed=None` 代表評分失敗（fallback）。"""

    passed: bool | None
    conceptual_correctness: float | None
    specificity: float | None
    causality: float | None
    feedback: str | None  # 1 句中文回饋，不持久化（即時回前端）


class _GradeResponse(BaseModel):
    conceptual_correctness: float = Field(ge=0.0, le=1.0)
    specificity: float = Field(ge=0.0, le=1.0)
    causality: float = Field(ge=0.0, le=1.0)
    feedback: str = Field(default="", max_length=300)


_GRADE_FALLBACK = EplGradeResult(
    passed=None,
    conceptual_correctness=None,
    specificity=None,
    causality=None,
    feedback=None,
)


async def generate_epl_prompt(
    question: Question, student_answer: StudentAnswer
) -> EplGenerationResult:
    """LLM 生成 EPL 提示題。失敗回 prompt=None；caller 應回 503 或 fallback。"""
    client = _get_client()
    if client is None:
        return EplGenerationResult(prompt=None)

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": build_generate_prompt(question, student_answer)},
                {"role": "user", "content": "請出題並回傳 JSON。"},
            ],
            temperature=0.4,
            max_tokens=120,
        )
    except Exception:
        return EplGenerationResult(prompt=None)

    raw = response.choices[0].message.content or "{}"
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        return EplGenerationResult(prompt=None)

    prompt = data.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        return EplGenerationResult(prompt=None)
    return EplGenerationResult(prompt=prompt.strip())


async def grade_epl_answer(
    question: Question,
    student_answer: StudentAnswer,
    epl_prompt: str,
    epl_answer: str,
) -> EplGradeResult:
    """LLM 評分學生 EPL 回答。失敗回 fallback（passed=None）。"""
    client = _get_client()
    if client is None:
        return _GRADE_FALLBACK

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": build_grade_prompt(question, student_answer, epl_prompt, epl_answer),
                },
                {"role": "user", "content": "請評分並回傳 JSON。"},
            ],
            temperature=0.2,
            max_tokens=300,
        )
    except Exception:
        return _GRADE_FALLBACK

    raw = response.choices[0].message.content or "{}"
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        return _GRADE_FALLBACK

    try:
        parsed = _GradeResponse(**data)
    except ValidationError:
        return _GRADE_FALLBACK

    avg = round(
        (parsed.conceptual_correctness + parsed.specificity + parsed.causality) / 3, 3
    )
    return EplGradeResult(
        passed=avg >= EPL_PASS_THRESHOLD,
        conceptual_correctness=parsed.conceptual_correctness,
        specificity=parsed.specificity,
        causality=parsed.causality,
        feedback=parsed.feedback or None,
    )
