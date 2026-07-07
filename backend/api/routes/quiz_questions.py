"""單題查詢 API（roadmap K3e）。

診斷嫌疑鏈的微測驗入口以 question_id 直取題目（K3c 已附題庫 validated 題）。
獨立檔避免 quiz.py 超過 250 行硬性限制；prefix 沿用 /quiz。
純 DB 讀取（無 LLM 呼叫）→ 不掛 rate limit。
"""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db, require_roles
from api.routes.quiz import QuestionForStudentOut
from core.errors import AppError
from models.quiz import Question
from models.user import User, UserRole
from services.dev_quiz_tools import list_questions_by_tag

router = APIRouter(prefix="/quiz", tags=["quiz"])


class TeacherQuestionOut(BaseModel):
    """教師題庫檢視——含完整 content（正解）與解析。"""

    id: uuid.UUID
    type: str
    bloom_level: int
    difficulty: int
    content: dict
    explanation: str


class TeacherQuestionsOut(BaseModel):
    questions: list[TeacherQuestionOut]


@router.get("/bank", response_model=TeacherQuestionsOut)
async def teacher_question_bank(
    tag: str = Query(min_length=1),
    db: AsyncSession = Depends(get_db),
    _teacher: User = Depends(require_roles(UserRole.TEACHER)),
) -> TeacherQuestionsOut:
    """教師檢視某 concept 的題庫（含正解 + 解析，僅 validated；5-6c）。"""
    questions = await list_questions_by_tag(db, tag)
    return TeacherQuestionsOut(
        questions=[
            TeacherQuestionOut(
                id=q.id, type=q.type, bloom_level=q.bloom_level,
                difficulty=q.difficulty, content=q.content or {},
                explanation=q.explanation or "",
            )
            for q in questions
            if q.validated
        ]
    )


@router.get("/questions/{question_id}", response_model=QuestionForStudentOut)
async def get_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_db_user),
) -> QuestionForStudentOut:
    """以 id 取單一題目（已 mask 答案）。

    僅回傳 validated=True 的題目（未審查題不可作答，與 /quiz/submit 一致）；
    不存在或未審查 → 404 QUESTION_NOT_FOUND。
    """
    result = await db.execute(
        select(Question).where(
            Question.id == question_id, Question.validated.is_(True)
        )
    )
    question = result.scalar_one_or_none()
    if question is None:
        raise AppError(404, "QUESTION_NOT_FOUND", "找不到題目（可能已被移除）")
    return QuestionForStudentOut.from_question(question)
