"""Variation Challenge — LLM 生變體題 + 評分學生新解（roadmap 2-6d）。

設計（理論基礎見 variation_prompts.py docstring）：
- generate：LLM 看 (原題 + 學生程式碼) → 產出 (新 stem, starter_code, test_cases, concept_focus)
- grade：LLM 看 (變體題 + 學生新 code) → 心智模擬執行 → binary passed + feedback

「禁用 AI 的作答環境」說明：
- 後端不主動 enforce — variation 流程不串接 chat / EDF / hint，純粹「LLM 出題 → 學生答 → LLM 評分」
- 前端責任：開始變體挑戰時應隱藏 chat panel / hint 觸發點（見 .claude/rules/frontend.md）
- 後續若需 server enforce（防學生繞過），再加 Redis flag + chat API 檢查（屬 2-6d 之外）

LLM 失敗策略：
- generate → 503 VARIATION_GENERATION_FAILED
- grade fallback → passed=False + feedback=None（保守，避免誤判通過）
"""

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, StrictBool, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.errors import AppError
from models.quiz import ComprehensionType, Question, QuestionType, StudentAnswer
from services.comprehension.crud import _get_owned_answer
from services.comprehension.variation_prompts import (
    build_generate_prompt,
    build_grade_prompt,
)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            return None
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


@dataclass(frozen=True)
class VariationGenerationResult:
    """LLM 產生的變體題；任一欄位 None 代表生成失敗。"""

    stem: str | None
    starter_code: str | None
    test_cases: list[dict] | None
    concept_focus: str | None


@dataclass(frozen=True)
class VariationGradeResult:
    """評分結果。passed=False + feedback=None 為 LLM 不可用 fallback。"""

    passed: bool
    feedback: str | None


class _GenerateResponse(BaseModel):
    stem: str = Field(min_length=1, max_length=2000)
    starter_code: str = Field(default="", max_length=4000)
    test_cases: list[dict] = Field(default_factory=list, max_length=10)
    concept_focus: str = Field(default="", max_length=300)


class _GradeResponse(BaseModel):
    # StrictBool：拒絕 "yes" / "true" / 1 等隱式轉型；LLM 必須明確回 bool 才接受，
    # 否則進入 fallback（避免文字噪音被誤解為通過）
    passed: StrictBool
    feedback: str = Field(default="", max_length=300)


_GEN_FAIL = VariationGenerationResult(stem=None, starter_code=None, test_cases=None, concept_focus=None)
_GRADE_FAIL = VariationGradeResult(passed=False, feedback=None)


async def _call_llm_json(
    system_prompt: str, max_tokens: int, temperature: float
) -> dict[str, Any] | None:
    """共用 LLM 呼叫 + JSON parse；任何失敗回 None。"""
    client = _get_client()
    if client is None:
        return None
    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "請回傳 JSON。"},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception:
        return None
    try:
        return json.loads(response.choices[0].message.content or "{}")
    except json.JSONDecodeError:
        return None


# === LLM functions ===


async def generate_variation(
    question: Question, student_code: str
) -> VariationGenerationResult:
    """LLM 生成變體題；失敗回 fallback（全 None）。"""
    data = await _call_llm_json(
        build_generate_prompt(question, student_code),
        max_tokens=800,
        temperature=0.5,
    )
    if data is None:
        return _GEN_FAIL
    try:
        parsed = _GenerateResponse(**data)
    except ValidationError:
        return _GEN_FAIL
    return VariationGenerationResult(
        stem=parsed.stem,
        starter_code=parsed.starter_code,
        test_cases=parsed.test_cases,
        concept_focus=parsed.concept_focus,
    )


async def grade_variation(
    variation_stem: str,
    test_cases: list[dict],
    concept_focus: str,
    student_code: str,
) -> VariationGradeResult:
    """LLM 評分學生變體解；LLM 失敗 → fallback。"""
    data = await _call_llm_json(
        build_grade_prompt(variation_stem, test_cases, concept_focus, student_code),
        max_tokens=300,
        temperature=0.1,
    )
    if data is None:
        return _GRADE_FAIL
    try:
        parsed = _GradeResponse(**data)
    except ValidationError:
        return _GRADE_FAIL
    return VariationGradeResult(passed=parsed.passed, feedback=parsed.feedback or None)


# === Workflow (DB integration) ===


async def start_variation_for_answer(
    db: AsyncSession, user_id: UUID, student_answer_id: UUID
) -> tuple[StudentAnswer, dict]:
    """LLM 生變體題並寫入。重新生成清空舊 answer/passed。

    Raises:
        AppError 404 STUDENT_ANSWER_NOT_FOUND
        AppError 422 VARIATION_NOT_APPLICABLE — 非 coding 題型
        AppError 503 VARIATION_GENERATION_FAILED
    """
    answer = await _get_owned_answer(db, student_answer_id, user_id)
    question = (
        await db.execute(select(Question).where(Question.id == answer.question_id))
    ).scalar_one_or_none()
    if question is None:
        raise AppError(404, "QUESTION_NOT_FOUND", f"找不到題目：{answer.question_id}")
    if question.type != QuestionType.CODING.value:
        raise AppError(
            422,
            "VARIATION_NOT_APPLICABLE",
            f"變體挑戰僅支援 coding 題型，當前題型：{question.type}",
        )

    student_code = (answer.answer or {}).get("code", "")
    result = await generate_variation(question, student_code)
    if result.stem is None:
        raise AppError(
            503,
            "VARIATION_GENERATION_FAILED",
            "AI 生成變體題暫時不可用，請稍後再試",
        )

    payload = {
        "stem": result.stem,
        "starter_code": result.starter_code,
        "test_cases": result.test_cases,
        "concept_focus": result.concept_focus,
    }
    answer.comprehension_type = ComprehensionType.VARIATION.value
    answer.comprehension_prompt = json.dumps(payload, ensure_ascii=False)
    answer.comprehension_answer = None
    answer.comprehension_passed = None

    await db.commit()
    await db.refresh(answer)
    return answer, payload


async def submit_variation_for_answer(
    db: AsyncSession, user_id: UUID, student_answer_id: UUID, student_code: str
) -> tuple[StudentAnswer, VariationGradeResult]:
    """評分學生變體解並寫入 student_answers。

    Raises:
        AppError 404 STUDENT_ANSWER_NOT_FOUND
        AppError 400 VARIATION_NOT_STARTED — 未先 generate
        AppError 500 VARIATION_PROMPT_CORRUPT — prompt JSON 損壞
    """
    answer = await _get_owned_answer(db, student_answer_id, user_id)
    if (
        answer.comprehension_type != ComprehensionType.VARIATION.value
        or not answer.comprehension_prompt
    ):
        raise AppError(400, "VARIATION_NOT_STARTED", "尚未生成變體題，請先呼叫 generate")

    try:
        prompt_data = json.loads(answer.comprehension_prompt)
        stem = prompt_data["stem"]
        test_cases = prompt_data.get("test_cases") or []
        concept_focus = prompt_data.get("concept_focus") or ""
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise AppError(
            500, "VARIATION_PROMPT_CORRUPT", "變體題資料損壞，請重新生成"
        ) from exc

    result = await grade_variation(stem, test_cases, concept_focus, student_code)

    answer.comprehension_answer = student_code
    answer.comprehension_passed = result.passed

    await db.commit()
    await db.refresh(answer)
    return answer, result
