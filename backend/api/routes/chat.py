"""Chat API — 教學互動 + 對話歷史管理。"""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db, User
from core.errors import AppError
from services.chat import interact, list_sessions, get_session_messages, delete_session

router = APIRouter(prefix="/chat", tags=["chat"])


# === Request / Response schemas ===

class InteractRequest(BaseModel):
    """教學互動請求。"""

    code: str = Field(..., min_length=1, max_length=50_000)
    question: str = Field(..., min_length=1, max_length=2_000)
    session_id: uuid.UUID | None = Field(default=None)
    hint_level: int = Field(default=0, ge=0, le=5)
    execution_result: dict | None = Field(default=None)


class MessageOut(BaseModel):
    """單則訊息回應。"""

    id: uuid.UUID
    role: str
    content: str
    code_snapshot: str | None = None
    evidence: dict | None = None
    created_at: str

    model_config = {"from_attributes": True}


class InteractResponse(BaseModel):
    """教學互動回應。"""

    session_id: uuid.UUID
    user_message: MessageOut
    assistant_message: MessageOut


class SessionOut(BaseModel):
    """Session 摘要。"""

    id: uuid.UUID
    title: str
    updated_at: str

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    """Session 列表回應。"""

    sessions: list[SessionOut]
    total: int


class SessionDetailResponse(BaseModel):
    """Session 詳情（含訊息）。"""

    session: SessionOut
    messages: list[MessageOut]


# === Endpoints ===

@router.post("/interact", response_model=InteractResponse)
async def chat_interact(
    body: InteractRequest,
    user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
) -> InteractResponse:
    """主要教學互動 — 串接 EDF Pipeline。"""
    session, user_msg, ai_msg = await interact(
        db=db,
        user_id=user.id,
        code=body.code,
        question=body.question,
        session_id=body.session_id,
        hint_level=body.hint_level,
        execution_result=body.execution_result,
    )

    return InteractResponse(
        session_id=session.id,
        user_message=MessageOut(
            id=user_msg.id,
            role=user_msg.role.value,
            content=user_msg.content,
            code_snapshot=user_msg.code_snapshot,
            evidence=None,
            created_at=str(user_msg.created_at),
        ),
        assistant_message=MessageOut(
            id=ai_msg.id,
            role=ai_msg.role.value,
            content=ai_msg.content,
            code_snapshot=None,
            evidence=ai_msg.evidence,
            created_at=str(ai_msg.created_at),
        ),
    )


@router.get("/sessions", response_model=SessionListResponse)
async def get_sessions(
    user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> SessionListResponse:
    """取得使用者所有對話 session。"""
    sessions, total = await list_sessions(db, user.id, page, limit)
    return SessionListResponse(
        sessions=[
            SessionOut(id=s.id, title=s.title, updated_at=str(s.updated_at))
            for s in sessions
        ],
        total=total,
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: uuid.UUID,
    user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
) -> SessionDetailResponse:
    """取得特定 session 的訊息歷史。"""
    session = await get_session_messages(db, user.id, session_id)
    if not session:
        raise AppError(404, "NOT_FOUND", "找不到該對話")

    return SessionDetailResponse(
        session=SessionOut(id=session.id, title=session.title, updated_at=str(session.updated_at)),
        messages=[
            MessageOut(
                id=m.id,
                role=m.role.value,
                content=m.content,
                code_snapshot=m.code_snapshot,
                evidence=m.evidence,
                created_at=str(m.created_at),
            )
            for m in session.messages
        ],
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def remove_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """刪除對話 session。"""
    deleted = await delete_session(db, user.id, session_id)
    if not deleted:
        raise AppError(404, "NOT_FOUND", "找不到該對話")
