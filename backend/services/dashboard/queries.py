"""Dashboard 統計查詢 + 今日建議（roadmap 3-3a）。

設計：
- 4 統計卡片：學習路徑進度 / 本週 Quiz / 精熟度概覽 / 反思次數
- 今日建議：規則版（不用 LLM）— 依當前 path 狀態給下一動作
  * 有 in_progress unit → 「繼續學習：xxx」
  * 有 available unit → 「開始下一單元：xxx」
  * 全部 completed → 「課程完成，挑戰 Quiz」
  * 無 path → fallback「進入 Learn 開始」（但 ensure_default_path 後不會發生）
- LLM 個人化建議留給 Phase 4+ 或 3-3b/c
- path 取最早建立的（與 ensure_default_path_exists 行為一致）
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.concept import Concept
from models.learning import LearningPath, LearningUnit, LearningUnitStatus
from models.mastery import StudentMastery
from models.quiz import StudentAnswer
from models.reflection import Reflection

MASTERED_THRESHOLD = 0.8
WEEK_DAYS = 7


@dataclass(frozen=True)
class PathProgressSummary:
    path_id: UUID
    title: str
    total_units: int
    completed_units: int
    percent: int  # 0-100


@dataclass(frozen=True)
class WeekQuizStats:
    total_attempts: int
    correct_count: int
    accuracy_percent: int  # 0-100；無作答時為 0


@dataclass(frozen=True)
class MasteryOverview:
    total_concepts: int
    started_count: int       # student_mastery 表中 user 的 row 數
    mastered_count: int      # confidence >= MASTERED_THRESHOLD


@dataclass(frozen=True)
class TodaySuggestion:
    title: str               # 短行動標題
    description: str         # 補充說明
    link: str                # 前端路由（/learn / /quiz）
    next_concept_name: str | None


@dataclass(frozen=True)
class DashboardStats:
    path_progress: PathProgressSummary | None
    week_quiz: WeekQuizStats
    mastery: MasteryOverview
    reflection_count: int
    today_suggestion: TodaySuggestion


async def _earliest_path(db: AsyncSession, user_id: UUID) -> LearningPath | None:
    return (
        await db.execute(
            select(LearningPath)
            .where(LearningPath.user_id == user_id)
            .order_by(LearningPath.created_at)
            .limit(1)
        )
    ).scalar_one_or_none()


async def _path_progress(
    db: AsyncSession, path: LearningPath
) -> PathProgressSummary:
    units = list(
        (
            await db.execute(
                select(LearningUnit).where(LearningUnit.path_id == path.id)
            )
        ).scalars().all()
    )
    total = len(units)
    completed = sum(
        1 for u in units if u.status == LearningUnitStatus.COMPLETED.value
    )
    percent = int((completed / total) * 100) if total else 0
    return PathProgressSummary(
        path_id=path.id,
        title=path.title,
        total_units=total,
        completed_units=completed,
        percent=percent,
    )


async def _week_quiz_stats(db: AsyncSession, user_id: UUID) -> WeekQuizStats:
    week_ago = datetime.now(timezone.utc) - timedelta(days=WEEK_DAYS)
    rows = (
        await db.execute(
            select(StudentAnswer.is_correct)
            .where(StudentAnswer.user_id == user_id)
            .where(StudentAnswer.answered_at >= week_ago)
        )
    ).scalars().all()
    total = len(rows)
    correct = sum(1 for c in rows if c)
    accuracy = int((correct / total) * 100) if total else 0
    return WeekQuizStats(
        total_attempts=total,
        correct_count=correct,
        accuracy_percent=accuracy,
    )


async def _mastery_overview(
    db: AsyncSession, user_id: UUID
) -> MasteryOverview:
    total_concepts = (
        await db.execute(select(func.count()).select_from(Concept))
    ).scalar_one()
    started = (
        await db.execute(
            select(func.count())
            .select_from(StudentMastery)
            .where(StudentMastery.user_id == user_id)
        )
    ).scalar_one()
    mastered = (
        await db.execute(
            select(func.count())
            .select_from(StudentMastery)
            .where(StudentMastery.user_id == user_id)
            .where(StudentMastery.confidence >= MASTERED_THRESHOLD)
        )
    ).scalar_one()
    return MasteryOverview(
        total_concepts=int(total_concepts or 0),
        started_count=int(started or 0),
        mastered_count=int(mastered or 0),
    )


async def _reflection_count(db: AsyncSession, user_id: UUID) -> int:
    n = (
        await db.execute(
            select(func.count())
            .select_from(Reflection)
            .where(Reflection.user_id == user_id)
        )
    ).scalar_one()
    return int(n or 0)


async def _today_suggestion(
    db: AsyncSession, path: LearningPath | None
) -> TodaySuggestion:
    if path is None:
        return TodaySuggestion(
            title="進入 Learn 開始學習",
            description="尚未建立學習路徑；點選下方連結建立預設課程。",
            link="/learn",
            next_concept_name=None,
        )

    # 找 in_progress；無 → 找 available；都無 → 完成
    next_unit = (
        await db.execute(
            select(LearningUnit, Concept)
            .join(Concept, Concept.id == LearningUnit.concept_id)
            .where(LearningUnit.path_id == path.id)
            .where(
                LearningUnit.status.in_(
                    [
                        LearningUnitStatus.IN_PROGRESS.value,
                        LearningUnitStatus.AVAILABLE.value,
                    ]
                )
            )
            .order_by(LearningUnit.status.desc(), LearningUnit.order_index)
            # status DESC：'in_progress' > 'available' 字典序剛好優先 in_progress
            .limit(1)
        )
    ).first()

    if next_unit is None:
        return TodaySuggestion(
            title="課程完成，可以挑戰 Quiz",
            description="所有單元已完成；到 Quiz 頁面測驗本課程概念。",
            link="/quiz",
            next_concept_name=None,
        )

    unit, concept = next_unit
    if unit.status == LearningUnitStatus.IN_PROGRESS.value:
        return TodaySuggestion(
            title=f"繼續學習：{concept.name_zh}",
            description="你上次有開始這個單元但未完成，繼續吧。",
            link="/learn",
            next_concept_name=concept.name_zh,
        )
    return TodaySuggestion(
        title=f"開始下一單元：{concept.name_zh}",
        description="依教學順序，這是你接下來該學的概念。",
        link="/learn",
        next_concept_name=concept.name_zh,
    )


async def get_dashboard_stats(
    db: AsyncSession, user_id: UUID
) -> DashboardStats:
    """組裝 dashboard 全部資料（4 卡片 + 1 建議）。"""
    path = await _earliest_path(db, user_id)
    path_progress = await _path_progress(db, path) if path is not None else None
    return DashboardStats(
        path_progress=path_progress,
        week_quiz=await _week_quiz_stats(db, user_id),
        mastery=await _mastery_overview(db, user_id),
        reflection_count=await _reflection_count(db, user_id),
        today_suggestion=await _today_suggestion(db, path),
    )
