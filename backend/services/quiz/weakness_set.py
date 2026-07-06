"""6-3d 弱項綜合測驗組——組裝（題庫優先 + 並行生成）。

流程：mastery 快照 → 藍圖 → 逐題計畫 → 題庫優先填（重用 ≤30%）→ 缺口並行生成。
並行生成每題各用獨立 session（避免共用交易衝突）；回傳依計畫順序的 Question 列表。
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import async_session
from core.errors import AppError
from models.quiz import Question, QuestionType
from services.edf.models import BloomLevel
from services.quiz.bank import pick_random_validated_question
from services.quiz.generate import generate_question
from services.quiz.validate import validate_question
from services.quiz.weakness_set_plan import (
    QuestionPlan,
    compute_blueprint,
    mastery_snapshot,
    plan_questions,
)

logger = logging.getLogger(__name__)

BLOOM_LEVEL = int(BloomLevel.APPLY)
MAX_VALIDATE_RETRIES = 2
REUSE_FRACTION = 0.3  # 題庫重用上限（其餘現生，保新鮮）
MAX_CONCURRENT_GEN = 6  # 並行生成上限（避免 OpenAI 帳戶層 rate limit）


def _is_bank_reusable(plan: QuestionPlan) -> bool:
    """僅單節點 MC 可從題庫重用（綜合題 / coding 為新組合，題庫無對應）。"""
    return plan.question_type == QuestionType.MULTIPLE_CHOICE and not plan.extra


async def _generate_one(plan: QuestionPlan) -> UUID | None:
    """獨立 session 生成 + 自審一題；validated 才 commit，回傳 question.id。

    coding 用強模型（gpt-5.4）提高通過率；MC 用預設生成組。失敗回 None。
    """
    difficulty = max(1, min(5, plan.target.difficulty_level))
    model = (
        settings.llm_model_validate
        if plan.question_type == QuestionType.CODING
        else None
    )
    async with async_session() as db:
        for _ in range(MAX_VALIDATE_RETRIES + 1):
            try:
                question = await generate_question(
                    db,
                    plan.target,
                    plan.question_type,
                    difficulty,
                    BLOOM_LEVEL,
                    extra_concepts=plan.extra,
                    model=model,
                )
                report = await validate_question(db, question)
            except AppError:
                await db.rollback()
                return None
            if report.passed:
                await db.commit()
                return question.id
            await db.rollback()
    return None


async def build_weakness_set(
    db: AsyncSession, user_id: UUID, count: int
) -> list[Question]:
    """組一組弱項測驗（count 題）。題庫優先重用 ≤30%，缺口並行現生。

    無弱項概念（cold-start / 已全數掌握）→ 回空 list，由 caller 決定 fallback。
    """
    snapshot = await mastery_snapshot(db, user_id)
    if not snapshot.weak:
        return []

    blueprint = compute_blueprint(count, snapshot.overall)
    plans = await plan_questions(db, snapshot, blueprint)

    max_reused = int(count * REUSE_FRACTION)
    ordered_ids: list[UUID | None] = []
    used_ids: set[UUID] = set()
    gen_slots: list[tuple[int, QuestionPlan]] = []
    reused = 0

    for plan in plans:
        if _is_bank_reusable(plan) and reused < max_reused:
            q = await pick_random_validated_question(
                db,
                plan.target.tag,
                exclude_question_ids=list(used_ids),
                question_type=QuestionType.MULTIPLE_CHOICE.value,
                exclude_answered_by=user_id,
            )
            if q is not None:
                ordered_ids.append(q.id)
                used_ids.add(q.id)
                reused += 1
                continue
        ordered_ids.append(None)
        gen_slots.append((len(ordered_ids) - 1, plan))

    # 缺口並行生成（各自獨立 session；semaphore 限制併發避免 OpenAI rate limit）
    sem = asyncio.Semaphore(MAX_CONCURRENT_GEN)

    async def _bounded(plan: QuestionPlan) -> UUID | None:
        async with sem:
            return await _generate_one(plan)

    gen_results = await asyncio.gather(
        *(_bounded(plan) for _, plan in gen_slots),
        return_exceptions=True,
    )
    for (idx, _plan), result in zip(gen_slots, gen_results):
        if isinstance(result, UUID):
            ordered_ids[idx] = result
        elif isinstance(result, Exception):
            logger.warning("weakness-set generation failed: %r", result)

    final_ids = [qid for qid in ordered_ids if qid is not None]
    return await _load_in_order(db, final_ids)


async def _load_in_order(db: AsyncSession, ids: list[UUID]) -> list[Question]:
    """依 ids 順序載入 Question（並行生成在別的 session commit，此處重讀主 session）。"""
    if not ids:
        return []
    rows = (
        await db.execute(select(Question).where(Question.id.in_(ids)))
    ).scalars().all()
    by_id = {q.id: q for q in rows}
    return [by_id[qid] for qid in ids if qid in by_id]
