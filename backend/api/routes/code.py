"""程式碼執行 API — 提交至 Judge0 並回傳結果。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.deps import get_current_db_user, User
from services.judge0 import submit_and_poll, ExecutionResult, CPP_LANGUAGE_ID

router = APIRouter(prefix="/code", tags=["code"])


class ExecuteRequest(BaseModel):
    """程式碼執行請求。"""

    code: str = Field(..., min_length=1, max_length=50_000)
    language_id: int = Field(default=CPP_LANGUAGE_ID)
    stdin: str = Field(default="", max_length=10_000)


@router.post("/execute", response_model=ExecutionResult)
async def execute_code(
    body: ExecuteRequest,
    _user: User = Depends(get_current_db_user),
) -> ExecutionResult:
    """提交程式碼至 Judge0 執行，回傳 stdout/stderr/compile_output。"""
    return await submit_and_poll(
        source_code=body.code,
        stdin=body.stdin,
        language_id=body.language_id,
    )
