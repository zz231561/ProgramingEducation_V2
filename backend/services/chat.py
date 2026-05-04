"""Chat service — 管理對話 session 和 EDF 管線串接。"""

import uuid

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.chat import ChatSession, ChatMessage, MessageRole
from models.reflection import Reflection
from services.edf.evidence import analyze_evidence
from services.edf.decision import decide_strategy
from services.edf.feedback import generate_feedback
from services.edf.reflection_context import (
    format_reflection_for_evidence,
    format_reflection_for_feedback,
)
from services.mastery import update_mastery
from services.security.sanitizer import sanitize_input, wrap_student_input, wrap_student_code


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


async def _load_reflection_safely(
    db: AsyncSession,
    user_id: uuid.UUID,
    reflection_id: uuid.UUID | None,
) -> Reflection | None:
    """Best-effort 載入學生本人的反思；找不到 / 非本人擁有 / 異常 → None（不擋教學流程）。"""
    if reflection_id is None:
        return None
    try:
        row = (
            await db.execute(
                select(Reflection).where(Reflection.id == reflection_id)
            )
        ).scalar_one_or_none()
        if row is None or row.user_id != user_id:
            return None
        return row
    except Exception:
        return None


async def interact(
    db: AsyncSession,
    user_id: uuid.UUID,
    code: str,
    question: str,
    session_id: uuid.UUID | None = None,
    hint_level: int = 0,
    execution_result: dict | None = None,
    reflection_id: uuid.UUID | None = None,
) -> tuple[ChatSession, ChatMessage, ChatMessage]:
    """主要教學互動 — 串接 EDF 三層管線。

    `reflection_id`（Phase 2-5e）：若提供，載入學生反思並注入 Evidence + Feedback 兩層 prompt；
    無或載入失敗都不擋流程（容錯，與 mastery / RAG 同款）。

    回傳 (session, user_message, assistant_message)。
    """
    # 安全防護：Regex 偵測 + 清理
    question = sanitize_input(question)

    session = await get_or_create_session(db, user_id, session_id)

    # 取得對話歷史（供 Feedback 層使用）
    history_stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
    )
    history_rows = (await db.execute(history_stmt)).scalars().all()
    chat_history = [{"role": m.role.value, "content": m.content} for m in history_rows]

    # 反思（best-effort）— 在 Evidence 之前載入，兩層共用
    reflection = await _load_reflection_safely(db, user_id, reflection_id)
    reflection_evidence_summary = format_reflection_for_evidence(reflection)
    reflection_feedback_block = format_reflection_for_feedback(reflection)

    # Evidence 層
    stdout = (execution_result or {}).get("stdout", "")
    stderr = (execution_result or {}).get("stderr", "")
    compile_output = (execution_result or {}).get("compile_output", "")

    evidence = await analyze_evidence(
        code, stdout, stderr, compile_output, reflection_evidence_summary
    )

    # 精熟度更新（roadmap 2-3b）— 在 Feedback 之前跑，確保 BKT state 與此次互動同步
    # 容錯：mastery 失敗不阻擋教學回應（與 RAG 同款處理）
    try:
        await update_mastery(db, user_id, evidence)
    except Exception:
        pass

    # Decision 層
    strategy = decide_strategy(evidence, hint_level)

    # Feedback 層
    ai_response = await generate_feedback(
        evidence=evidence,
        strategy=strategy,
        student_message=question,
        chat_history=chat_history,
        reflection_block=reflection_feedback_block,
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
