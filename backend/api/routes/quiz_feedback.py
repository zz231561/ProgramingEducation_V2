"""Quiz 作答後 EDF 回饋 API（roadmap 3-2c）。

獨立檔避免 quiz.py 超過 250 行硬性限制。

API：
- GET /quiz/answers/{answer_id}/feedback
  → 含學生在相關概念的 BKT mastery + LLM 個人化建議 + 推薦學習單元

與 /quiz/submit 的 feedback 欄位（即時對錯一句話）分離；本 endpoint 含 LLM 慢呼叫。
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from models.user import User
from services.quiz import generate_quiz_feedback

router = APIRouter(prefix="/quiz", tags=["quiz"])


class ConceptMasteryOut(BaseModel):
    concept_tag: str
    concept_name_zh: str
    confidence: float


class RecommendedUnitOut(BaseModel):
    unit_id: uuid.UUID
    path_id: uuid.UUID
    concept_tag: str
    concept_name_zh: str
    video_order: int | None
    status: str


class QuizFeedbackResponse(BaseModel):
    concept_mastery: list[ConceptMasteryOut]
    suggestion: str
    suggestion_fallback: bool  # True = LLM 失敗用了固定模板
    recommended_units: list[RecommendedUnitOut]


@router.get("/answers/{answer_id}/feedback", response_model=QuizFeedbackResponse)
async def quiz_feedback(
    answer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> QuizFeedbackResponse:
    """作答後的 EDF 回饋。404 若非本人作答或不存在。"""
    result = await generate_quiz_feedback(db, user.id, answer_id)
    return QuizFeedbackResponse(
        concept_mastery=[
            ConceptMasteryOut(
                concept_tag=m.concept_tag,
                concept_name_zh=m.concept_name_zh,
                confidence=m.confidence,
            )
            for m in result.concept_mastery
        ],
        suggestion=result.suggestion,
        suggestion_fallback=result.suggestion_fallback,
        recommended_units=[
            RecommendedUnitOut(
                unit_id=u.unit_id,
                path_id=u.path_id,
                concept_tag=u.concept_tag,
                concept_name_zh=u.concept_name_zh,
                video_order=u.video_order,
                status=u.status,
            )
            for u in result.recommended_units
        ],
    )
