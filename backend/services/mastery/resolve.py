"""EDF ConceptTag → concept 解析（roadmap K2a）。

三層 fan-out 策略 — 讓 Workspace 對話重新驅動 BKT，
同時避免粗 tag（如 control-flow 對映 11 個影片 concept）的
對話噪音淹沒 quiz / comprehension 的精準信號：

1. tag 直接命中 `concepts.tag` → 只更新該 concept（原行為，backward compat）
2. tag 命中 `concepts.edf_parent_tag` 群組 → 只更新該生「已曝光」
   （已有 mastery row）的組內 concepts — 對話是既學內容的精煉信號
3. 組內全未曝光 → 只更新組內 video_order 最小的入門 concept — 冷啟動落點
4. 兩者皆未命中（如課綱未涵蓋的 stl-containers）→ 回空 list，caller 跳過
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.concept import Concept
from models.mastery import StudentMastery


async def resolve_concept_ids_for_tag(
    db: AsyncSession,
    user_id: UUID,
    tag: str,
) -> list[UUID]:
    """把 EDF evidence tag 解析為應更新 mastery 的 concept id 列表。

    Args:
        db: SQLAlchemy async session
        user_id: 學生（第 2 層「已曝光」判斷需要）
        tag: EDF evidence 的 concept tag（可能是影片 tag 或 20 粗 tag 之一）

    Returns:
        待更新的 concept ids；無對應回 []。
    """
    # 第 1 層：直接命中
    direct = (
        await db.execute(select(Concept.id).where(Concept.tag == tag))
    ).scalar_one_or_none()
    if direct is not None:
        return [direct]

    # 第 2 層：parent group（依 video_order 排序，供第 3 層取入門 concept）
    group_ids = list(
        (
            await db.execute(
                select(Concept.id)
                .where(Concept.edf_parent_tag == tag)
                .order_by(Concept.video_order)
            )
        ).scalars().all()
    )
    if not group_ids:
        return []

    exposed = list(
        (
            await db.execute(
                select(StudentMastery.concept_id).where(
                    StudentMastery.user_id == user_id,
                    StudentMastery.concept_id.in_(group_ids),
                )
            )
        ).scalars().all()
    )
    if exposed:
        return exposed

    # 第 3 層：冷啟動 → 組內入門 concept
    return [group_ids[0]]
