"""Quiz API — 智慧出題 + 作答 + 歷史（roadmap 2-4e）。"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from models.quiz import Question, QuestionType, StudentAnswer
from models.user import User
from services.quiz import generate_for_student, list_history, submit_answer

router = APIRouter(prefix="/quiz", tags=["quiz"])


# === Schemas ===


def _mask_content_for_student(question_type: str, content: dict[str, Any]) -> dict:
    """移除答案欄位，供前端題目顯示用（避免提前洩漏）。"""
    if question_type == QuestionType.MULTIPLE_CHOICE.value:
        return {
            "stem": content.get("stem", ""),
            "options": content.get("options", []),
        }
    if question_type == QuestionType.FILL_BLANK.value:
        return {"stem": content.get("stem", "")}
    if question_type == QuestionType.CODING.value:
        return {
            "stem": content.get("stem", ""),
            "starter_code": content.get("starter_code", ""),
        }
    return {}


class GenerateRequest(BaseModel):
    type: str = Field(default=QuestionType.MULTIPLE_CHOICE.value)
    bloom_level: int = Field(default=3, ge=1, le=6)
    # 3-1e：Learn 練習 tab 指定本單元 concept；None → 走弱項補強邏輯
    concept_tag: str | None = Field(default=None, max_length=50)


class QuestionForStudentOut(BaseModel):
    """題目展示（已 mask 答案）。"""

    id: uuid.UUID
    type: str
    concept_tags: list[str]
    bloom_level: int
    difficulty: int
    content: dict

    @classmethod
    def from_question(cls, q: Question) -> "QuestionForStudentOut":
        return cls(
            id=q.id,
            type=q.type,
            concept_tags=list(q.concept_tags),
            bloom_level=q.bloom_level,
            difficulty=q.difficulty,
            content=_mask_content_for_student(q.type, q.content or {}),
        )


class SubmitRequest(BaseModel):
    question_id: uuid.UUID
    answer: dict
    time_spent_seconds: int | None = Field(default=None, ge=0)
    hint_level_used: int = Field(default=0, ge=0, le=5)


class SubmitResponse(BaseModel):
    """作答結果 + 完整解答 + LLM 解釋。"""

    is_correct: bool
    feedback: str
    correct_content: dict  # 含答案欄位（提交後才回傳）
    explanation: str


class AnswerHistoryItem(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    is_correct: bool
    answered_at: str
    hint_level_used: int
    time_spent_seconds: int | None
    concept_tags: list[str]


class HistoryResponse(BaseModel):
    items: list[AnswerHistoryItem]
    total: int
    page: int
    limit: int


# === Endpoints ===


@router.post("/generate", response_model=QuestionForStudentOut)
async def generate(
    body: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> QuestionForStudentOut:
    """產生一題給當前學生。Server 自動選弱項 + 生成 + LLM 自審（retry）。

    可選指定 concept_tag（3-1e）→ 直接對該 concept 出題，跳過弱項邏輯。
    """
    question = await generate_for_student(
        db,
        user_id=user.id,
        question_type=QuestionType(body.type),
        bloom_level=body.bloom_level,
        concept_tag=body.concept_tag,
    )
    return QuestionForStudentOut.from_question(question)


@router.post("/submit", response_model=SubmitResponse)
async def submit(
    body: SubmitRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> SubmitResponse:
    """提交作答；server 判分、寫入 student_answers、更新精熟度。"""
    student_answer, question = await submit_answer(
        db,
        user_id=user.id,
        question_id=body.question_id,
        answer=body.answer,
        time_spent_seconds=body.time_spent_seconds,
        hint_level_used=body.hint_level_used,
    )
    return SubmitResponse(
        is_correct=student_answer.is_correct,
        feedback=student_answer.feedback,
        correct_content=question.content or {},
        explanation=question.explanation,
    )


@router.get("/history", response_model=HistoryResponse)
async def history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> HistoryResponse:
    """取當前學生的作答歷史。"""
    rows, total = await list_history(db, user.id, page=page, limit=limit)
    items = [
        AnswerHistoryItem(
            id=r.id,
            question_id=r.question_id,
            is_correct=r.is_correct,
            answered_at=r.answered_at.isoformat(),
            hint_level_used=r.hint_level_used,
            time_spent_seconds=r.time_spent_seconds,
            concept_tags=[],  # 透過 join 補；當前 list_history 未 join，留空簡化
        )
        for r in rows
    ]
    return HistoryResponse(items=items, total=total, page=page, limit=limit)
