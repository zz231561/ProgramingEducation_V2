"""出題 Generate 階段 — LLM 出題 + RAG 教材注入（roadmap 2-4c）。

設計：
- 餵入單一 concept + type + difficulty + bloom，加上 RAG 抓回的相關教材片段
- 用 OpenAI `json_object` mode，prompt 明訂三種 type 的 JSON 形狀
- 收到 JSON 後依 type 用 Pydantic 模型驗證，shape 不對 → 502
- 寫入 `questions` 表 `validated=False`，等 2-4d Validate 階段過審才標 True
"""

import json
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.errors import AppError
from models.concept import Concept
from models.quiz import Question, QuestionSource, QuestionType
from services.rag import retrieve_chunks

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise AppError(503, "LLM_UNAVAILABLE", "OpenAI API Key 未設定")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


# === 三種 type 的 content shape 驗證模型 ===


class _MCContent(BaseModel):
    """multiple_choice 題目 content。"""

    stem: str = Field(min_length=5)
    options: list[str] = Field(min_length=2, max_length=6)
    answer_index: int = Field(ge=0)

    @field_validator("answer_index")
    @classmethod
    def _answer_in_range(cls, v: int, info: Any) -> int:
        opts = info.data.get("options") or []
        if v >= len(opts):
            raise ValueError("answer_index 超過 options 長度")
        return v


class _FillContent(BaseModel):
    """fill_blank 題目 content（stem 用 `___` 表示空格）。"""

    stem: str = Field(min_length=5)
    answers: list[str] = Field(min_length=1)


class _CodingContent(BaseModel):
    """coding 題目 content。"""

    stem: str = Field(min_length=5)
    starter_code: str = ""
    expected_output: str | None = None


_CONTENT_MODEL_BY_TYPE = {
    QuestionType.MULTIPLE_CHOICE: _MCContent,
    QuestionType.FILL_BLANK: _FillContent,
    QuestionType.CODING: _CodingContent,
}


# === Prompt 組裝 ===


def _build_system_prompt(
    concept: Concept,
    question_type: QuestionType,
    difficulty: int,
    bloom_level: int,
) -> str:
    schema_hint = {
        QuestionType.MULTIPLE_CHOICE: (
            '{"stem": "題幹", "options": ["A...", "B...", ...], '
            '"answer_index": 正解 index (0-based), "explanation": "為何正解"}'
        ),
        QuestionType.FILL_BLANK: (
            '{"stem": "題幹（用 ___ 標示空格）", "answers": ["...", ...], '
            '"explanation": "為何此填法正確"}'
        ),
        QuestionType.CODING: (
            '{"stem": "題目敘述", "starter_code": "起始程式碼（可空）", '
            '"expected_output": "預期 stdout 或 null", "explanation": "解題思路"}'
        ),
    }[question_type]

    return f"""\
你是 C++ 程式教學題目生成助手。為以下概念生成**一題**測驗題。

目標概念：
- tag: {concept.tag}
- 名稱：{concept.name_zh} / {concept.name_en}
- 分類：{concept.category}
- 描述：{concept.description}

題目參數：
- 題型：{question_type.value}
- 難度：{difficulty}/5（1=最簡單，5=最進階）
- Bloom 認知層級：{bloom_level} (1=記憶, 2=理解, 3=應用, 4=分析, 5=評估, 6=創造)

回傳**嚴格 JSON**，欄位 schema：
{schema_hint}

撰寫規則：
- 全部用繁體中文，C++ 技術名詞保留英文
- 題幹具體、可單獨閱讀無需額外脈絡
- 難度與 Bloom 必須匹配（高難度配高 Bloom）
- 不可洩漏完整解答程式碼（coding 題的 starter_code 限骨架 + TODO）
- 選擇題：每個選項 < 30 字、誘答合理（不可有明顯錯選項）
- explanation 解釋為何正解（2-3 句）
"""


def _build_user_prompt(rag_chunks: list[Any]) -> str:
    if not rag_chunks:
        return "請依目標概念與題目參數出題。"
    parts = ["以下教材片段可供參考（請以教材內容為依據出題，避免自編未驗證的細節）：\n"]
    for i, chunk in enumerate(rag_chunks, 1):
        parts.append(f"[{i}] {chunk.text.strip()}")
    return "\n\n".join(parts)


# === RAG 取材（容錯）===


async def _fetch_rag_chunks_for_concept(concept: Concept, top_k: int = 3) -> list[Any]:
    try:
        return await retrieve_chunks(
            f"{concept.name_zh} {concept.tag}：{concept.description}",
            top_k=top_k,
        )
    except Exception:
        # RAG 失敗不阻擋出題，沒教材就靠 LLM 內建知識
        return []


# === 主函式 ===


async def generate_question(
    db: AsyncSession,
    concept: Concept,
    question_type: QuestionType,
    difficulty: int,
    bloom_level: int,
) -> Question:
    """為單一 concept 生成題目並寫入 DB（caller commit）。

    Args:
        db: SQLAlchemy async session（caller 負責 commit）
        concept: 目標概念
        question_type: multiple_choice / fill_blank / coding
        difficulty: 1-5
        bloom_level: 1-6

    Returns:
        新建的 Question 物件（已 db.add，未 commit；validated=False）
    """
    client = _get_client()
    rag_chunks = await _fetch_rag_chunks_for_concept(concept)

    system_prompt = _build_system_prompt(concept, question_type, difficulty, bloom_level)
    user_prompt = _build_user_prompt(rag_chunks)

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=900,
        )
    except Exception as e:
        raise AppError(502, "LLM_ERROR", f"AI 服務暫時不可用：{e}") from e

    raw = response.choices[0].message.content or "{}"

    try:
        data: dict = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AppError(502, "LLM_PARSE_ERROR", "AI 回傳格式異常") from e

    explanation = str(data.pop("explanation", "")).strip()
    content_model_cls = _CONTENT_MODEL_BY_TYPE[question_type]
    try:
        content_obj = content_model_cls(**data)
    except ValidationError as e:
        raise AppError(
            502,
            "LLM_VALIDATION_ERROR",
            f"AI 回傳內容不符 {question_type.value} schema：{e.errors()[0]['msg']}",
        ) from e

    question = Question(
        type=question_type.value,
        concept_tags=[concept.tag],
        bloom_level=bloom_level,
        difficulty=difficulty,
        content=content_obj.model_dump(),
        explanation=explanation,
        source=QuestionSource.GENERATED.value,
        validated=False,
    )
    db.add(question)
    return question
