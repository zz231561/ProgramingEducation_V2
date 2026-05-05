"""學生 Dashboard API（roadmap 3-3a/b/c）。

API：
- GET /dashboard/stats               — 4 統計卡片 + 今日建議
- GET /dashboard/timeline?limit=30   — 最近活動時間線
- GET /dashboard/mastery-overview    — 依 category 分組的精熟度詳細總覽
"""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from models.user import User
from services.dashboard import (
    get_dashboard_stats,
    get_mastery_breakdown,
    list_recent_activities,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class PathProgressOut(BaseModel):
    path_id: uuid.UUID
    title: str
    total_units: int
    completed_units: int
    percent: int


class WeekQuizOut(BaseModel):
    total_attempts: int
    correct_count: int
    accuracy_percent: int


class MasteryOut(BaseModel):
    total_concepts: int
    started_count: int
    mastered_count: int


class TodaySuggestionOut(BaseModel):
    title: str
    description: str
    link: str
    next_concept_name: str | None


class DashboardStatsResponse(BaseModel):
    path_progress: PathProgressOut | None
    week_quiz: WeekQuizOut
    mastery: MasteryOut
    reflection_count: int
    today_suggestion: TodaySuggestionOut


class ActivityItemOut(BaseModel):
    type: str  # quiz | reflection | unit_completed
    timestamp: str  # ISO
    title: str
    detail: str
    link: str | None
    is_correct: bool | None


class TimelineResponse(BaseModel):
    items: list[ActivityItemOut]


@router.get("/timeline", response_model=TimelineResponse)
async def timeline(
    limit: int = Query(default=30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> TimelineResponse:
    """最近活動（quiz / reflection / unit_completed）合併按時間排序。"""
    activities = await list_recent_activities(db, user.id, limit=limit)
    return TimelineResponse(
        items=[
            ActivityItemOut(
                type=a.type,
                timestamp=a.timestamp.isoformat(),
                title=a.title,
                detail=a.detail,
                link=a.link,
                is_correct=a.is_correct,
            )
            for a in activities
        ]
    )


class ConceptMasteryDetailOut(BaseModel):
    concept_tag: str
    concept_name_zh: str
    video_order: int | None
    difficulty: int
    confidence: float


class CategoryBreakdownOut(BaseModel):
    name: str
    total: int
    started: int
    mastered: int
    concepts: list[ConceptMasteryDetailOut]


class MasteryOverviewResponse(BaseModel):
    categories: list[CategoryBreakdownOut]


@router.get("/mastery-overview", response_model=MasteryOverviewResponse)
async def mastery_overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> MasteryOverviewResponse:
    """依 category 分組返回精熟度總覽。"""
    result = await get_mastery_breakdown(db, user.id)
    return MasteryOverviewResponse(
        categories=[
            CategoryBreakdownOut(
                name=cat.name,
                total=cat.total,
                started=cat.started,
                mastered=cat.mastered,
                concepts=[
                    ConceptMasteryDetailOut(
                        concept_tag=c.concept_tag,
                        concept_name_zh=c.concept_name_zh,
                        video_order=c.video_order,
                        difficulty=c.difficulty,
                        confidence=c.confidence,
                    )
                    for c in cat.concepts
                ],
            )
            for cat in result.categories
        ]
    )


@router.get("/stats", response_model=DashboardStatsResponse)
async def stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> DashboardStatsResponse:
    """取當前學生的 dashboard 概覽資料。"""
    s = await get_dashboard_stats(db, user.id)
    return DashboardStatsResponse(
        path_progress=(
            PathProgressOut(
                path_id=s.path_progress.path_id,
                title=s.path_progress.title,
                total_units=s.path_progress.total_units,
                completed_units=s.path_progress.completed_units,
                percent=s.path_progress.percent,
            )
            if s.path_progress is not None
            else None
        ),
        week_quiz=WeekQuizOut(
            total_attempts=s.week_quiz.total_attempts,
            correct_count=s.week_quiz.correct_count,
            accuracy_percent=s.week_quiz.accuracy_percent,
        ),
        mastery=MasteryOut(
            total_concepts=s.mastery.total_concepts,
            started_count=s.mastery.started_count,
            mastered_count=s.mastery.mastered_count,
        ),
        reflection_count=s.reflection_count,
        today_suggestion=TodaySuggestionOut(
            title=s.today_suggestion.title,
            description=s.today_suggestion.description,
            link=s.today_suggestion.link,
            next_concept_name=s.today_suggestion.next_concept_name,
        ),
    )
