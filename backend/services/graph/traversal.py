"""知識圖譜走訪 — prerequisite 回溯查詢（roadmap K1b）。

K3 根源弱點定位的基礎：從任一 concept 沿 PREREQUISITE 邊向前置方向 BFS，
取得完整（或限深）的先備概念閉包。

效能設計：62 節點 / ~90 邊的量級，一次載入全部 PREREQUISITE 邊在記憶體 BFS
（單一 SQL 查詢），比逐層遞迴查詢或 recursive CTE 更簡單且足夠快；
節點數成長至數千前不需改寫。
"""

from collections import deque
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.concept import Concept, ConceptEdge, EdgeType


@dataclass(frozen=True)
class PrerequisiteClosure:
    """單一概念的先備概念閉包。"""

    center: Concept
    # (concept, depth)；depth=1 為直接前置，依 BFS 層序排列（同層依 video_order）
    ancestors: list[tuple[Concept, int]]


async def get_prerequisite_closure(
    db: AsyncSession,
    tag: str,
    max_depth: int | None = None,
) -> PrerequisiteClosure | None:
    """沿 PREREQUISITE 邊向前置方向 BFS，回傳指定概念的先備閉包。

    Args:
        db: SQLAlchemy async session
        tag: 起點概念 tag（如 "cpp-47-recursion"）
        max_depth: 回溯層數上限；None = 走到底（K3 診斷通常限 2-3 層）

    Returns:
        PrerequisiteClosure；tag 不存在回傳 None。
        ancestors 依 (depth, video_order) 排序 — 診斷時「先看最近的前置」。
    """
    center = (
        await db.execute(select(Concept).where(Concept.tag == tag))
    ).scalar_one_or_none()
    if center is None:
        return None

    # 一次載入全部 PREREQUISITE 邊 → 反向鄰接表（target → sources）
    edges = (
        await db.execute(
            select(ConceptEdge.source_id, ConceptEdge.target_id).where(
                ConceptEdge.edge_type == EdgeType.PREREQUISITE
            )
        )
    ).all()
    parents: dict[UUID, list[UUID]] = {}
    for source_id, target_id in edges:
        parents.setdefault(target_id, []).append(source_id)

    # BFS 回溯（visited 防多對多圖中的菱形重複展開）
    depth_by_id: dict[UUID, int] = {}
    queue: deque[tuple[UUID, int]] = deque([(center.id, 0)])
    visited: set[UUID] = {center.id}
    while queue:
        node_id, depth = queue.popleft()
        if max_depth is not None and depth >= max_depth:
            continue
        for parent_id in parents.get(node_id, []):
            if parent_id in visited:
                continue
            visited.add(parent_id)
            depth_by_id[parent_id] = depth + 1
            queue.append((parent_id, depth + 1))

    if not depth_by_id:
        return PrerequisiteClosure(center=center, ancestors=[])

    rows = (
        await db.execute(select(Concept).where(Concept.id.in_(depth_by_id.keys())))
    ).scalars().all()
    ancestors = sorted(
        ((c, depth_by_id[c.id]) for c in rows),
        key=lambda pair: (pair[1], pair[0].video_order or 0),
    )
    return PrerequisiteClosure(center=center, ancestors=ancestors)
