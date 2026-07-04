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
from services.learning.remedial import open_remedial_units

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


class RemedialUnitOut(BaseModel):
    """單一補救單元。"""

    unit_id: uuid.UUID
    concept_tag: str
    name_zh: str
    order_index: int
    previous_status: str
    status: str


class RemediateOut(BaseModel):
    """補救路徑開放結果。"""

    target_tag: str
    remedial_units: list[RemedialUnitOut] = Field(
        description="order_index 升冪 = 建議學習順序"
    )


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


@router.post("/{tag}/diagnosis/remediate", response_model=RemediateOut)
async def remediate(
    tag: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> RemediateOut:
    """依診斷結果在學生預設路徑重新開放嫌疑概念的補救單元（K4c）。

    前置：診斷必須已觸發（連續失敗達門檻）；未觸發 → 409。
    """
    result = await diagnose_root_cause(db, user.id, tag)
    if result is None:
        raise AppError(404, "CONCEPT_NOT_FOUND", f"找不到概念：{tag}")
    if not result.triggered:
        raise AppError(
            409,
            "DIAGNOSIS_NOT_TRIGGERED",
            "尚未達到診斷觸發條件（連續失敗不足），無補救路徑可開放",
        )

    units = await open_remedial_units(
        db, user.id, [s.concept.id for s in result.suspects]
    )
    return RemediateOut(
        target_tag=result.target.tag,
        remedial_units=[
            RemedialUnitOut(
                unit_id=u.unit_id,
                concept_tag=u.concept_tag,
                name_zh=u.name_zh,
                order_index=u.order_index,
                previous_status=u.previous_status,
                status=u.status,
            )
            for u in units
        ],
    )
