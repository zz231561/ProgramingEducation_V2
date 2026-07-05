"""Quiz API — 智慧出題 + 作答 + 歷史（roadmap 2-4e）。"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from core.errors import AppError
from core.rate_limit import rate_limit
from models.quiz import Question, QuestionType, StudentAnswer
from models.user import User
from services.quiz import (
    generate_for_student,
    generate_hint,
    list_history,
    pick_random_validated_question,
    pick_target_concept,
    submit_answer,
)
from sqlalchemy import select as sa_select  # noqa: F401  used by hint endpoint

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

    answer_id: uuid.UUID  # 3-2c：供前端 fetch /quiz/answers/{id}/feedback
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


@router.get("/from-bank", response_model=QuestionForStudentOut)
async def from_bank(
    concept_tag: str | None = Query(default=None, min_length=1, max_length=50),
    question_type: str | None = Query(default=None, max_length=20),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> QuestionForStudentOut:
    """Phase 6-3b：從題庫隨機抽 validated grounded 題目（不呼叫 LLM）。

    - `concept_tag` 指定 → 抽該概念題（Learn 練習 tab）
    - `concept_tag` 省略 → **U2d 弱項模式**：沿用出題 Select 邏輯挑最弱概念再抽題庫
      （Quiz 頁題庫優先，省 LLM 成本與延遲）
    - 一律排除該學生已答過的題（重複曝光防護）；全部答過 → 404 → 前端
      fallback 至 /quiz/generate 現生新題（新題 validated 後入庫，題庫自然成長）

    命中 → 直接回題目；無題 → 404 QUESTION_BANK_EMPTY，前端 fallback 至 /quiz/generate。
    """
    tag = concept_tag
    if tag is None:
        concept = await pick_target_concept(db, user.id)
        tag = concept.tag
    question = await pick_random_validated_question(
        db,
        concept_tag=tag,
        question_type=question_type,
        exclude_answered_by=user.id,
    )
    if question is None:
        raise AppError(
            404,
            "QUESTION_BANK_EMPTY",
            f"題庫尚無針對 {tag} 的可用題目（未答過且 validated）",
        )
    return QuestionForStudentOut.from_question(question)


@router.post(
    "/generate",
    response_model=QuestionForStudentOut,
    dependencies=[Depends(rate_limit("llm"))],
)
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
        answer_id=student_answer.id,
        is_correct=student_answer.is_correct,
        feedback=student_answer.feedback,
        correct_content=question.content or {},
        explanation=question.explanation,
    )


# === Hint endpoint (3-2b) ===


class HintRequest(BaseModel):
    question_id: uuid.UUID
    hint_level: int = Field(..., ge=1, le=5)
    student_attempt: str = Field(default="", max_length=4000)


class HintResponse(BaseModel):
    level: int
    hint: str
    fallback: bool  # True = LLM 失敗用了固定句子


@router.post(
    "/hint",
    response_model=HintResponse,
    dependencies=[Depends(rate_limit("llm"))],
)
async def hint(
    body: HintRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> HintResponse:
    """為當前題目生成對應 hint_level 的提示（1-5）。

    純即時生成，不寫入 DB；學生實際使用的最高 level 由 /quiz/submit 的
    hint_level_used 欄位帶回持久化。
    """
    question = (
        await db.execute(sa_select(Question).where(Question.id == body.question_id))
    ).scalar_one_or_none()
    if question is None:
        raise AppError(404, "QUESTION_NOT_FOUND", f"找不到題目：{body.question_id}")
    if not question.validated:
        raise AppError(400, "QUESTION_NOT_VALIDATED", "此題尚未通過審查，無法取得提示")

    result = await generate_hint(
        question, hint_level=body.hint_level, student_attempt=body.student_attempt
    )
    return HintResponse(level=result.level, hint=result.hint, fallback=result.fallback)


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
