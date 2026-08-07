"""出題 Generate 階段 — LLM 出題 + RAG 教材注入。

設計：餵 concept + type + difficulty + bloom + RAG chunks → LLM JSON mode
→ Pydantic 驗 shape（不符 → 502）→ 寫 questions（validated=False，等 2-4d 過審）。

Grounded mode：`video_order` 提供時改走 `get_chunks_by_video_order`
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
from core.llm_params import chat_model_kwargs
from models.concept import Concept
from models.quiz import Question, QuestionSource, QuestionType
from services.quiz.generate_prompts import build_system_prompt, build_user_prompt
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

    @field_validator("starter_code")
    @classmethod
    def _normalize_escaped_newlines(cls, value: str) -> str:
        """修正 LLM 將整份多行程式重複 JSON escape 的情況。"""
        if "\n" not in value and "\\n" in value and "#include" in value:
            return value.replace("\\n", "\n")
        return value


_CONTENT_MODEL_BY_TYPE = {
    QuestionType.MULTIPLE_CHOICE: _MCContent,
    QuestionType.FILL_BLANK: _FillContent,
    QuestionType.CODING: _CodingContent,
}




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




async def generate_question(
    db: AsyncSession,
    concept: Concept,
    question_type: QuestionType,
    difficulty: int,
    bloom_level: int,
    video_order: int | None = None,
    knowledge_point: str | None = None,
    source: QuestionSource = QuestionSource.GENERATED,
    model: str | None = None,
    extra_concepts: list[Concept] | None = None,
) -> Question:
    """為單一 concept 生成題目並寫入 DB（caller commit）。

    `video_order` 提供時走 6-3a grounded mode（影片字幕 + grounding prompt 規則）；
    None 時走原 semantic RAG（學生現生題 backward compat）。
    `knowledge_point`（6-3c）提供時題目聚焦該知識點，並記錄於 content 供覆蓋追溯。
    `model`（6-3c coding 強模型）提供時覆蓋生成模型；None → 預設生成組模型。
    `extra_concepts`（6-3d 綜合題）提供時題目綜合測驗目標 + 相關概念；
    concept_tags 記錄全部概念（去重保序）。
    回傳已 db.add、未 commit、validated=False 的 Question。
    """
    client = _get_client()
    grounded = video_order is not None
    if grounded:
        rag_chunks = await _fetch_grounded_chunks_for_video(video_order)
    else:
        rag_chunks = await _fetch_rag_chunks_for_concept(concept)

    system_prompt = build_system_prompt(
        concept,
        question_type,
        difficulty,
        bloom_level,
        grounded=grounded,
        knowledge_point=knowledge_point,
        extra_concepts=extra_concepts,
    )
    user_prompt = build_user_prompt(rag_chunks, grounded=grounded)

    try:
        response = await client.chat.completions.create(
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **chat_model_kwargs(
                model=model or settings.llm_model_generate,
                temperature=0.7,
                max_tokens=900,
            ),
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

    content = content_obj.model_dump()
    if knowledge_point:
        # 6-3c：記錄本題對應的知識點（LEARN 題組覆蓋率追溯；前端不顯示）
        content["knowledge_point"] = knowledge_point

    # 6-3d 綜合題：concept_tags 含目標 + 相關概念（去重保序）
    tags = [concept.tag]
    for c in extra_concepts or []:
        if c.tag not in tags:
            tags.append(c.tag)

    question = Question(
        type=question_type.value,
        concept_tags=tags,
        bloom_level=bloom_level,
        difficulty=difficulty,
        content=content,
        explanation=explanation,
        source=source.value,
        validated=False,
    )
    db.add(question)
    return question
