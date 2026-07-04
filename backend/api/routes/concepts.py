"""Concepts API — 知識圖譜全圖 + 單節點鄰居查詢。

對應 roadmap 2-2b。前端 Cytoscape (2-2c) 與 Concept Detail Panel (2-2d) 消費這些端點。
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from core.errors import AppError
from models.concept import Concept, ConceptEdge
from models.user import User
from services.graph import (
    ConceptNeighborhood,
    GraphSnapshot,
    get_concept_neighborhood,
    get_full_graph,
)
from services.mastery import MasterySummaryEntry, get_user_mastery_summary

router = APIRouter(prefix="/concepts", tags=["concepts"])


# === Response schemas ===


class ConceptOut(BaseModel):
    """節點輸出（含完整 metadata；給 Detail Panel 用）。"""

    id: uuid.UUID
    tag: str
    name_zh: str
    name_en: str
    description: str
    difficulty_level: int = Field(ge=1, le=5)
    category: str

    @classmethod
    def from_orm(cls, c: Concept) -> "ConceptOut":
        return cls(
            id=c.id,
            tag=c.tag,
            name_zh=c.name_zh,
            name_en=c.name_en,
            description=c.description,
            difficulty_level=c.difficulty_level,
            category=c.category,
        )


class EdgeOut(BaseModel):
    """邊輸出（Cytoscape 慣用 source/target 命名）。"""

    id: uuid.UUID
    source: uuid.UUID
    target: uuid.UUID
    edge_type: str
    weight: float

    @classmethod
    def from_orm(cls, e: ConceptEdge) -> "EdgeOut":
        return cls(
            id=e.id,
            source=e.source_id,
            target=e.target_id,
            edge_type=e.edge_type.value if hasattr(e.edge_type, "value") else str(e.edge_type),
            weight=e.weight,
        )


class GraphOut(BaseModel):
    """全圖回應 — Cytoscape 友善格式。"""

    nodes: list[ConceptOut]
    edges: list[EdgeOut]


class NeighborOut(BaseModel):
    """單節點鄰居（含方向：incoming = 邊指向 center，outgoing = 邊從 center 出發）。"""

    direction: str = Field(description="incoming | outgoing")
    edge: EdgeOut
    concept: ConceptOut


class ConceptDetailOut(BaseModel):
    """單節點詳情 + depth-1 鄰居。"""

    concept: ConceptOut
    neighbors: list[NeighborOut]


class MasteryEntryOut(BaseModel):
    """單一 concept 的精熟度（給前端 Knowledge Graph 著色用）。"""

    tag: str
    confidence: float = Field(ge=0, le=1)
    exposure_count: int
    success_count: int
    error_count: int
    bloom_level: int | None
    # K2b：最近練習時間（ISO 字串；K4 Coddy prompt 的時序信號）
    last_practiced_at: str | None = None

    @classmethod
    def from_summary(cls, e: MasterySummaryEntry) -> "MasteryEntryOut":
        return cls(
            tag=e.tag,
            confidence=e.confidence,
            exposure_count=e.exposure_count,
            success_count=e.success_count,
            error_count=e.error_count,
            bloom_level=e.bloom_level,
            last_practiced_at=(
                str(e.last_practiced_at) if e.last_practiced_at else None
            ),
        )


# === Endpoints ===


@router.get("/graph", response_model=GraphOut)
async def get_graph(
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_db_user),
) -> GraphOut:
    """回傳全部 concepts + edges（一次性供前端 Cytoscape 渲染整圖）。"""
    snapshot: GraphSnapshot = await get_full_graph(db)
    return GraphOut(
        nodes=[ConceptOut.from_orm(c) for c in snapshot.concepts],
        edges=[EdgeOut.from_orm(e) for e in snapshot.edges],
    )


@router.get("/mastery", response_model=list[MasteryEntryOut])
async def get_my_mastery(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> list[MasteryEntryOut]:
    """回傳當前使用者所有 concept 的精熟度（沒互動過的 concept 不會出現）。

    供 Knowledge 頁面繪製節點外圈著色（綠/黃/紅 = mastered/learning/struggling）。
    """
    summaries = await get_user_mastery_summary(db, user.id)
    return [MasteryEntryOut.from_summary(s) for s in summaries]


@router.get("/{tag}", response_model=ConceptDetailOut)
async def get_concept_detail(
    tag: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_db_user),
) -> ConceptDetailOut:
    """以 tag 取單一 concept + 所有相連邊 + 鄰居 concepts。

    - direction=outgoing：center → neighbor（如「center 是 neighbor 的 prerequisite」）
    - direction=incoming：neighbor → center
    """
    nbhd: ConceptNeighborhood | None = await get_concept_neighborhood(db, tag)
    if nbhd is None:
        raise AppError(404, "CONCEPT_NOT_FOUND", f"找不到概念：{tag}")

    neighbors: list[NeighborOut] = []
    for edge in nbhd.edges:
        if edge.source_id == nbhd.center.id:
            direction = "outgoing"
            neighbor_id = edge.target_id
        else:
            direction = "incoming"
            neighbor_id = edge.source_id

        neighbor_concept = nbhd.neighbors_by_id.get(neighbor_id)
        if neighbor_concept is None:
            # 資料不一致（FK 應防止）— 跳過避免 500
            continue

        neighbors.append(
            NeighborOut(
                direction=direction,
                edge=EdgeOut.from_orm(edge),
                concept=ConceptOut.from_orm(neighbor_concept),
            )
        )

    return ConceptDetailOut(
        concept=ConceptOut.from_orm(nbhd.center),
        neighbors=neighbors,
    )
