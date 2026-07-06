"""Phase 6-3a-2：批次生成 grounded 練習題 → questions 表（validated=True 才入庫）。

流程：per concept → 跑 N 題（題型 mix）→ 每題 generate（grounded mode）+ validate
→ validated=True commit；validated=False rollback 該題、不阻擋同 concept 其他題。

設計取捨：
- 不走 orchestrator.generate_for_student：那條 path 為「學生弱項補強」，會 pick_target_concept；
  批次模式直接針對指定 concept，且強制走 grounded mode（傳 video_order）。
- 題型 mix 預設 multiple_choice + coding（涵蓋認知 + 實作）；caller 可自訂。
- 每題獨立 validate；validate 失敗 → 該題回滾、結果記 ValidationFail，下一題繼續。
- 與 6-2b unit content 區隔：unit content 一 concept 一 staging row；questions 一 concept 多筆。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.concept import Concept
from models.quiz import Question, QuestionType
from services.edf.models import BloomLevel
from services.quiz.generate import generate_question
from services.quiz.validate import validate_question

DEFAULT_QUESTION_TYPES: tuple[QuestionType, ...] = (
    QuestionType.MULTIPLE_CHOICE,
    QuestionType.CODING,
)
DEFAULT_BLOOM_LEVEL = int(BloomLevel.APPLY)
MAX_VALIDATE_RETRIES = 2


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
) -> QuestionAttempt:
    """單題完整流程：generate + validate（retry max 2 次）。

    validated=True → Question 已 commit；validated=False → 已 rollback，不污染 DB。
    rollback / commit 後 ORM attr 會 expire，下次 access 觸發 async lazy reload；
    每次 IO 後都 `db.refresh(concept)` 確保 attrs 仍可同步存取。
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
    question_types: tuple[QuestionType, ...] = DEFAULT_QUESTION_TYPES,
    bloom_level: int = DEFAULT_BLOOM_LEVEL,
) -> ConceptBatchResult:
    """為單一 concept 跑 `len(question_types)` 題，全部 grounded mode。

    不向上拋例外（除 NO_VIDEO_ORDER 防呆）；單題 generate / validate 失敗皆收進 result.attempts。
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
        requested=len(question_types),
    )
    for qtype in question_types:
        attempt = await _generate_one_validated(
            db, concept, qtype, difficulty, bloom_level
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


async def _count_validated_questions(db: AsyncSession, concept_tag: str) -> int:
    """以 concept_tag 在 concept_tags JSON 陣列中的存在計數 validated=True 題目。

    用 func.count + JSON-contains 的可攜版本：對任何方言皆有效的 fallback —
    先撈出 validated rows 再 filter，n 不大（≤ 數百）可接受。
    """
    rows = (
        await db.execute(
            select(Question.concept_tags).where(Question.validated.is_(True))
        )
    ).scalars().all()
    return sum(1 for tags in rows if concept_tag in (tags or []))


async def generate_all(
    db: AsyncSession,
    only: int | None = None,
    skip_existing: bool = True,
    question_types: tuple[QuestionType, ...] = DEFAULT_QUESTION_TYPES,
    bloom_level: int = DEFAULT_BLOOM_LEVEL,
) -> list[ConceptBatchResult]:
    """批次入口。`skip_existing=True` 時跳過已有 ≥ `len(question_types)` validated 題的 concept。"""
    concepts = await list_target_concepts(db, only=only)
    target_per_concept = len(question_types)

    results: list[ConceptBatchResult] = []
    for concept in concepts:
        # rollback 會讓 session 內「所有」物件 expire（不只當前處理的 concept），
        # 前一輪的失敗回滾會使本輪 concept 屬性存取觸發同步 lazy-load（MissingGreenlet）
        await db.refresh(concept)
        if skip_existing:
            existing = await _count_validated_questions(db, concept.tag)
            if existing >= target_per_concept:
                results.append(
                    ConceptBatchResult(
                        concept_id=concept.id,
                        concept_tag=concept.tag,
                        video_order=concept.video_order or 0,
                        requested=target_per_concept,
                        error="SKIPPED_HAS_ENOUGH",
                    )
                )
                continue
        results.append(
            await generate_questions_for_concept(
                db, concept, question_types=question_types, bloom_level=bloom_level
            )
        )
    return results
