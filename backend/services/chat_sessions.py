"""Chat session 的 CRUD — 建立／列表／讀取／刪除。

自 `chat.py` 抽出：該檔超過 250 行硬上限，而且同時裝了
兩件事——「對話容器的管理」與「EDF 三層管線」。前者是單純的資料操作，
後者是教學邏輯，沒有共用狀態，切開後兩邊都好讀。
"""

import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.chat import ChatSession


async def get_or_create_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID | None,
) -> ChatSession:
    """取得既有 session 或建立新的。"""
    if session_id:
        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        session = (await db.execute(stmt)).scalar_one_or_none()
        if session:
            return session

    session = ChatSession(user_id=user_id)
    db.add(session)
    await db.flush()
    return session


async def list_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[ChatSession], int]:
    """取得使用者所有 session（分頁）。"""
    count_stmt = (
        select(func.count())
        .select_from(ChatSession)
        .where(ChatSession.user_id == user_id)
    )
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(desc(ChatSession.updated_at))
        .offset((page - 1) * limit)
        .limit(limit)
    )
    sessions = (await db.execute(stmt)).scalars().all()
    return list(sessions), total


async def get_session_messages(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
) -> ChatSession | None:
    """取得特定 session 及其所有訊息。"""
    stmt = (
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def delete_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
) -> bool:
    """刪除 session（cascade 刪除訊息）。"""
    stmt = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id,
    )
    session = (await db.execute(stmt)).scalar_one_or_none()
    if not session:
        return False
    await db.delete(session)
    await db.commit()
    return True
