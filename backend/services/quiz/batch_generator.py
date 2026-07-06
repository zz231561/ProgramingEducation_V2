"""6-3c：知識點驅動批次生成 → questions 表（validated=True 才入庫，source='batch'）。

流程：per concept → 知識點萃取（題量 = 知識點數）→ 每知識點 1 題觀念選擇題
→ 非課程介紹單元補滿 1 題 coding → 每題 generate（grounded mode）+ validate
→ validated=True commit；validated=False rollback 該題、不阻擋同 concept 其他題。

設計取捨：
- 題量依影片知識量（2026-07-06 晚間使用者定案）：LLM 萃取 3-8 個重要知識點，
  每點 1 題 MC（content.knowledge_point 記錄對應點）；coding 每單元固定 1 題。
- source='batch' 區隔 LEARN 單元題組與 QUIZ 弱項現生題（source='generated'）。
- coding 沿用既有 validated coding（任何 source）——已有就不重生，省批次成本。
- 每題獨立 validate；失敗回滾該題不阻擋其他題。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.errors import AppError
from models.concept import Concept
from models.quiz import Question, QuestionSource, QuestionType
from services.edf.models import BloomLevel
from services.quiz.generate import generate_question
from services.quiz.knowledge_points import extract_knowledge_points
from services.quiz.validate import validate_question
from services.rag.retrieve import get_chunks_by_video_order

DEFAULT_BLOOM_LEVEL = int(BloomLevel.APPLY)
MAX_VALIDATE_RETRIES = 2
INTRO_CATEGORY = "課程介紹"  # v01-03：無程式碼可寫，不生 coding 題


@dataclass
class QuestionAttempt:
    """單一題目嘗試結果。"""

    question_type: str
    validated: bool
    attempt_count: int
    error: str | None = None
    issues: list[str] = field(default_factory=list)


@dataclass
class ConceptBatchResult:
    """單一 concept 批次結果（含每題詳情供 CLI / 測試斷言）。"""

    concept_id: UUID
    concept_tag: str
    video_order: int
    requested: int
    attempts: list[QuestionAttempt] = field(default_factory=list)
    error: str | None = None  # 若整 concept 直接 fail（如 NO_VIDEO_ORDER / SKIPPED）

    @property
    def validated_count(self) -> int:
        return sum(1 for a in self.attempts if a.validated)


async def _generate_one_validated(
    db: AsyncSession,
    concept: Concept,
    question_type: QuestionType,
    difficulty: int,
    bloom_level: int,
    knowledge_point: str | None = None,
    model: str | None = None,
) -> QuestionAttempt:
    """單題完整流程：generate + validate（retry max 2 次）。

    validated=True → Question 已 commit；validated=False → 已 rollback，不污染 DB。
    rollback / commit 後 ORM attr 會 expire，下次 access 觸發 async lazy reload；
    每次 IO 後都 `db.refresh(concept)` 確保 attrs 仍可同步存取。
    `model` 覆蓋生成模型（coding 用強模型提高通過率）。
    """
    last_issues: list[str] = []
    for attempt in range(1, MAX_VALIDATE_RETRIES + 1):
        try:
            question = await generate_question(
                db,
                concept,
                question_type,
                difficulty,
                bloom_level,
                video_order=concept.video_order,
                knowledge_point=knowledge_point,
                source=QuestionSource.BATCH,
                model=model,
            )
        except AppError as e:
            await db.rollback()
            await db.refresh(concept)
            return QuestionAttempt(
                question_type=question_type.value,
                validated=False,
                attempt_count=attempt,
                error=f"{e.error}: {e.message}",
            )

        try:
            report = await validate_question(db, question)
        except AppError as e:
            await db.rollback()
            await db.refresh(concept)
            return QuestionAttempt(
                question_type=question_type.value,
                validated=False,
                attempt_count=attempt,
                error=f"{e.error}: {e.message}",
            )

        if report.passed:
            await db.commit()
            await db.refresh(concept)
            return QuestionAttempt(
                question_type=question_type.value,
                validated=True,
                attempt_count=attempt,
            )

        await db.rollback()
        await db.refresh(concept)
        last_issues = report.issues

    return QuestionAttempt(
        question_type=question_type.value,
        validated=False,
        attempt_count=MAX_VALIDATE_RETRIES,
        error="VALIDATION_RETRY_EXHAUSTED",
        issues=last_issues,
    )


async def generate_questions_for_concept(
    db: AsyncSession,
    concept: Concept,
    bloom_level: int = DEFAULT_BLOOM_LEVEL,
    skip_existing: bool = True,
) -> ConceptBatchResult:
    """為單一 concept 生成知識點題組：每知識點 1 題 MC + （非 intro）1 題 coding。

    skip_existing=True 時：已有 batch MC 題組 → 跳過 MC；已有 batch coding → 跳過
    coding。coding 用強模型（validate 組 gpt-5.4）生成以提高通過率。
    不向上拋例外（除 NO_VIDEO_ORDER 防呆）。
    """
    if concept.video_order is None:
        raise AppError(
            422,
            "NO_VIDEO_ORDER",
            f"concept {concept.tag} 缺 video_order，無法 grounded 出題",
        )

    difficulty = max(1, min(5, concept.difficulty_level))
    result = ConceptBatchResult(
        concept_id=concept.id,
        concept_tag=concept.tag,
        video_order=concept.video_order,
        requested=0,
    )

    # --- MC 題組（每知識點 1 題）---
    if not (skip_existing and await _has_batch_mc(db, concept.tag)):
        chunks = await get_chunks_by_video_order(concept.video_order)
        try:
            points = await extract_knowledge_points(concept, chunks)
        except AppError as e:
            result.error = f"KNOWLEDGE_POINTS_FAILED: {e.error}"
            return result
        await db.refresh(concept)

        result.requested += len(points)
        for point in points:
            attempt = await _generate_one_validated(
                db,
                concept,
                QuestionType.MULTIPLE_CHOICE,
                difficulty,
                bloom_level,
                knowledge_point=point,
            )
            result.attempts.append(attempt)

    # --- coding（每單元固定 1 題；課程介紹 0 題）---
    # coding 用強模型（gpt-5.4）生成：cascade 弱生成通過率極低，改強生成 + 強審查
    if concept.category != INTRO_CATEGORY and not (
        skip_existing and await _has_batch_coding(db, concept.tag)
    ):
        result.requested += 1
        attempt = await _generate_one_validated(
            db,
            concept,
            QuestionType.CODING,
            difficulty,
            bloom_level,
            model=settings.llm_model_validate,
        )
        result.attempts.append(attempt)

    return result


async def list_target_concepts(
    db: AsyncSession, only: int | None = None
) -> list[Concept]:
    """凡有 video_order 皆為目標；含 1-3 課程介紹（與 6-2b 同策略）。"""
    stmt = (
        select(Concept)
        .where(Concept.video_order.is_not(None))
        .order_by(Concept.video_order)
    )
    if only is not None:
        stmt = stmt.where(Concept.video_order == only)
    return list((await db.execute(stmt)).scalars().all())


async def _validated_questions_for(db: AsyncSession, concept_tag: str) -> list[Question]:
    """撈出 concept_tags 含目標 tag 的 validated 題（JSON-contains 可攜寫法：
    先撈 validated rows 再 Python filter，n 不大可接受）。"""
    rows = (
        await db.execute(select(Question).where(Question.validated.is_(True)))
    ).scalars().all()
    return [q for q in rows if concept_tag in (q.concept_tags or [])]


async def _has_batch_mc(db: AsyncSession, concept_tag: str) -> bool:
    """該概念是否已有 batch 來源的 MC 題組（skip_existing 判斷 MC 是否重生）。"""
    return any(
        q.type == QuestionType.MULTIPLE_CHOICE.value
        and q.source == QuestionSource.BATCH.value
        for q in await _validated_questions_for(db, concept_tag)
    )


async def _has_batch_coding(db: AsyncSession, concept_tag: str) -> bool:
    """該概念是否已有 batch coding 題——LEARN 只讀 batch，故以 batch 為準判斷重生。"""
    return any(
        q.type == QuestionType.CODING.value
        and q.source == QuestionSource.BATCH.value
        for q in await _validated_questions_for(db, concept_tag)
    )


async def generate_all(
    db: AsyncSession,
    only: int | None = None,
    skip_existing: bool = True,
    bloom_level: int = DEFAULT_BLOOM_LEVEL,
) -> list[ConceptBatchResult]:
    """批次入口。逐 concept 生成知識點題組；skip_existing 交由 per-concept 函式判斷。"""
    concepts = await list_target_concepts(db, only=only)

    results: list[ConceptBatchResult] = []
    for concept in concepts:
        # rollback 會讓 session 內「所有」物件 expire（不只當前處理的 concept），
        # 前一輪的失敗回滾會使本輪 concept 屬性存取觸發同步 lazy-load（MissingGreenlet）
        await db.refresh(concept)
        results.append(
            await generate_questions_for_concept(
                db, concept, bloom_level=bloom_level, skip_existing=skip_existing
            )
        )
    return results
