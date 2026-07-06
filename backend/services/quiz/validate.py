"""出題 Validate 階段 — LLM 自我檢查題目品質（roadmap 2-4d）。

設計：
- 對 generate 出來的題目跑第二次 LLM call，檢查三個面向：
  A. 答案正確性（answer 是否真的對）
  B. 概念符合（題目是否真的測到 concept_tags 列出的概念）
  C. Bloom 等級適當（題目要求的認知層級是否 <= 目標 bloom）
- 三項全 pass → 直接 set `question.validated=True`（caller commit）
- 任一 fail → 不動 validated，回 `ValidationReport(passed=False, issues=[...])`
  caller（2-4e API）決定 retry / 丟棄 / 升降難度
- 與 generate 同一 transaction：caller 已 db.add(question) 但未 commit，
  本層在同 session 上 set validated 後由 caller 一起 commit
"""

import json
from dataclasses import dataclass, field
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.errors import AppError
from models.quiz import Question

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise AppError(503, "LLM_UNAVAILABLE", "OpenAI API Key 未設定")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


# === LLM 回應 schema 驗證 ===


class _ValidatorResponse(BaseModel):
    answer_correct: bool
    answer_reason: str = Field(default="")
    concept_fits: bool
    concept_reason: str = Field(default="")
    bloom_appropriate: bool
    bloom_reason: str = Field(default="")


# === 對外回傳結構 ===


@dataclass(frozen=True)
class ValidationReport:
    """三面向審查結果。`passed` 為三個 bool 的 AND。"""

    passed: bool
    answer_correct: bool
    concept_fits: bool
    bloom_appropriate: bool
    issues: list[str] = field(default_factory=list)


# === Prompt ===


def _build_prompt(question: Question) -> str:
    return f"""\
你是 C++ 教學題目品質審查員。審查以下題目的三個面向，並給出 JSON 結構化結果。

題目資料：
- 題型 (type)：{question.type}
- 涉及概念 (intended_concept_tags)：{question.concept_tags}
- 目標 Bloom 等級：{question.bloom_level} (1=記憶, 2=理解, 3=應用, 4=分析, 5=評估, 6=創造)
- 難度：{question.difficulty}/5
- 題目內容 (content JSON)：
{json.dumps(question.content, ensure_ascii=False, indent=2)}
- 解釋 (explanation)：{question.explanation}

請審查：
A. **答案正確性 (answer_correct)**：題目所宣稱的答案在 C++ 語法 / 邏輯上是否真的正確？
   多選題檢查 answer_index 對應的 option；填空題檢查 answers；coding 題檢查 stem 描述與 starter_code 是否一致、explanation 描述的解法是否真能達到目標。
B. **概念符合 (concept_fits)**：題目實際測試的概念是否吻合 intended_concept_tags？
   舉例：如果 tag 是 pointer-arithmetic 但題目其實只在考 std::cout 用法 → false。
C. **Bloom 等級適當 (bloom_appropriate)**：題目實際要求的認知層級是否 **不超出** 目標 Bloom？
   超過（例如目標 APPLY=3 但題目要求 EVALUATE=5）→ false；剛好或低於目標 → true。

回傳嚴格 JSON：
{{
  "answer_correct": true/false,
  "answer_reason": "（一句話說明判斷依據）",
  "concept_fits": true/false,
  "concept_reason": "...",
  "bloom_appropriate": true/false,
  "bloom_reason": "..."
}}
"""


# === 主函式 ===


async def validate_question(
    db: AsyncSession,  # noqa: ARG001 — 預留供未來查相關資料；當前只用來呼叫 caller commit
    question: Question,
) -> ValidationReport:
    """LLM 自審題目；通過則 set `validated=True`。

    Args:
        db: 共用同一 transaction（service 不 commit；由 caller 統一 commit）
        question: 已 db.add 但 validated=False 的 Question 物件

    Returns:
        ValidationReport — passed 為三個面向 AND 的結果；
        失敗時 issues 列出未通過的 reason。
    """
    client = _get_client()

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model_validate,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _build_prompt(question)},
                {"role": "user", "content": "請審查並回傳 JSON。"},
            ],
            temperature=0.2,
            max_tokens=500,
        )
    except Exception as e:
        raise AppError(502, "LLM_ERROR", f"AI 服務暫時不可用：{e}") from e

    raw = response.choices[0].message.content or "{}"
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AppError(502, "LLM_PARSE_ERROR", "AI 審查回傳格式異常") from e

    try:
        parsed = _ValidatorResponse(**data)
    except ValidationError as e:
        raise AppError(
            502,
            "LLM_VALIDATION_ERROR",
            f"AI 審查回傳缺欄位：{e.errors()[0]['msg']}",
        ) from e

    issues: list[str] = []
    if not parsed.answer_correct:
        issues.append(f"答案不正確：{parsed.answer_reason}")
    if not parsed.concept_fits:
        issues.append(f"概念不符：{parsed.concept_reason}")
    if not parsed.bloom_appropriate:
        issues.append(f"Bloom 等級不適當：{parsed.bloom_reason}")

    passed = parsed.answer_correct and parsed.concept_fits and parsed.bloom_appropriate
    if passed:
        question.validated = True

    return ValidationReport(
        passed=passed,
        answer_correct=parsed.answer_correct,
        concept_fits=parsed.concept_fits,
        bloom_appropriate=parsed.bloom_appropriate,
        issues=issues,
    )
