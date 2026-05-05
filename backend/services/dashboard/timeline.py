"""Dashboard 最近活動時間線（roadmap 3-3b）。

事件類型 3 種：
- quiz：學生作答（含對錯）
- reflection：解題前反思建立
- unit_completed：學習單元完成

合併策略：每類各取 limit 筆 → 全集 sort by timestamp desc → 取最終 limit
（避免某類事件刷屏遮蔽其他類型）。

設計取捨：
- 不含 comprehension 事件（schema 沒專屬 completed_at；後續加欄位再加）
- 不含 chat 訊息（量大且不算「學習進度」級別）
- 不分頁；前端只顯示固定 limit 的最近活動，要看完整歷史去 /quiz/history
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.concept import Concept
from models.learning import LearningUnit
from models.quiz import Question, StudentAnswer
from models.reflection import Reflection

ActivityType = Literal["quiz", "reflection", "unit_completed"]


@dataclass(frozen=True)
class ActivityItem:
    """時間線單一事件。type 決定前端 icon 與配色。"""

    type: ActivityType
    timestamp: datetime
    title: str            # 短標題（事件主旨）
    detail: str           # 細節（concept / 題型 / 對錯 etc.）
    link: str | None      # 前端路由（None 表示無對應頁面）
    is_correct: bool | None  # 僅 quiz 事件有意義；其他為 None


async def _list_quiz(
    db: AsyncSession, user_id: UUID, limit: int
) -> list[ActivityItem]:
    rows = (
        await db.execute(
            select(StudentAnswer, Question)
            .join(Question, Question.id == StudentAnswer.question_id)
            .where(StudentAnswer.user_id == user_id)
            .order_by(desc(StudentAnswer.answered_at))
            .limit(limit)
        )
    ).all()
    items: list[ActivityItem] = []
    for ans, q in rows:
        stem = (q.content or {}).get("stem", "")
        verdict = "答對" if ans.is_correct else "答錯"
        items.append(ActivityItem(
            type="quiz",
            timestamp=ans.answered_at,
            title=f"Quiz {verdict}：{stem[:30]}{'...' if len(stem) > 30 else ''}",
            detail=f"題型 {q.type} · 難度 {q.difficulty} · 提示用了 {ans.hint_level_used}/5",
            link="/quiz",
            is_correct=ans.is_correct,
        ))
    return items


async def _list_reflection(
    db: AsyncSession, user_id: UUID, limit: int
) -> list[ActivityItem]:
    rows = list(
        (
            await db.execute(
                select(Reflection)
                .where(Reflection.user_id == user_id)
                .order_by(desc(Reflection.created_at))
                .limit(limit)
            )
        ).scalars().all()
    )
    items: list[ActivityItem] = []
    for r in rows:
        score = (
            f"品質 {round((r.quality_score or 0) * 100)}%"
            if r.quality_score is not None
            else "品質未評"
        )
        items.append(ActivityItem(
            type="reflection",
            timestamp=r.created_at,
            title=f"反思已記錄（{r.source_type}）",
            detail=f"{score} · {len(r.planned_steps or [])} 個步驟",
            link=None,
            is_correct=None,
        ))
    return items


async def _list_completed_units(
    db: AsyncSession, user_id: UUID, limit: int
) -> list[ActivityItem]:
    """完成的 learning_units（透過 path.user_id filter；schema unit 無 user_id）。"""
    from models.learning import LearningPath

    rows = (
        await db.execute(
            select(LearningUnit, Concept)
            .join(Concept, Concept.id == LearningUnit.concept_id)
            .join(LearningPath, LearningPath.id == LearningUnit.path_id)
            .where(LearningPath.user_id == user_id)
            .where(LearningUnit.completed_at.is_not(None))
            .order_by(desc(LearningUnit.completed_at))
            .limit(limit)
        )
    ).all()
    items: list[ActivityItem] = []
    for unit, concept in rows:
        items.append(ActivityItem(
            type="unit_completed",
            timestamp=unit.completed_at,
            title=f"完成學習單元：{concept.name_zh}",
            detail=f"概念 {concept.tag} · 難度 {concept.difficulty_level}",
            link="/learn",
            is_correct=None,
        ))
    return items


async def list_recent_activities(
    db: AsyncSession, user_id: UUID, limit: int = 30
) -> list[ActivityItem]:
    """3 類事件合併取最近 N 筆（每類各先取 limit 筆避免單類刷屏，再 merge）。"""
    quiz = await _list_quiz(db, user_id, limit)
    reflection = await _list_reflection(db, user_id, limit)
    units = await _list_completed_units(db, user_id, limit)
    merged = quiz + reflection + units
    merged.sort(key=lambda x: x.timestamp, reverse=True)
    return merged[:limit]
