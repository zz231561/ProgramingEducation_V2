"""學生 Dashboard service — 統計 + 建議 + 時間線 + 精熟度總覽（roadmap 3-3a/b/c）。"""

from services.dashboard.mastery import (
    CategoryBreakdown,
    ConceptMasteryDetail,
    MasteryBreakdown,
    get_mastery_breakdown,
)
from services.dashboard.queries import (
    DashboardStats,
    MasteryOverview,
    PathProgressSummary,
    TodaySuggestion,
    WeekQuizStats,
    get_dashboard_stats,
)
from services.dashboard.timeline import (
    ActivityItem,
    ActivityType,
    list_recent_activities,
)

__all__ = [
    "ActivityItem",
    "ActivityType",
    "CategoryBreakdown",
    "ConceptMasteryDetail",
    "DashboardStats",
    "MasteryBreakdown",
    "MasteryOverview",
    "PathProgressSummary",
    "TodaySuggestion",
    "WeekQuizStats",
    "get_dashboard_stats",
    "get_mastery_breakdown",
    "list_recent_activities",
]
