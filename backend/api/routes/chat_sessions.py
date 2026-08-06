"""Chat 對話歷史 API — session 列表 / 詳情 / 刪除。

由 `chat.py` 拆出（250 行硬性線）：該檔保留教學互動端點（interact / kickoff /
compile-error），本檔只處理歷史管理。共用的 `MessageOut` 仍由 `chat.py` 提供。
"""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db, User
from api.routes.chat import MessageOut
from core.errors import AppError
from services.chat_sessions import delete_session, get_session_messages, list_sessions

router = APIRouter(prefix="/chat", tags=["chat"])


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
                citations=m.citations,
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
