"""學習路徑 API — 路徑 CRUD + 生成（roadmap 3-1c）。

API 設計：
- POST   /learning/paths         — 生成新路徑（拓撲 + 弱項補強）
- GET    /learning/paths         — 列出該使用者所有路徑（含進度概覽）
- GET    /learning/paths/{id}    — 取單一路徑詳細（含 units + concept 資訊）
- DELETE /learning/paths/{id}    — 刪除路徑（CASCADE 連動 units）
"""

import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from models.user import User
from services.learning import (
    DEFAULT_SKIP_MASTERED_THRESHOLD,
    delete_path,
    generate_learning_path,
    get_path_with_units,
    list_paths_for_user,
)

router = APIRouter(prefix="/learning", tags=["learning"])


# === Schemas ===


class GeneratePathRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    category: str | None = Field(default=None, max_length=50)
    skip_mastered_threshold: float = Field(
        default=DEFAULT_SKIP_MASTERED_THRESHOLD, ge=0.0, le=1.0
    )


class PathSummaryOut(BaseModel):
    """list 用 — 含進度概覽。"""

    id: uuid.UUID
    title: str
    description: str
    total_units: int
    completed_units: int
    available_units: int
    created_at: str
    updated_at: str


class ListPathsOut(BaseModel):
    paths: list[PathSummaryOut]


class UnitOut(BaseModel):
    id: uuid.UUID
    concept_id: uuid.UUID
    concept_tag: str
    concept_name_zh: str
    concept_difficulty: int
    order_index: int
    status: str
    completed_at: str | None
    content: dict


class PathDetailOut(BaseModel):
    """detail 用 — 含 units 列表。"""

    id: uuid.UUID
    title: str
    description: str
    units: list[UnitOut]
    created_at: str
    updated_at: str


# === Endpoints ===


@router.post("/paths", response_model=PathDetailOut, status_code=status.HTTP_201_CREATED)
async def create_path(
    body: GeneratePathRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> PathDetailOut:
    """生成新學習路徑（拓撲排序 + 弱項補強）。"""
    path = await generate_learning_path(
        db,
        user_id=user.id,
        title=body.title,
        description=body.description,
        category=body.category,
        skip_mastered_threshold=body.skip_mastered_threshold,
    )
    # 重新讀完整 detail（含 units + concept join）以對齊 GET 形狀
    _, units = await get_path_with_units(db, path.id, user.id)
    return PathDetailOut(
        id=path.id,
        title=path.title,
        description=path.description,
        units=[
            UnitOut(
                id=u.unit.id,
                concept_id=u.unit.concept_id,
                concept_tag=u.concept_tag,
                concept_name_zh=u.concept_name_zh,
                concept_difficulty=u.concept_difficulty,
                order_index=u.unit.order_index,
                status=u.unit.status,
                completed_at=u.unit.completed_at.isoformat() if u.unit.completed_at else None,
                content=u.unit.content or {},
            )
            for u in units
        ],
        created_at=path.created_at.isoformat(),
        updated_at=path.updated_at.isoformat(),
    )


@router.get("/paths", response_model=ListPathsOut)
async def list_paths(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> ListPathsOut:
    """列出當前使用者所有路徑（按 created_at 降冪）。"""
    summaries = await list_paths_for_user(db, user.id)
    return ListPathsOut(
        paths=[
            PathSummaryOut(
                id=s.path.id,
                title=s.path.title,
                description=s.path.description,
                total_units=s.total_units,
                completed_units=s.completed_units,
                available_units=s.available_units,
                created_at=s.path.created_at.isoformat(),
                updated_at=s.path.updated_at.isoformat(),
            )
            for s in summaries
        ]
    )


@router.get("/paths/{path_id}", response_model=PathDetailOut)
async def get_path(
    path_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> PathDetailOut:
    """取單一路徑詳細（含 units + concept 資訊）。404 若非本人擁有。"""
    path, units = await get_path_with_units(db, path_id, user.id)
    return PathDetailOut(
        id=path.id,
        title=path.title,
        description=path.description,
        units=[
            UnitOut(
                id=u.unit.id,
                concept_id=u.unit.concept_id,
                concept_tag=u.concept_tag,
                concept_name_zh=u.concept_name_zh,
                concept_difficulty=u.concept_difficulty,
                order_index=u.unit.order_index,
                status=u.unit.status,
                completed_at=u.unit.completed_at.isoformat() if u.unit.completed_at else None,
                content=u.unit.content or {},
            )
            for u in units
        ],
        created_at=path.created_at.isoformat(),
        updated_at=path.updated_at.isoformat(),
    )


@router.delete("/paths/{path_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_path_route(
    path_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> None:
    """刪除路徑（CASCADE 連動 units）。404 若非本人擁有。"""
    await delete_path(db, path_id, user.id)
