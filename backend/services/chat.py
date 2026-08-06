"""Chat service — 管理對話 session 和 EDF 管線串接。"""

import logging
import uuid
from collections.abc import Awaitable, Callable

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.chat import ChatSession, ChatMessage, DialogueAct, MessageRole
from models.reflection import Reflection
from services.analytics import classify_dialogue_act
from services.chat_signals import TurnSignal, compute_persistence, is_repeat_evidence
from services.edf.evidence import analyze_evidence
from services.edf.decision import decide_strategy
from services.edf.feedback import generate_feedback
from services.edf.kgraph_context import fetch_kgraph_block_safe
from services.edf.reflection_context import (
    format_reflection_for_evidence,
    format_reflection_for_feedback,
)
from services.mastery import BKT_CHAT_PARAMS, update_mastery
from services.security.sanitizer import sanitize_input, wrap_student_input, wrap_student_code

# EDF 管線階段（7-U6）——值同時是 SSE 事件內容與前端文案的 key，改名需同步前端
STAGE_ANALYZING = "analyzing"   # Evidence 層：分析程式碼與提問
STAGE_RETRIEVING = "retrieving"  # 讀 K-Graph 狀態 + Feedback 層檢索教材
STAGE_COMPOSING = "composing"    # Feedback 層：組織回答

StageCallback = Callable[[str], Awaitable[None]]

logger = logging.getLogger(__name__)


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
    execution_result: dict | None = None,
    reflection_id: uuid.UUID | None = None,
    debug_sink: dict | None = None,
    strategy_sink: dict | None = None,
    on_stage: StageCallback | None = None,
) -> tuple[ChatSession, ChatMessage, ChatMessage]:
    """主要教學互動 — 串接 EDF 三層管線。

    `reflection_id`（Phase 2-5e）：若提供，載入學生反思並注入 Evidence + Feedback 兩層 prompt；
    無或載入失敗都不擋流程（容錯，與 mastery / RAG 同款）。
    `debug_sink`（DEV-7）：dev 帳號的中間層觀測 dict——收集 evidence / strategy /
    kgraph / RAG 命中，由 route 附在回應 debug 欄位；None（一般帳號）零開銷。
    `strategy_sink`（7-C2a）：回填 `reveal_level` / `persistence` 供 route 記錄
    hint_request 事件——兩者改由後端自算後，route 已無從得知學生被升到第幾級。
    `on_stage`（7-U6）：每進入一個管線階段就回報，供 SSE 推播進度給前端；
    None 時完全不呼叫（非串流呼叫端零開銷）。

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
    # 揭露階梯與證據去重共用的歷史訊號（7-C2a：只看學生自己說過什麼、跑出什麼）
    prior_turns = [
        TurnSignal(m.content, m.code_snapshot, m.execution_result)
        for m in history_rows
        if m.role == MessageRole.USER
    ]

    # 對話行為分類（5-2c）— 啟發式，僅用 LLM 呼叫前既有訊號，隨 user message 一併持久化。
    # hint_level 傳 0：chat 沒有「學生按提示鈕」這種明確訊號（那是 Quiz 的語意），
    # 照傳堅持度會把一般追問全誤標成 asking_hint
    dialogue_act = classify_dialogue_act(question, 0, execution_result)

    # Fail-safe 持久化：user message 在 LLM 呼叫前先 commit。
    # OpenAI 偶發失敗是常態，不可讓學生打的問題隨 rollback 蒸發。
    user_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER,
        content=question,
        code_snapshot=code,
        execution_result=execution_result,
        dialogue_act=dialogue_act,
    )
    db.add(user_msg)
    if not history_rows:
        session.title = question[:50] if len(question) > 50 else question
    await db.commit()

    # 反思（best-effort）— 在 Evidence 之前載入，兩層共用
    reflection = await _load_reflection_safely(db, user_id, reflection_id)
    reflection_evidence_summary = format_reflection_for_evidence(reflection)
    reflection_feedback_block = format_reflection_for_feedback(reflection)

    # Evidence 層 — exit_code / status_description 必須帶上：
    # NZEC（如 return 1）stderr 全空，少了這兩欄管線會誤稱「執行成功」
    stdout = (execution_result or {}).get("stdout", "")
    stderr = (execution_result or {}).get("stderr", "")
    compile_output = (execution_result or {}).get("compile_output", "")
    exit_code = (execution_result or {}).get("exit_code")
    status_description = (execution_result or {}).get("status_description") or ""

    if on_stage:
        await on_stage(STAGE_ANALYZING)
    evidence = await analyze_evidence(
        code, stdout, stderr, compile_output, reflection_evidence_summary, question,
        exit_code=exit_code if isinstance(exit_code, int) else None,
        status_description=status_description,
    )

    # 離題判定覆寫 dialogue_act（5-2c）——LLM 判定優先於關鍵字啟發式：
    # 「幫我決定晚餐」會先被「幫我」誤標 asking_hint，僅在 None 時回填會漏統計
    if not evidence.is_on_topic:
        user_msg.dialogue_act = DialogueAct.OFF_TOPIC.value

    # K-Graph state（K4a）— 在 mastery 更新「之前」讀取：鷹架標榜「依過往練習
    # 紀錄」，若先更新再讀，本輪 evidence 的 tag 雜訊會當場污染鷹架分級
    # （實測：熟練度 0.9 的學生因當輪誤標 io-streams 而拿到新手鷹架）
    if on_stage:
        await on_stage(STAGE_RETRIEVING)
    kgraph_block = await fetch_kgraph_block_safe(db, user_id, evidence)

    # 精熟度更新（roadmap 2-3b / K6a chat 弱證據參數）
    # 容錯：mastery 失敗不阻擋教學回應（與 RAG 同款處理）
    # 兩種情況跳過：① 無程式碼＝純提問，沒有能力佐證（導覽性問題曾從 0 直寫 0.46）
    # ② 與上一則訊息完全相同的 code+執行結果＝同一證據，不重複計分
    # （連續追問同一次執行曾把 confidence 從 0.22 連砍到 0.12）
    if not code.strip():
        logger.info("mastery skip: no code artifact (question-only turn)")
    elif is_repeat_evidence(prior_turns, code, execution_result):
        logger.info("mastery skip: identical code+execution as previous turn")
    else:
        try:
            await update_mastery(db, user_id, evidence, params=BKT_CHAT_PARAMS)
        except Exception as e:
            logger.warning("update_mastery failed (non-blocking): %r", e)

    # Decision 層（7-C2a）— 揭露等級 = base(error_type) + 學生堅持度，全在後端算
    persistence = compute_persistence(prior_turns, question, execution_result)
    strategy = decide_strategy(evidence, persistence)
    if strategy_sink is not None:
        strategy_sink["reveal_level"] = strategy.reveal_level
        strategy_sink["persistence"] = persistence

    # DEV-7：dev 帳號收集中間層觀測（RAG 命中由 generate_feedback 補入）
    if debug_sink is not None:
        debug_sink.update({
            "evidence": evidence.model_dump(),
            "persistence": persistence,
            "strategy": strategy.model_dump(),
            "kgraph_block": kgraph_block,
            "reflection_injected": bool(reflection_feedback_block),
        })

    # Feedback 層（citations_sink 收本次引用的教材出處，供學生核對）
    if on_stage:
        await on_stage(STAGE_COMPOSING)
    citations: list[dict] = []
    ai_response = await generate_feedback(
        evidence=evidence,
        strategy=strategy,
        student_message=question,
        chat_history=chat_history,
        reflection_block=reflection_feedback_block,
        kgraph_block=kgraph_block,
        debug_sink=debug_sink,
        citations_sink=citations,
    )

    # 儲存 assistant message（user message 已於 LLM 呼叫前 commit）
    assistant_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=ai_response,
        evidence=evidence.model_dump(),
        citations=citations or None,
    )
    db.add(assistant_msg)

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
