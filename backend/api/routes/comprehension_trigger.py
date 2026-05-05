"""Comprehension trigger-suggestion API（roadmap 2-6e）。

獨立檔避免主 comprehension.py 超過 250 行硬性限制。

API：
- GET /comprehension/trigger-suggestion/{student_answer_id}
  → 依學生過往通過率 + 當前題型，建議是否觸發 + 哪一種 comprehension type

前端用法：
- 學生答對題目後呼叫此端點
- should_trigger=False → 直接結束
- should_trigger=True → 顯示對應類型的 comprehension UI（呼叫 epl/predict/variation generate）
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from models.user import User
from services.comprehension import decide_trigger

router = APIRouter(prefix="/comprehension", tags=["comprehension"])


class TriggerDecisionOut(BaseModel):
    student_answer_id: uuid.UUID
    should_trigger: bool
    suggested_type: str | None  # epl / predict_output / variation / None
    pass_rate: float | None  # None = 無歷史
    sample_size: int
    reason: str


@router.get(
    "/trigger-suggestion/{student_answer_id}", response_model=TriggerDecisionOut
)
async def trigger_suggestion(
    student_answer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> TriggerDecisionOut:
    """為當前 student_answer 計算 trigger 建議。404 若非本人擁有。"""
    decision = await decide_trigger(db, user.id, student_answer_id)
    return TriggerDecisionOut(
        student_answer_id=student_answer_id,
        should_trigger=decision.should_trigger,
        suggested_type=decision.suggested_type.value if decision.suggested_type else None,
        pass_rate=decision.pass_rate,
        sample_size=decision.sample_size,
        reason=decision.reason,
    )
