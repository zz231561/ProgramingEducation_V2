"""Comprehension API — Post-Solution Comprehension Check 端點（roadmap 2-6a + 2-6b）。

API 設計：
- GET  /comprehension/{student_answer_id}              — 讀取 comprehension 狀態
- PUT  /comprehension/{student_answer_id}              — partial upsert（手動寫入）
- POST /comprehension/{student_answer_id}/epl/generate — LLM 生成 EPL 題（2-6b）
- POST /comprehension/{student_answer_id}/epl/grade    — LLM 評分學生 EPL 回答（2-6b）

PUT 採 partial：未提供欄位保留原值。EPL endpoints 採重置/順序語意：generate 會清空舊
answer/passed，grade 必須在 generate 之後呼叫。
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from core.errors import AppError
from models.quiz import ComprehensionType, StudentAnswer
from models.user import User
from services.comprehension import (
    ComprehensionUpdate,
    get_comprehension,
    start_epl_for_answer,
    submit_epl_for_answer,
    upsert_comprehension,
)

router = APIRouter(prefix="/comprehension", tags=["comprehension"])


# === Schemas ===


class ComprehensionOut(BaseModel):
    """comprehension 欄位投影（不回傳 student_answer 其他欄位避免重複）。"""

    student_answer_id: uuid.UUID
    comprehension_type: str | None
    comprehension_prompt: str | None
    comprehension_answer: str | None
    comprehension_passed: bool | None

    @classmethod
    def from_model(cls, a: StudentAnswer) -> "ComprehensionOut":
        return cls(
            student_answer_id=a.id,
            comprehension_type=a.comprehension_type,
            comprehension_prompt=a.comprehension_prompt,
            comprehension_answer=a.comprehension_answer,
            comprehension_passed=a.comprehension_passed,
        )


class UpsertComprehensionRequest(BaseModel):
    """partial — 未提供欄位保留原值。type 由 service 驗證為合法 enum。"""

    comprehension_type: str | None = Field(default=None, description="epl | predict_output | variation")
    comprehension_prompt: str | None = Field(default=None, max_length=4000)
    comprehension_answer: str | None = Field(default=None, max_length=4000)
    comprehension_passed: bool | None = None


# === Endpoints ===


@router.get("/{student_answer_id}", response_model=ComprehensionOut)
async def get(
    student_answer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> ComprehensionOut:
    """讀取 comprehension 狀態。非本人擁有的作答回 404。"""
    answer = await get_comprehension(db, student_answer_id, user.id)
    return ComprehensionOut.from_model(answer)


@router.put("/{student_answer_id}", response_model=ComprehensionOut)
async def put(
    student_answer_id: uuid.UUID,
    body: UpsertComprehensionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> ComprehensionOut:
    """upsert comprehension 欄位。type 必須為合法 enum 否則回 422。"""
    parsed_type = _parse_type(body.comprehension_type) if body.comprehension_type is not None else None
    answer = await upsert_comprehension(
        db,
        student_answer_id=student_answer_id,
        user_id=user.id,
        payload=ComprehensionUpdate(
            comprehension_type=parsed_type,
            comprehension_prompt=body.comprehension_prompt,
            comprehension_answer=body.comprehension_answer,
            comprehension_passed=body.comprehension_passed,
        ),
    )
    return ComprehensionOut.from_model(answer)


def _parse_type(value: str) -> ComprehensionType:
    """422 if invalid。"""
    try:
        return ComprehensionType(value)
    except ValueError as exc:
        raise AppError(
            422,
            "INVALID_COMPREHENSION_TYPE",
            f"comprehension_type 必須為 epl / predict_output / variation，收到：{value}",
        ) from exc


# === EPL endpoints (roadmap 2-6b) ===


class EplGenerateOut(BaseModel):
    """EPL 生成結果 — 含 comprehension 狀態 + LLM 給的 prompt（同欄位重複是為前端方便）。"""

    student_answer_id: uuid.UUID
    comprehension_type: str
    comprehension_prompt: str  # generate 成功必非空


class GradeEplRequest(BaseModel):
    epl_answer: str = Field(..., min_length=1, max_length=4000)


class EplGradeOut(BaseModel):
    """EPL 評分結果 — 持久化欄位 + 即時細項分數 + 回饋（細項與 feedback 不入庫）。"""

    student_answer_id: uuid.UUID
    comprehension_passed: bool | None
    conceptual_correctness: float | None
    specificity: float | None
    causality: float | None
    feedback: str | None


@router.post("/{student_answer_id}/epl/generate", response_model=EplGenerateOut)
async def epl_generate(
    student_answer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> EplGenerateOut:
    """LLM 生成 EPL 題目並寫入。重新生成會清空舊 answer/passed。"""
    answer, _ = await start_epl_for_answer(db, user.id, student_answer_id)
    return EplGenerateOut(
        student_answer_id=answer.id,
        comprehension_type=answer.comprehension_type or "",
        comprehension_prompt=answer.comprehension_prompt or "",
    )


@router.post("/{student_answer_id}/epl/grade", response_model=EplGradeOut)
async def epl_grade(
    student_answer_id: uuid.UUID,
    body: GradeEplRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> EplGradeOut:
    """LLM 評分學生 EPL 回答。需先呼叫 generate。"""
    answer, result = await submit_epl_for_answer(
        db, user.id, student_answer_id, body.epl_answer
    )
    return EplGradeOut(
        student_answer_id=answer.id,
        comprehension_passed=answer.comprehension_passed,
        conceptual_correctness=result.conceptual_correctness,
        specificity=result.specificity,
        causality=result.causality,
        feedback=result.feedback,
    )
