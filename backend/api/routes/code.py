"""程式碼執行 API — 提交至 Judge0 並回傳結果。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db, User
from core.rate_limit import rate_limit
from services.analytics import log_execution
from services.judge0 import submit_and_poll, ExecutionResult, CPP_LANGUAGE_ID

router = APIRouter(prefix="/code", tags=["code"])


class ExecuteRequest(BaseModel):
    """程式碼執行請求。"""

    code: str = Field(..., min_length=1, max_length=50_000)
    stdin: str = Field(default="", max_length=10_000)
    # 章節 58「main 函式的參數」：以空白分隔的 argv（不含程式名）
    args: str = Field(default="", max_length=500)


@router.post(
    "/execute",
    response_model=ExecutionResult,
    dependencies=[Depends(rate_limit("execute"))],
)
async def execute_code(
    body: ExecuteRequest,
    user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
) -> ExecutionResult:
    """提交程式碼至 Judge0 執行，回傳 stdout/stderr/compile_output。"""
    result = await submit_and_poll(
        source_code=body.code,
        stdin=body.stdin,
        # 語言固定 C++：本平台只教 C++，不讓前端指定 language_id
        language_id=CPP_LANGUAGE_ID,
        command_line_arguments=body.args,
    )
    # 行為事件記錄（best-effort，不擋回應）
    await log_execution(db, user_id=user.id, result=result, code=body.code)
    return result
