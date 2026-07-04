"""Reflection API — 解題前反思 CRUD（roadmap 2-5a）。

API spec 對齊 docs/api-spec.md：
- POST /reflection            — 建立反思
- GET /reflection/{id}        — 取得反思
- PATCH /reflection/{id}      — 更新反思（補充回答 / 修改計畫）

LLM 品質評分（quality_score / followup_question）留給 2-5b 注入；本層回傳
固定 nullable 欄位，不阻擋 caller 提前讀取。
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from core.rate_limit import rate_limit
from models.reflection import Reflection, ReflectionSourceType
from models.user import User
from services.reflection import (
    ReflectionUpdate,
    create_reflection,
    get_reflection,
    update_reflection,
)

router = APIRouter(prefix="/reflection", tags=["reflection"])


# === Schemas ===


class CreateReflectionRequest(BaseModel):
    source_type: str = Field(..., description="quiz | learning_unit")
    source_id: uuid.UUID
    problem_understanding: str = Field(default="", max_length=2000)
    planned_steps: list[str] = Field(default_factory=list, max_length=20)
    expected_concepts: str = Field(default="", max_length=500)


class PatchReflectionRequest(BaseModel):
    planned_steps: list[str] | None = Field(default=None, max_length=20)
    expected_concepts: str | None = Field(default=None, max_length=500)
    followup_answer: str | None = Field(default=None, max_length=2000)
    problem_understanding: str | None = Field(default=None, max_length=2000)


class ReflectionOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    source_type: str
    source_id: uuid.UUID
    problem_understanding: str
    planned_steps: list[str]
    expected_concepts: str
    quality_score: float | None
    followup_question: str | None
    followup_answer: str | None
    is_modified: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, r: Reflection) -> "ReflectionOut":
        return cls(
            id=r.id,
            user_id=r.user_id,
            source_type=r.source_type,
            source_id=r.source_id,
            problem_understanding=r.problem_understanding,
            planned_steps=list(r.planned_steps or []),
            expected_concepts=r.expected_concepts,
            quality_score=r.quality_score,
            followup_question=r.followup_question,
            followup_answer=r.followup_answer,
            is_modified=r.is_modified,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat(),
        )


# === Endpoints ===


@router.post(
    "",
    response_model=ReflectionOut,
    status_code=201,
    dependencies=[Depends(rate_limit("llm"))],
)
async def create(
    body: CreateReflectionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> ReflectionOut:
    """建立反思。Pydantic 校驗 source_type 由 service 透過 enum 解析（無效值回 422）。"""
    source_type = _parse_source_type(body.source_type)
    reflection = await create_reflection(
        db,
        user_id=user.id,
        source_type=source_type,
        source_id=body.source_id,
        problem_understanding=body.problem_understanding,
        planned_steps=body.planned_steps,
        expected_concepts=body.expected_concepts,
    )
    return ReflectionOut.from_model(reflection)


@router.get("/{reflection_id}", response_model=ReflectionOut)
async def get(
    reflection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> ReflectionOut:
    reflection = await get_reflection(db, reflection_id, user.id)
    return ReflectionOut.from_model(reflection)


@router.patch("/{reflection_id}", response_model=ReflectionOut)
async def patch(
    reflection_id: uuid.UUID,
    body: PatchReflectionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> ReflectionOut:
    reflection = await update_reflection(
        db,
        reflection_id=reflection_id,
        user_id=user.id,
        payload=ReflectionUpdate(
            planned_steps=body.planned_steps,
            expected_concepts=body.expected_concepts,
            followup_answer=body.followup_answer,
            problem_understanding=body.problem_understanding,
        ),
    )
    return ReflectionOut.from_model(reflection)


def _parse_source_type(value: str) -> ReflectionSourceType:
    """422 if invalid — 走 Pydantic 的 ValueError 路徑。"""
    try:
        return ReflectionSourceType(value)
    except ValueError as exc:
        from core.errors import AppError

        raise AppError(
            422,
            "INVALID_SOURCE_TYPE",
            f"source_type 必須為 quiz 或 learning_unit，收到：{value}",
        ) from exc
