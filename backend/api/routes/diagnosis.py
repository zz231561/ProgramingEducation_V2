"""根源弱點診斷 API（roadmap K3d）。

獨立檔避免 concepts.py 超過 250 行硬性限制；prefix 沿用 /concepts。
純 DB 讀取（無 LLM 呼叫）→ 不掛 rate limit。
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from core.errors import AppError
from models.user import User
from services.diagnosis import DiagnosisResult, diagnose_root_cause

router = APIRouter(prefix="/concepts", tags=["diagnosis"])


class SuspectOut(BaseModel):
    """嫌疑前置節點。"""

    tag: str
    name_zh: str
    depth: int = Field(ge=1, description="距目標的回溯層數（1 = 直接前置）")
    confidence: float | None = Field(default=None, description="null = 從未曝光（盲區）")
    exposure_count: int
    question_id: uuid.UUID | None = Field(default=None, description="題庫診斷題；無題為 null")


class DiagnosisOut(BaseModel):
    """診斷結果。"""

    target_tag: str
    triggered: bool
    recent_failure_streak: int
    suspects: list[SuspectOut]


@router.get("/{tag}/diagnosis", response_model=DiagnosisOut)
async def get_diagnosis(
    tag: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> DiagnosisOut:
    """對指定 concept 執行根源弱點診斷。

    觸發條件：該 concept 最近連續 3 次作答失敗。
    未觸發時回 triggered=false + 空 suspects（前端據此隱藏「找出根本原因」入口）。
    """
    result: DiagnosisResult | None = await diagnose_root_cause(db, user.id, tag)
    if result is None:
        raise AppError(404, "CONCEPT_NOT_FOUND", f"找不到概念：{tag}")

    return DiagnosisOut(
        target_tag=result.target.tag,
        triggered=result.triggered,
        recent_failure_streak=result.recent_failure_streak,
        suspects=[
            SuspectOut(
                tag=s.concept.tag,
                name_zh=s.concept.name_zh,
                depth=s.depth,
                confidence=s.confidence,
                exposure_count=s.exposure_count,
                question_id=s.question_id,
            )
            for s in result.suspects
        ],
    )
