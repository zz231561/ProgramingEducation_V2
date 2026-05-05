"""學生 Dashboard service — 統計卡片 + 今日建議（roadmap 3-3a）。"""

from services.dashboard.queries import (
    DashboardStats,
    MasteryOverview,
    PathProgressSummary,
    TodaySuggestion,
    WeekQuizStats,
    get_dashboard_stats,
)

__all__ = [
    "DashboardStats",
    "MasteryOverview",
    "PathProgressSummary",
    "TodaySuggestion",
    "WeekQuizStats",
    "get_dashboard_stats",
]
