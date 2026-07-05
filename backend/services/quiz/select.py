"""出題 Select 階段 — 從學生 student_mastery 選弱項概念，並用圖譜中心度加權。

設計（roadmap 2-4b）：
- 弱項定義：`effective confidence < WEAK_THRESHOLD` 且 `exposure_count >= 1`
  （未互動過的不算「弱」，那是「未接觸」由 cold-start 處理）
- K6b（2026-07-06）：改用衰減後 effective confidence——久未練習的概念會
  「衰減回弱項」重新被選中，這正是遺忘曲線驅動複習的機制；因衰減須在
  Python 端計算，改為撈出全部已曝光 rows 再過濾（每人 ≤62 concepts 可接受）
- 圖譜中心度加權：一個弱項概念若有越多後續概念依賴它（prerequisite 出度高），
  優先補強——因為它的弱會 cascade 影響後續學習
- score = (1 - confidence) * (1 + CENTRALITY_BONUS * out_degree)
- 排序 score 降冪，回傳前 top_k 個 Concept 物件

Cold-start：學生尚無 mastery rows → 回空 list；caller（2-4c Generate）自行決定。
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.concept import Concept, ConceptEdge, EdgeType
from models.mastery import StudentMastery
from services.mastery.decay import effective_confidence

# Confidence < 此值視為弱項；對齊前端 mastery_band 的 struggling 邊界
WEAK_THRESHOLD = 0.4

# 中心度加權係數：每多一個後續依賴 +20% 優先度
CENTRALITY_BONUS = 0.2


async def select_weak_concepts(
    db: AsyncSession,
    user_id: UUID,
    top_k: int = 5,
) -> list[Concept]:
    """選出該使用者最該補強的弱項概念。

    Args:
        db: SQLAlchemy async session
        user_id: 學生 UUID
        top_k: 回傳上限（預設 5）

    Returns:
        Concept 列表，依「弱度 × 中心度」降冪排序；學生無 mastery 紀錄回空 list。
    """
    exposed_stmt = (
        select(
            Concept,
            StudentMastery.confidence,
            StudentMastery.last_practiced_at,
            StudentMastery.success_count,
        )
        .join(StudentMastery, StudentMastery.concept_id == Concept.id)
        .where(
            StudentMastery.user_id == user_id,
            StudentMastery.exposure_count >= 1,
        )
    )
    exposed_rows = list((await db.execute(exposed_stmt)).tuples())

    # K6b：以衰減後 effective confidence 判弱
    weak_rows: list[tuple[Concept, float]] = [
        (c, eff)
        for c, conf, last_at, successes in exposed_rows
        if (eff := effective_confidence(conf, last_at, successes)) < WEAK_THRESHOLD
    ]

    if not weak_rows:
        return []

    # 取每個弱項概念的 prerequisite 出度（後續多少概念依賴它）
    weak_ids = [c.id for c, _ in weak_rows]
    degree_stmt = (
        select(
            ConceptEdge.source_id,
            func.count(ConceptEdge.id).label("out_degree"),
        )
        .where(
            ConceptEdge.source_id.in_(weak_ids),
            ConceptEdge.edge_type == EdgeType.PREREQUISITE,
        )
        .group_by(ConceptEdge.source_id)
    )
    degree_map: dict[UUID, int] = {
        row.source_id: row.out_degree
        for row in (await db.execute(degree_stmt)).all()
    }

    scored: list[tuple[Concept, float]] = [
        (c, (1.0 - conf) * (1.0 + CENTRALITY_BONUS * degree_map.get(c.id, 0)))
        for c, conf in weak_rows
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [c for c, _ in scored[:top_k]]
