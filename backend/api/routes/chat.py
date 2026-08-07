"""Chat API — 教學互動 + 對話歷史管理。"""

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import User, get_current_db_user, get_db
from api.routes.chat_sse import interact_event_stream
from core.dev_mode import is_dev_email
from core.rate_limit import rate_limit
from services.chat_kickoff import reflection_kickoff
from services.run_help import run_help

router = APIRouter(prefix="/chat", tags=["chat"])


# === Request / Response schemas ===

class InteractRequest(BaseModel):
    """教學互動請求。"""

    # code 允許空字串：學生剛開 Workspace 還沒打程式碼時，仍可向 AI 問「怎麼開始？」
    code: str = Field(default="", max_length=50_000)
    question: str = Field(..., min_length=1, max_length=2_000)
    session_id: uuid.UUID | None = Field(default=None)
    # 7-C2a：原有的 hint_level 已移除——揭露等級改由後端從對話歷史自算，
    # 前端送得出來的數字就可能被寫死成 0（7-C1 修的正是這個 bug）。
    # 7-C2a'：`explicit_help` 是例外且不牴觸——它不是前端推算的等級，
    # 而是「學生按了『我卡住了』」這個後端觀測不到的實際動作
    explicit_help: bool = Field(default=False)
    execution_result: dict | None = Field(default=None)
    # Phase 2-5e：若前端帶上當前 active reflection_id，後端會載入並注入 EDF prompt
    reflection_id: uuid.UUID | None = Field(default=None)


class MessageOut(BaseModel):
    """單則訊息回應。"""

    id: uuid.UUID
    role: str
    content: str
    code_snapshot: str | None = None
    evidence: dict | None = None
    # 教材出處（章節 / 時間 / 連結 / 原文摘錄），供前端讓學生核對
    citations: list[dict] | None = None
    created_at: str

    model_config = {"from_attributes": True}


class InteractResponse(BaseModel):
    """教學互動回應。"""

    session_id: uuid.UUID
    user_message: MessageOut
    assistant_message: MessageOut
    # DEV-7：dev 帳號附 EDF 中間層觀測（evidence/strategy/RAG/kgraph）；一般帳號 None
    debug: dict | None = None


class KickoffRequest(BaseModel):
    """反思開場請求（學生帶反思進 Workspace 時前端呼叫一次）。"""

    reflection_id: uuid.UUID


class KickoffResponse(BaseModel):
    """反思開場回應 — 新 session + Coddy 開場訊息。"""

    session_id: uuid.UUID
    session_title: str
    assistant_message: MessageOut


# === Endpoints ===

@router.post(
    "/reflection-kickoff",
    response_model=KickoffResponse,
    dependencies=[Depends(rate_limit("llm"))],
)
async def chat_reflection_kickoff(
    body: KickoffRequest,
    user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
) -> KickoffResponse:
    """Coddy 主動開場：閱讀題目 + 反思計畫，肯定亮點並接手引導。"""
    session, msg = await reflection_kickoff(db, user.id, body.reflection_id)
    return KickoffResponse(
        session_id=session.id,
        session_title=session.title or "",
        assistant_message=MessageOut(
            id=msg.id,
            role=msg.role.value,
            content=msg.content,
            code_snapshot=None,
            evidence=None,
            created_at=str(msg.created_at),
        ),
    )


class RunHelpRequest(BaseModel):
    """執行出現問題時請 Coddy 主動說明。"""

    code: str = Field(default="", max_length=50_000)
    # 逾時 / 時區的情況沒有編譯訊息，改由 status_description 與 kind 判定
    compile_output: str = Field(default="", max_length=10_000)
    status_description: str = Field(default="", max_length=200)
    # 前端機械判定出的類型（"timezone" / "nzec"）；空＝依編譯訊息判斷
    kind: str = Field(default="", max_length=20)
    session_id: uuid.UUID | None = Field(default=None)


class RunHelpResponse(BaseModel):
    session_id: uuid.UUID
    session_title: str
    # True = 機械判定（平台限制 / 逾時 / 時區），固定文案未呼叫 LLM
    is_mechanical: bool
    assistant_message: MessageOut


@router.post(
    "/run-help",
    response_model=RunHelpResponse,
    dependencies=[Depends(rate_limit("llm"))],
)
async def chat_run_help(
    body: RunHelpRequest,
    user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
) -> RunHelpResponse:
    """執行出問題時 Coddy 主動發話：環境限制直說，學生自己的錯誤走引導。"""
    session, msg, mechanical = await run_help(
        db,
        user.id,
        body.session_id,
        body.code,
        body.compile_output,
        body.status_description,
        body.kind,
    )
    return RunHelpResponse(
        session_id=session.id,
        session_title=session.title or "",
        is_mechanical=mechanical,
        assistant_message=MessageOut(
            id=msg.id,
            role=msg.role.value,
            content=msg.content,
            code_snapshot=None,
            evidence=None,
            created_at=str(msg.created_at),
        ),
    )


@router.post("/interact", dependencies=[Depends(rate_limit("llm"))])
async def chat_interact(
    body: InteractRequest,
    user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """主要教學互動 — 串接 EDF Pipeline，以 SSE 推播階段進度（7-U6）。

    事件：`stage`（analyzing / retrieving / composing）→ `done`（InteractResponse）。
    管線途中失敗時 header 已送出，無法改 HTTP status，故改發 `error` 事件；
    rate limit 等前置檢查仍在串流開始前，維持正常的 429 / 401 回應。
    """
    # DEV-7：dev 帳號才建 sink（後端判定，非前端宣稱）
    debug_sink: dict | None = {} if is_dev_email(user.email) else None

    def build_payload(session, user_msg, ai_msg) -> dict:
        return InteractResponse(
            debug=debug_sink,
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
                citations=ai_msg.citations,
                created_at=str(ai_msg.created_at),
            ),
        ).model_dump(mode="json")

    return StreamingResponse(
        interact_event_stream(
            db=db,
            user=user,
            body=body,
            debug_sink=debug_sink,
            build_payload=build_payload,
        ),
        media_type="text/event-stream",
        # 反向代理（Zeabur 邊緣）不得緩衝，否則階段事件會被壓到最後一起送達
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
