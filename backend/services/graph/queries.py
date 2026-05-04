"""知識圖譜查詢函式 — 純 DB 讀取，回傳 ORM 物件給 route 層做 serialization。"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.concept import Concept, ConceptEdge


@dataclass(frozen=True)
class GraphSnapshot:
    """全圖一次性快照。"""

    concepts: list[Concept]
    edges: list[ConceptEdge]


@dataclass(frozen=True)
class ConceptNeighborhood:
    """單節點 + depth-1 鄰居。"""

    center: Concept
    edges: list[ConceptEdge]  # 所有觸碰 center 的邊（無論方向）
    neighbors_by_id: dict[UUID, Concept]  # 鄰居 concept 以 id 索引


async def get_full_graph(db: AsyncSession) -> GraphSnapshot:
    """讀取所有 concepts + edges 一次回傳（供 Cytoscape 整圖渲染）。

    全圖目前 20 節點 + 預期數十邊以內，無需分頁；後續若超過 200+ 邊再考慮過濾。
    """
    concepts = list(
        (await db.execute(select(Concept).order_by(Concept.tag))).scalars().all()
    )
    edges = list((await db.execute(select(ConceptEdge))).scalars().all())
    return GraphSnapshot(concepts=concepts, edges=edges)


async def get_concept_neighborhood(
    db: AsyncSession, tag: str
) -> ConceptNeighborhood | None:
    """以 tag 取單一 concept + 所有相連邊 + depth-1 鄰居。

    Args:
        db: SQLAlchemy async session
        tag: 概念 tag（如 "pointer-arithmetic"）— 比 UUID 更穩定 + URL 友善

    Returns:
        ConceptNeighborhood 物件，若 tag 不存在回傳 None。
    """
    center = (
        await db.execute(select(Concept).where(Concept.tag == tag))
    ).scalar_one_or_none()
    if center is None:
        return None

    edges = list(
        (
            await db.execute(
                select(ConceptEdge).where(
                    or_(
                        ConceptEdge.source_id == center.id,
                        ConceptEdge.target_id == center.id,
                    )
                )
            )
        )
        .scalars()
        .all()
    )

    neighbor_ids = {
        (e.target_id if e.source_id == center.id else e.source_id) for e in edges
    }

    neighbors_by_id: dict[UUID, Concept] = {}
    if neighbor_ids:
        neighbor_rows = (
            await db.execute(select(Concept).where(Concept.id.in_(neighbor_ids)))
        ).scalars().all()
        neighbors_by_id = {c.id: c for c in neighbor_rows}

    return ConceptNeighborhood(
        center=center,
        edges=edges,
        neighbors_by_id=neighbors_by_id,
    )
