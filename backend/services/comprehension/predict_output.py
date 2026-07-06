"""Predict-Output 驗證 — LLM 生成新測資 + 兩階段比對學生預測（roadmap 2-6c）。

設計（理論基礎見 references.md：Mental simulation / Trace prediction）：
- Generate：LLM 看 (題目 + 學生程式碼) → 出新 input + expected（針對學生實際程式而非題目正解）
- Grade 兩階段：
  1. normalize 後嚴格字串比對（trim + 折疊內部空白）
  2. 不通過 → LLM 判斷「語意一致」（允許格式差異如逗號 vs 空白）
  3. LLM 失敗 → fallback 用 Stage 1 結果
- match_method：'exact' / 'semantic' / 'mismatch' — 回前端供 debug / 顯示

LLM 失敗策略：
- generate 失敗 → 回 None（caller raise 503）
- grade LLM 失敗 → 退回嚴格比對結果（不擋學生流程）
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

from core.config import settings
from models.quiz import Question
from services.comprehension.predict_output_prompts import (
    build_generate_prompt,
    build_semantic_grade_prompt,
)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    """無 API key 直接回 None；caller fallback。"""
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            return None
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


@dataclass(frozen=True)
class PredictGenerationResult:
    """LLM 生成的新測資。任一 None 代表生成失敗（caller raise 503）。"""

    test_input: str | None
    expected_output: str | None


@dataclass(frozen=True)
class PredictGradeResult:
    """學生預測比對結果。`passed=False` 也可能是 LLM 評分失敗的 fallback。"""

    passed: bool
    expected_output: str  # 評分後告訴學生正確輸出（即使通過也回，方便對照）
    match_method: Literal["exact", "semantic", "mismatch"]
    feedback: str | None  # semantic 階段才有；exact pass / mismatch 為 None


class _GenerateResponse(BaseModel):
    test_input: str = Field(alias="input", min_length=0, max_length=2000)
    expected_output: str = Field(alias="expected", min_length=0, max_length=2000)


class _SemanticResponse(BaseModel):
    semantically_equal: bool
    feedback: str = Field(default="", max_length=300)


_WHITESPACE_RUN = re.compile(r"\s+")


def normalize_output(text: str) -> str:
    """正規化輸出字串供嚴格比對：
    - 全文 strip
    - 每行 strip
    - 折疊每行內部連續空白為單一空格
    - 多行用單一 \\n 連接（去除空行）

    意圖：吸收瑣碎格式差異（行尾空格、tab vs space），保留實質內容。
    """
    lines = [
        _WHITESPACE_RUN.sub(" ", line).strip() for line in text.strip().splitlines()
    ]
    return "\n".join(line for line in lines if line)


async def generate_predict_test(
    question: Question, student_code: str
) -> PredictGenerationResult:
    """LLM 生成新測資 + 對應預期輸出。失敗回 (None, None)。"""
    client = _get_client()
    if client is None:
        return PredictGenerationResult(test_input=None, expected_output=None)

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model_generate,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": build_generate_prompt(question, student_code)},
                {"role": "user", "content": "請出測資並回傳 JSON。"},
            ],
            temperature=0.4,
            max_tokens=400,
        )
    except Exception:
        return PredictGenerationResult(test_input=None, expected_output=None)

    raw = response.choices[0].message.content or "{}"
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        return PredictGenerationResult(test_input=None, expected_output=None)

    try:
        parsed = _GenerateResponse(**data)
    except ValidationError:
        return PredictGenerationResult(test_input=None, expected_output=None)

    return PredictGenerationResult(
        test_input=parsed.test_input,
        expected_output=parsed.expected_output,
    )


async def _semantic_match(
    student_code: str,
    test_input: str,
    expected_output: str,
    student_predicted: str,
) -> tuple[bool | None, str | None]:
    """LLM 判斷語意一致。回 (bool, feedback) 或 (None, None) 代表 LLM 失敗。"""
    client = _get_client()
    if client is None:
        return None, None

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": build_semantic_grade_prompt(
                        student_code, test_input, expected_output, student_predicted
                    ),
                },
                {"role": "user", "content": "請判斷並回傳 JSON。"},
            ],
            temperature=0.1,
            max_tokens=200,
        )
    except Exception:
        return None, None

    raw = response.choices[0].message.content or "{}"
    try:
        data: dict[str, Any] = json.loads(raw)
        parsed = _SemanticResponse(**data)
    except (json.JSONDecodeError, ValidationError):
        return None, None
    return parsed.semantically_equal, (parsed.feedback or None)


async def grade_predict_answer(
    student_code: str,
    test_input: str,
    expected_output: str,
    student_predicted: str,
) -> PredictGradeResult:
    """兩階段比對學生預測：嚴格 normalize → LLM 語意 fallback。"""
    if normalize_output(student_predicted) == normalize_output(expected_output):
        return PredictGradeResult(
            passed=True,
            expected_output=expected_output,
            match_method="exact",
            feedback=None,
        )

    semantic_pass, feedback = await _semantic_match(
        student_code, test_input, expected_output, student_predicted
    )
    if semantic_pass is True:
        return PredictGradeResult(
            passed=True,
            expected_output=expected_output,
            match_method="semantic",
            feedback=feedback,
        )

    return PredictGradeResult(
        passed=False,
        expected_output=expected_output,
        match_method="mismatch",
        feedback=feedback,  # LLM 不通過時也帶回提示，可能為 None（fallback）
    )
