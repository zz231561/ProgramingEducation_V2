"""出題 + 作答的 use-case orchestration（roadmap 2-4e backbone）。

把 Select / Generate / Validate / Grade / Mastery 串成兩條主流程：
- `generate_for_student` — 學生請求新題：選弱項 → 生成 → 自審 → retry
- `submit_answer` — 學生作答：判分 → 寫 StudentAnswer → 更新 mastery
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.concept import Concept
from models.quiz import Question, QuestionType, StudentAnswer
from services.edf.models import BloomLevel, ErrorType, EvidenceResult
from services.mastery import update_mastery
from services.quiz.generate import generate_question
from services.quiz.grade import grade_answer
from services.quiz.select import select_weak_concepts
from services.quiz.validate import ValidationReport, validate_question

logger = logging.getLogger(__name__)

# Cold-start fallback：學生無弱項紀錄時，挑入門概念
COLD_START_FALLBACK_TAG = "syntax-basic"

# Validate 失敗時最多重試幾次
MAX_VALIDATE_RETRIES = 2


async def _pick_target_concept(db: AsyncSession, user_id: UUID) -> Concept:
    """先取弱項；無弱項則 fallback 到入門 concept。

    Cold-start 兩段 fallback：
    1. `COLD_START_FALLBACK_TAG`（V1 schema 兼容；測試環境直接 seed 此 tag）
    2. 動態查 `difficulty_level` 最低 + `video_order` 最前的 concept
       （V2 cpp-XX 章節制 seed 不含此固定 tag 時的 robust 後援）
    """
    weak = await select_weak_concepts(db, user_id, top_k=1)
    if weak:
        return weak[0]

    fallback = (
        await db.execute(
            select(Concept).where(Concept.tag == COLD_START_FALLBACK_TAG)
        )
    ).scalar_one_or_none()
    if fallback is not None:
        return fallback

    fallback = (
        await db.execute(
            select(Concept)
            .order_by(Concept.difficulty_level.asc(), Concept.video_order.asc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if fallback is None:
        raise AppError(503, "QUIZ_UNAVAILABLE", "題庫尚未初始化（無入門概念）")
    return fallback


async def _resolve_concept_by_tag(db: AsyncSession, tag: str) -> Concept:
    """依 tag 取 concept；不存在 → 404。"""
    concept = (
        await db.execute(select(Concept).where(Concept.tag == tag))
    ).scalar_one_or_none()
    if concept is None:
        raise AppError(404, "CONCEPT_NOT_FOUND", f"找不到概念：{tag}")
    return concept


async def generate_for_student(
    db: AsyncSession,
    user_id: UUID,
    question_type: QuestionType,
    bloom_level: int = int(BloomLevel.APPLY),
    concept_tag: str | None = None,
) -> Question:
    """為學生產生一題。流程：select → generate → validate（retry）→ commit。

    Args:
        db: SQLAlchemy async session
        user_id: 學生 UUID
        question_type: 期望題型
        bloom_level: 目標 Bloom 等級（1-6，預設 APPLY=3）
        concept_tag: 指定 concept tag（3-1e Learn 練習 tab 用）；
                     若提供 → 直接針對該 concept 出題；
                     若 None → 走原弱項補強邏輯（_pick_target_concept）

    Returns:
        validated=True 的 Question 物件

    Raises:
        AppError 404 CONCEPT_NOT_FOUND — concept_tag 指定但不存在
        AppError 503 QUIZ_VALIDATION_RETRY_EXHAUSTED — 連續多次 validate 失敗
    """
    if concept_tag is not None:
        concept = await _resolve_concept_by_tag(db, concept_tag)
    else:
        concept = await _pick_target_concept(db, user_id)
    difficulty = max(1, min(5, concept.difficulty_level))

    last_report: ValidationReport | None = None
    for _attempt in range(MAX_VALIDATE_RETRIES + 1):
        question = await generate_question(
            db, concept, question_type, difficulty, bloom_level
        )
        report = await validate_question(db, question)
        if report.passed:
            await db.commit()
            await db.refresh(question)
            return question
        # 未通過：rollback 此次 add，下一輪重試
        await db.rollback()
        last_report = report

    raise AppError(
        503,
        "QUIZ_VALIDATION_RETRY_EXHAUSTED",
        "AI 生成題目連續審查未通過：" + "; ".join(last_report.issues if last_report else []),
    )


async def submit_answer(
    db: AsyncSession,
    user_id: UUID,
    question_id: UUID,
    answer: dict,
    time_spent_seconds: int | None = None,
    hint_level_used: int = 0,
) -> tuple[StudentAnswer, Question]:
    """學生提交答案：判分 → 寫 student_answers → 更新 mastery → commit。

    Returns:
        (StudentAnswer 寫入後的物件, 對應 Question 物件供 caller 取 explanation)

    Raises:
        AppError 404 QUESTION_NOT_FOUND
        AppError 400 QUESTION_NOT_VALIDATED — 嘗試作答未審查通過的題
    """
    question = (
        await db.execute(select(Question).where(Question.id == question_id))
    ).scalar_one_or_none()
    if question is None:
        raise AppError(404, "QUESTION_NOT_FOUND", f"找不到題目：{question_id}")
    if not question.validated:
        raise AppError(400, "QUESTION_NOT_VALIDATED", "此題尚未通過審查，不可作答")

    is_correct, feedback = grade_answer(question, answer)

    student_answer = StudentAnswer(
        user_id=user_id,
        question_id=question.id,
        answer=answer,
        is_correct=is_correct,
        time_spent_seconds=time_spent_seconds,
        hint_level_used=hint_level_used,
        feedback=feedback,
    )
    db.add(student_answer)

    # 更新精熟度（與作答結果直接相關，不像 chat 是輔助訊號）
    evidence = EvidenceResult(
        error_type=ErrorType.NONE if is_correct else ErrorType.LOGIC,
        error_message="",
        concept_tags=list(question.concept_tags),
        bloom_level=BloomLevel(question.bloom_level),
        bloom_reasoning="from quiz answer",
        code_analysis="",
    )
    try:
        await update_mastery(db, user_id, evidence)
    except Exception as e:
        # mastery 失敗不阻擋作答記錄寫入（同 chat 容錯）
        logger.warning("update_mastery failed (non-blocking): %r", e)

    await db.commit()
    await db.refresh(student_answer)
    return student_answer, question


async def list_history(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[StudentAnswer], int]:
    """學生作答歷史（分頁，依 answered_at 降冪）。"""
    total = (
        await db.execute(
            select(func.count())
            .select_from(StudentAnswer)
            .where(StudentAnswer.user_id == user_id)
        )
    ).scalar_one()

    rows = (
        await db.execute(
            select(StudentAnswer)
            .where(StudentAnswer.user_id == user_id)
            .order_by(desc(StudentAnswer.answered_at))
            .offset((page - 1) * limit)
            .limit(limit)
        )
    ).scalars().all()
    return list(rows), total
