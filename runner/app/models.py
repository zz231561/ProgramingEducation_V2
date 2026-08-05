"""Request / Response schema。

RunResponse 的七個核心欄位**逐字對齊** backend `services/judge0.py::ExecutionResult`，
status_description 沿用 Judge0 命名慣例（"Accepted" / "Compilation Error" /
"Time Limit Exceeded" / "Runtime Error (...)"）——前端 `classifyStatus` 與
`run_help` 的字串比對因此零改動。
"""

from pydantic import BaseModel, Field

# Judge0 慣例狀態字串（前端 classifyStatus 依賴這些子字串，勿改寫法）
STATUS_ACCEPTED = "Accepted"
STATUS_COMPILE_ERROR = "Compilation Error"
STATUS_TIME_LIMIT = "Time Limit Exceeded"
STATUS_NZEC = "Runtime Error (NZEC)"  # 非零 exit code，Judge0 同名


class RunRequest(BaseModel):
    code: str = Field(min_length=1)
    stdin: str = ""
    # 以空白分隔的 argv（章節 58），對齊 Judge0 command_line_arguments 介面
    args: str = ""


class RunResponse(BaseModel):
    # —— 與 ExecutionResult 完全同名同型別 ——
    stdout: str = ""
    stderr: str = ""
    compile_output: str = ""
    exit_code: int | None = None
    time: str | None = None
    memory: int | None = None
    status_description: str = ""
    # —— runner 額外觀測欄位（backend 映射時忽略即可）——
    cache_hit: bool = False
    queued_ms: int = 0
