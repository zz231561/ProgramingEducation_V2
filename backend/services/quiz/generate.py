"""出題 Generate 階段 — LLM 出題 + RAG 教材注入（roadmap 2-4c / 6-3a）。

設計：餵 concept + type + difficulty + bloom + RAG chunks → LLM JSON mode
→ Pydantic 驗 shape（不符 → 502）→ 寫 questions（validated=False，等 2-4d 過審）。

Phase 6-3a grounded mode：`video_order` 提供時改走 `get_chunks_by_video_order`
取整支影片字幕（避免跨 video 污染，與 6-2b 同策略），且 prompt 加 grounding 規則：
情境須與字幕範例 / 變數命名一致。`video_order=None` 走原語意 retrieve_chunks。
"""

import json
import logging
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.errors import AppError
from models.concept import Concept
from models.quiz import Question, QuestionSource, QuestionType
from services.rag import retrieve_chunks
from services.rag.retrieve import get_chunks_by_video_order

logger = logging.getLogger(__name__)

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
    # stem 用 `___` 標示空格
    stem: str = Field(min_length=5)
    answers: list[str] = Field(min_length=1)


class _CodingContent(BaseModel):
    stem: str = Field(min_length=5)
    starter_code: str = ""
    expected_output: str | None = None


_CONTENT_MODEL_BY_TYPE = {
    QuestionType.MULTIPLE_CHOICE: _MCContent,
    QuestionType.FILL_BLANK: _FillContent,
    QuestionType.CODING: _CodingContent,
}


# === Prompt 組裝 ===


_GROUNDING_RULES = """\

【Grounding 規則 - 不可違反】（本題以教授實際 YouTube 教學影片字幕為依據）
1. 題目情境（變數名稱、輸入輸出、舉例 scenario）必須與 TRANSCRIPT 出現的範例 / 命名一致
2. 嚴禁發明字幕未提到的程式碼；coding 題 starter_code 須沿用字幕示範的識別字
3. 若字幕資訊不足 → 仍須出題，但降難度回到 transcript 明確涵蓋的概念
"""


def _build_system_prompt(
    concept: Concept,
    question_type: QuestionType,
    difficulty: int,
    bloom_level: int,
    grounded: bool = False,
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

    grounding_block = _GROUNDING_RULES if grounded else ""

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
{grounding_block}"""


def _build_user_prompt(rag_chunks: list[Any], grounded: bool = False) -> str:
    if not rag_chunks:
        return "請依目標概念與題目參數出題。"
    if grounded:
        header = (
            "以下 TRANSCRIPT 為教授實際 YouTube 影片字幕（依時間順序），"
            "請以這些字幕為唯一依據出題：\n"
        )
    else:
        header = (
            "以下教材片段可供參考（請以教材內容為依據出題，避免自編未驗證的細節）：\n"
        )
    parts = [header]
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
    except Exception as e:
        # RAG 失敗不阻擋出題，沒教材就靠 LLM 內建知識
        logger.warning("RAG retrieval failed for quiz generate (non-blocking): %r", e)
        return []


async def _fetch_grounded_chunks_for_video(video_order: int) -> list[Any]:
    # 6-3a：取 video 完整字幕（時間順序）；失敗回 [] 不阻擋出題（同 _fetch_rag_chunks_for_concept）
    try:
        return await get_chunks_by_video_order(video_order)
    except Exception as e:
        logger.warning(
            "Grounded chunks fetch failed for video %s (non-blocking): %r",
            video_order,
            e,
        )
        return []


# === 主函式 ===


async def generate_question(
    db: AsyncSession,
    concept: Concept,
    question_type: QuestionType,
    difficulty: int,
    bloom_level: int,
    video_order: int | None = None,
) -> Question:
    """為單一 concept 生成題目並寫入 DB（caller commit）。

    `video_order` 提供時走 6-3a grounded mode（影片字幕 + grounding prompt 規則）；
    None 時走原 semantic RAG（學生現生題 backward compat）。
    回傳已 db.add、未 commit、validated=False 的 Question。
    """
    client = _get_client()
    grounded = video_order is not None
    if grounded:
        rag_chunks = await _fetch_grounded_chunks_for_video(video_order)
    else:
        rag_chunks = await _fetch_rag_chunks_for_concept(concept)

    system_prompt = _build_system_prompt(
        concept, question_type, difficulty, bloom_level, grounded=grounded
    )
    user_prompt = _build_user_prompt(rag_chunks, grounded=grounded)

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model_generate,
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
