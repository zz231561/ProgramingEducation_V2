"""Chat service — EDF 三層管線的串接（session CRUD 見 `chat_sessions.py`）。"""

import logging
import uuid
from collections.abc import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.chat import ChatMessage, ChatSession, DialogueAct, MessageRole
from models.reflection import Reflection
from services.analytics import classify_dialogue_act
from services.chat_sessions import get_or_create_session
from services.chat_signals import (
    TurnSignal,
    compute_need,
    format_previous_exchange,
    is_repeat_evidence,
    stabilize_error_type,
    turns_from_history,
)
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
    explicit_help: bool = False,
    debug_sink: dict | None = None,
    strategy_sink: dict | None = None,
    on_stage: StageCallback | None = None,
) -> tuple[ChatSession, ChatMessage, ChatMessage]:
    """主要教學互動 — 串接 EDF 三層管線。

    `reflection_id`（Phase 2-5e）：若提供，載入學生反思並注入 Evidence + Feedback 兩層 prompt；
    無或載入失敗都不擋流程（容錯，與 mastery / RAG 同款）。
    `debug_sink`（DEV-7）：dev 帳號的中間層觀測 dict——收集 evidence / strategy /
    kgraph / RAG 命中，由 route 附在回應 debug 欄位；None（一般帳號）零開銷。
    `explicit_help`（7-C2a'）：學生按下「我卡住了」。這是前端**唯一**還能影響
    揭露等級的輸入，因為按鈕事件後端觀測不到——與被移除的 `hint_level` 不同，
    那是前端自行推算的階梯位置（可被寫死），這是使用者的實際動作。
    `strategy_sink`（7-C2a）：回填 `reveal_level` / `need` 供 route 記錄
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
    # 揭露階梯與證據去重共用的歷史訊號（7-C2a：只看學生做過什麼、判定紀錄怎麼寫）
    prior_turns = turns_from_history(history_rows)
    previous_exchange = format_previous_exchange(history_rows)

    # 對話行為分類（5-2c）— 啟發式，僅用 LLM 呼叫前既有訊號，隨 user message 一併持久化。
    # 按了「我卡住了」＝明確的 hint 請求，直接標記；否則走關鍵字啟發式（hint_level 傳 0，
    # 那個參數是 Quiz「按了 N 次提示鈕」的語意，chat 端沒有對應物）
    dialogue_act = (
        DialogueAct.ASKING_HINT.value
        if explicit_help
        else classify_dialogue_act(question, 0, execution_result)
    )

    # Fail-safe 持久化：user message 在 LLM 呼叫前先 commit。
    # OpenAI 偶發失敗是常態，不可讓學生打的問題隨 rollback 蒸發。
    user_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER,
        content=question,
        code_snapshot=code,
        execution_result=execution_result,
        dialogue_act=dialogue_act,
        explicit_help=explicit_help,
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
        previous_exchange=previous_exchange,
    )

    # B8：證據沒變就沿用上輪的 error_type，避免 base 漂移害學生看到揭露程度倒退
    evidence = stabilize_error_type(evidence, prior_turns, code, execution_result)

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

    # Decision 層（7-C2a'）— 揭露等級 = base(error_type) + need，全在後端算。
    # 本輪 evidence 剛出爐，接在歷史後面一起重放；單純追問／索答施壓 delta 為 0
    current_turn = TurnSignal(
        content=question,
        code_snapshot=code,
        execution_result=execution_result,
        created_at=user_msg.created_at,
        comprehension=evidence.comprehension_signal,
        continues_issue=evidence.continues_previous_issue,
        explicit_help=explicit_help,
        error_type=evidence.error_type.value,
    )
    need = compute_need([*prior_turns, current_turn])
    strategy = decide_strategy(evidence, need)
    if strategy_sink is not None:
        strategy_sink["reveal_level"] = strategy.reveal_level
        strategy_sink["need"] = need

    # DEV-7：dev 帳號收集中間層觀測（RAG 命中由 generate_feedback 補入）
    if debug_sink is not None:
        debug_sink.update({
            "evidence": evidence.model_dump(),
            "need": need,
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
