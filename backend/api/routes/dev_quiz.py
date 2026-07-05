"""開發者模式 quiz 端點（DEV-8/9）— 診斷模擬 + 題庫檢視。

與 `dev.py` 同掛 `/dev` prefix，拆檔控制大小；全部端點掛 `require_dev_user`。
業務邏輯在 `services/dev_quiz_tools.py`。
"""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, require_dev_user
from models.user import User
from services.dev_quiz_tools import list_questions_by_tag, simulate_failures

router = APIRouter(prefix="/dev", tags=["dev"])


class SimulateFailuresIn(BaseModel):
    """診斷模擬請求。"""

    tag: str = Field(min_length=1)
    count: int = Field(default=3, ge=1, le=10)


class SimulateFailuresOut(BaseModel):
    """注入結果 + 最新診斷摘要。"""

    injected: int
    streak: int
    triggered: bool
    suspect_tags: list[str]


class BankQuestionOut(BaseModel):
    """題庫題目摘要。"""

    id: uuid.UUID
    type: str
    bloom_level: int
    difficulty: int
    source: str
    validated: bool
    stem: str


class BankQuestionsOut(BaseModel):
    """題庫檢視回應。"""

    questions: list[BankQuestionOut]


@router.post("/simulate-failures", response_model=SimulateFailuresOut)
async def dev_simulate_failures(
    body: SimulateFailuresIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_dev_user),
) -> SimulateFailuresOut:
    """注入指定 concept 連續答錯 N 次，觸發 K3 診斷（DEV-8）。"""
    result = await simulate_failures(db, user.id, body.tag, body.count)
    return SimulateFailuresOut(
        injected=body.count,
        streak=result.recent_failure_streak,
        triggered=result.triggered,
        suspect_tags=[s.concept.tag for s in result.suspects],
    )


@router.get("/questions", response_model=BankQuestionsOut)
async def dev_list_questions(
    tag: str = Query(min_length=1),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_dev_user),
) -> BankQuestionsOut:
    """列出指定 concept 的題庫題目（DEV-9）。"""
    questions = await list_questions_by_tag(db, tag)
    return BankQuestionsOut(
        questions=[
            BankQuestionOut(
                id=q.id,
                type=q.type,
                bloom_level=q.bloom_level,
                difficulty=q.difficulty,
                source=q.source,
                validated=q.validated,
                stem=str((q.content or {}).get("stem", ""))[:160],
            )
            for q in questions
        ]
    )
