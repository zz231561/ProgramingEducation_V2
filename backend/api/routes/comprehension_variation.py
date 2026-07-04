"""Comprehension Variation Challenge API（roadmap 2-6d）。

獨立檔避免 comprehension.py 超過 250 行硬性限制。

API：
- POST /comprehension/{student_answer_id}/variation/generate — LLM 生變體題
- POST /comprehension/{student_answer_id}/variation/grade    — LLM 評分學生新解

「禁用 AI」屬前端責任：開始變體挑戰時前端應隱藏 chat panel / hint UI。
本 router 不串接 chat / EDF / hint，純 LLM 出題 + 評分閉環。
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from core.rate_limit import rate_limit
from models.user import User
from services.comprehension import (
    start_variation_for_answer,
    submit_variation_for_answer,
)

router = APIRouter(prefix="/comprehension", tags=["comprehension"])


class VariationTestCase(BaseModel):
    input: str
    expected: str


class VariationGenerateOut(BaseModel):
    """generate 把 stem / starter / test_cases 全露給學生（解題需要）；不藏 expected。"""

    student_answer_id: uuid.UUID
    comprehension_type: str
    stem: str
    starter_code: str
    test_cases: list[VariationTestCase]
    concept_focus: str


class GradeVariationRequest(BaseModel):
    student_code: str = Field(..., min_length=1, max_length=10000)


class VariationGradeOut(BaseModel):
    student_answer_id: uuid.UUID
    comprehension_passed: bool
    feedback: str | None


@router.post(
    "/{student_answer_id}/variation/generate",
    response_model=VariationGenerateOut,
    dependencies=[Depends(rate_limit("llm"))],
)
async def variation_generate(
    student_answer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> VariationGenerateOut:
    """LLM 生變體題並寫入。422 若非 coding；503 若 LLM 失敗。"""
    answer, payload = await start_variation_for_answer(db, user.id, student_answer_id)
    test_cases = [
        VariationTestCase(
            input=str(tc.get("input", "")),
            expected=str(tc.get("expected", "")),
        )
        for tc in (payload.get("test_cases") or [])
    ]
    return VariationGenerateOut(
        student_answer_id=answer.id,
        comprehension_type=answer.comprehension_type or "",
        stem=payload.get("stem") or "",
        starter_code=payload.get("starter_code") or "",
        test_cases=test_cases,
        concept_focus=payload.get("concept_focus") or "",
    )


@router.post(
    "/{student_answer_id}/variation/grade",
    response_model=VariationGradeOut,
    dependencies=[Depends(rate_limit("llm"))],
)
async def variation_grade(
    student_answer_id: uuid.UUID,
    body: GradeVariationRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> VariationGradeOut:
    """LLM 評分學生變體解。需先呼叫 generate。"""
    answer, result = await submit_variation_for_answer(
        db, user.id, student_answer_id, body.student_code
    )
    return VariationGradeOut(
        student_answer_id=answer.id,
        comprehension_passed=result.passed,
        feedback=result.feedback,
    )
