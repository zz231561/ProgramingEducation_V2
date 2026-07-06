"""Quiz 作答後 EDF 回饋生成（roadmap 3-2c）。

提交後立即顯示的 feedback 與 quiz/submit 的 feedback 不同：
- /quiz/submit 的 `feedback` 欄位 = 對錯一句話（即時、快）
- 本 service 的 feedback = 含學生 mastery + LLM 個人化建議 + 推薦學習單元（慢、async）

設計：
- 不重做 EDF Evidence Pipeline（quiz answer 結構化已知，不需 LLM 拆解錯誤類型）
- LLM 只負責「依對錯 + mastery 給 1-2 句建議」；失敗 fallback 為固定模板
- 推薦學習單元：限該學生 learning_paths 內、status != completed、concept 與 question.concept_tags 重疊
- 擁有權檢查：student_answer.user_id 與 user_id 對齊；非本人 → 404
"""

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.llm_params import chat_model_kwargs
from core.errors import AppError
from models.concept import Concept
from models.learning import LearningPath, LearningUnit, LearningUnitStatus
from models.mastery import StudentMastery
from models.quiz import Question, StudentAnswer

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            return None
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


@dataclass(frozen=True)
class ConceptMasteryItem:
    concept_tag: str
    concept_name_zh: str
    confidence: float  # 0.0-1.0；未練過視為 0


@dataclass(frozen=True)
class RecommendedUnit:
    unit_id: UUID
    path_id: UUID
    concept_tag: str
    concept_name_zh: str
    video_order: int | None
    status: str  # locked / available / in_progress


@dataclass(frozen=True)
class QuizFeedbackResult:
    concept_mastery: list[ConceptMasteryItem]
    suggestion: str
    suggestion_fallback: bool
    recommended_units: list[RecommendedUnit]


_SUGGESTION_FALLBACK_CORRECT = "答得很好！繼續挑戰下一題或進入更難的概念。"
_SUGGESTION_FALLBACK_WRONG = (
    "別氣餒，回頭看看相關概念的教學單元再試一次；多練習就能掌握。"
)


async def _get_owned_answer(
    db: AsyncSession, answer_id: UUID, user_id: UUID
) -> StudentAnswer:
    answer = (
        await db.execute(select(StudentAnswer).where(StudentAnswer.id == answer_id))
    ).scalar_one_or_none()
    if answer is None or answer.user_id != user_id:
        raise AppError(
            404,
            "STUDENT_ANSWER_NOT_FOUND",
            f"找不到作答紀錄：{answer_id}",
        )
    return answer


async def _fetch_concept_mastery(
    db: AsyncSession, user_id: UUID, concept_tags: list[str]
) -> list[ConceptMasteryItem]:
    """{tag: confidence}；未在 mastery 表中視為 0。回 list 順序對齊 concept_tags。"""
    if not concept_tags:
        return []
    rows = (
        await db.execute(
            select(Concept, StudentMastery.confidence)
            .outerjoin(
                StudentMastery,
                (StudentMastery.concept_id == Concept.id)
                & (StudentMastery.user_id == user_id),
            )
            .where(Concept.tag.in_(concept_tags))
        )
    ).all()
    by_tag = {c.tag: (c, conf) for c, conf in rows}
    items: list[ConceptMasteryItem] = []
    for tag in concept_tags:
        if tag not in by_tag:
            continue  # 該 tag 不在 concepts 表（如 EDF 留下的舊 tag）
        c, conf = by_tag[tag]
        items.append(ConceptMasteryItem(
            concept_tag=tag,
            concept_name_zh=c.name_zh,
            confidence=float(conf or 0.0),
        ))
    return items


async def _fetch_recommended_units(
    db: AsyncSession, user_id: UUID, concept_tags: list[str]
) -> list[RecommendedUnit]:
    """取該使用者 path 內、與題目 concept 相關、尚未完成的 unit。"""
    if not concept_tags:
        return []
    rows = (
        await db.execute(
            select(LearningUnit, LearningPath, Concept)
            .join(LearningPath, LearningPath.id == LearningUnit.path_id)
            .join(Concept, Concept.id == LearningUnit.concept_id)
            .where(LearningPath.user_id == user_id)
            .where(Concept.tag.in_(concept_tags))
            .where(LearningUnit.status != LearningUnitStatus.COMPLETED.value)
            .order_by(Concept.video_order.nulls_last())
        )
    ).all()
    return [
        RecommendedUnit(
            unit_id=unit.id,
            path_id=path.id,
            concept_tag=concept.tag,
            concept_name_zh=concept.name_zh,
            video_order=concept.video_order,
            status=unit.status,
        )
        for unit, path, concept in rows
    ]


def _build_suggestion_prompt(
    is_correct: bool,
    question_stem: str,
    concept_mastery: list[ConceptMasteryItem],
) -> str:
    mastery_lines = "\n".join(
        f"- {m.concept_name_zh}（{m.concept_tag}）: {round(m.confidence * 100)}%"
        for m in concept_mastery
    ) or "（無相關精熟度資料）"
    verdict = "答對了" if is_correct else "答錯了"
    return f"""\
你是 C++ 學習教練。學生剛在 Quiz {verdict}。請給 1-2 句個人化建議。

題幹：{question_stem}
學生在相關概念的精熟度（BKT）：
{mastery_lines}

規則：
- 答對且 mastery 高（≥ 70%）→ 鼓勵 + 建議挑戰更難內容
- 答對但 mastery 低 → 提醒「再多練幾題鞏固」
- 答錯且 mastery 高 → 提示「可能粗心或邊界條件，逐步檢查」
- 答錯且 mastery 低 → 建議「先複習概念再回頭做題」
- 1-2 句中文，溫暖鼓勵，**不可給完整答案 / 程式碼**

回傳嚴格 JSON：{{"suggestion": "<1-2 句中文建議>"}}
"""


async def _llm_suggestion(
    is_correct: bool,
    question_stem: str,
    concept_mastery: list[ConceptMasteryItem],
) -> tuple[str, bool]:
    """回 (suggestion, fallback)；fallback=True 表示用了固定模板。"""
    client = _get_client()
    fallback = (
        _SUGGESTION_FALLBACK_CORRECT if is_correct else _SUGGESTION_FALLBACK_WRONG
    )
    if client is None:
        return fallback, True

    try:
        response = await client.chat.completions.create(
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": _build_suggestion_prompt(
                        is_correct, question_stem, concept_mastery
                    ),
                },
                {"role": "user", "content": "請回傳 JSON。"},
            ],
            **chat_model_kwargs(
                model=settings.LLM_MODEL, temperature=0.4, max_tokens=200
            ),
        )
    except Exception:
        return fallback, True

    raw = response.choices[0].message.content or "{}"
    try:
        data: dict[str, Any] = json.loads(raw)
        suggestion = data.get("suggestion")
        if not isinstance(suggestion, str) or not suggestion.strip():
            raise ValueError("empty")
    except (json.JSONDecodeError, ValueError):
        return fallback, True
    return suggestion.strip(), False


async def generate_quiz_feedback(
    db: AsyncSession, user_id: UUID, answer_id: UUID
) -> QuizFeedbackResult:
    """組合 mastery + LLM suggestion + 推薦 units 為 quiz 結果頁的 EDF 回饋。

    Raises:
        AppError 404 STUDENT_ANSWER_NOT_FOUND
        AppError 404 QUESTION_NOT_FOUND（FK 異常理論不會發生）
    """
    answer = await _get_owned_answer(db, answer_id, user_id)
    question = (
        await db.execute(select(Question).where(Question.id == answer.question_id))
    ).scalar_one_or_none()
    if question is None:
        raise AppError(404, "QUESTION_NOT_FOUND", f"找不到題目：{answer.question_id}")

    concept_tags = list(question.concept_tags or [])
    concept_mastery = await _fetch_concept_mastery(db, user_id, concept_tags)
    recommended_units = await _fetch_recommended_units(db, user_id, concept_tags)
    suggestion, fallback = await _llm_suggestion(
        answer.is_correct,
        (question.content or {}).get("stem", ""),
        concept_mastery,
    )

    return QuizFeedbackResult(
        concept_mastery=concept_mastery,
        suggestion=suggestion,
        suggestion_fallback=fallback,
        recommended_units=recommended_units,
    )
