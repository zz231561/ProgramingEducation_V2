"""Chat service — 管理對話 session 和 EDF 管線串接。"""

import uuid

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.chat import ChatSession, ChatMessage, MessageRole
from services.edf.evidence import analyze_evidence
from services.edf.decision import decide_strategy
from services.edf.feedback import generate_feedback


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


async def interact(
    db: AsyncSession,
    user_id: uuid.UUID,
    code: str,
    question: str,
    session_id: uuid.UUID | None = None,
    hint_level: int = 0,
    execution_result: dict | None = None,
) -> tuple[ChatSession, ChatMessage, ChatMessage]:
    """主要教學互動 — 串接 EDF 三層管線。

    回傳 (session, user_message, assistant_message)。
    """
    session = await get_or_create_session(db, user_id, session_id)

    # 取得對話歷史（供 Feedback 層使用）
    history_stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
    )
    history_rows = (await db.execute(history_stmt)).scalars().all()
    chat_history = [{"role": m.role.value, "content": m.content} for m in history_rows]

    # Evidence 層
    stdout = (execution_result or {}).get("stdout", "")
    stderr = (execution_result or {}).get("stderr", "")
    compile_output = (execution_result or {}).get("compile_output", "")

    evidence = await analyze_evidence(code, stdout, stderr, compile_output)

    # Decision 層
    strategy = decide_strategy(evidence, hint_level)

    # Feedback 層
    ai_response = await generate_feedback(
        evidence=evidence,
        strategy=strategy,
        student_message=question,
        chat_history=chat_history,
    )

    # 儲存 user message
    user_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER,
        content=question,
        code_snapshot=code,
        execution_result=execution_result,
    )
    db.add(user_msg)

    # 儲存 assistant message
    assistant_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=ai_response,
        evidence=evidence.model_dump(),
    )
    db.add(assistant_msg)

    # 更新 session title（首次訊息）
    if not history_rows:
        session.title = question[:50] if len(question) > 50 else question

    await db.commit()
    await db.refresh(session)

    return session, user_msg, assistant_msg


async def list_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[ChatSession], int]:
    """取得使用者所有 session（分頁）。"""
    count_stmt = select(ChatSession).where(ChatSession.user_id == user_id)
    total = len((await db.execute(count_stmt)).scalars().all())

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
