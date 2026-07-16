"""Coddy 反思開場 service — 學生帶反思進 Workspace 時的主動開場訊息。

設計（2026-07-16 使用者定案：「modal 追問一層，剩下交給 Coddy」）：
- 開場內容：(1) 引用反思亮點先肯定 (2) 溫和接手「被跳過的追問」或補充最模糊處
  （已回答過的追問不重複問）(3) 邀請學生提出想先弄懂的概念；3–5 句、不給程式碼
- 每個反思開場一次（前端 sessionStorage 去重）；建立獨立新 session（一次解題一個脈絡）
- LLM 失敗 fail-open：改用固定友善開場，不擋流程（與 mastery / RAG 容錯哲學一致）
"""

import logging
import uuid

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.errors import AppError
from core.llm_params import chat_model_kwargs
from models.chat import ChatMessage, ChatSession, MessageRole
from models.quiz import Question
from models.reflection import Reflection, ReflectionSourceType

logger = logging.getLogger(__name__)

_FALLBACK_MESSAGE = (
    "我看過你的反思計畫了，方向不錯！開始動手吧——"
    "過程中有任何不清楚的概念或卡住的地方，隨時問我。"
)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            return None
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def _followup_instruction(reflection: Reflection) -> str:
    if reflection.followup_question and not reflection.followup_answer:
        return (
            f"教練先前追問過「{reflection.followup_question}」但學生尚未回應——"
            "請換一種更輕鬆的說法自然帶到這個模糊點（不要照抄原句、不要提到「追問」二字）。"
        )
    if reflection.followup_question and reflection.followup_answer:
        return (
            "學生已回應過教練的追問，不要重複問同一件事；"
            "改為針對反思中另一處較模糊的地方，補充一句說明或提出一個小問題。"
        )
    return "針對反思中最模糊的一處，補充一句說明或提出一個小問題。"


def _build_prompt(reflection: Reflection, question: Question | None) -> str:
    stem = (question.content or {}).get("stem", "") if question else ""
    return f"""\
你是 Coddy，一位像鄰座學長姊的 C++ 教練。學生剛寫完「動手前反思」、帶著計畫進入程式編輯器。
請寫一則開場訊息（繁體中文，3–5 句，不用條列、不用標題）：

1. 從學生反思中挑一個具體亮點，先肯定（引用他自己的說法）
2. {_followup_instruction(reflection)}
3. 結尾邀請：若有哪個概念想先弄清楚，可以直接問你

規則：不可給完整程式碼、不可直接給解法答案；語氣自然友善，不說教。

題目：
{stem or "（無題目脈絡）"}

學生反思：
- 問題理解：{reflection.problem_understanding!r}
- 解題步驟：{reflection.planned_steps!r}
- 預期概念：{reflection.expected_concepts!r}
- 教練追問：{reflection.followup_question!r}
- 學生回應：{reflection.followup_answer!r}
"""


async def _generate_opening(
    reflection: Reflection, question: Question | None
) -> str:
    """生成開場訊息；任何失敗回 fallback 文案（fail-open）。"""
    client = _get_client()
    if client is None:
        return _FALLBACK_MESSAGE
    try:
        response = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": _build_prompt(reflection, question)},
                {"role": "user", "content": "請寫開場訊息。"},
            ],
            **chat_model_kwargs(
                model=settings.LLM_MODEL, temperature=0.5, max_tokens=350
            ),
        )
        content = (response.choices[0].message.content or "").strip()
        return content or _FALLBACK_MESSAGE
    except Exception as e:
        logger.warning("reflection kickoff LLM failed (fail-open): %r", e)
        return _FALLBACK_MESSAGE


async def reflection_kickoff(
    db: AsyncSession, user_id: uuid.UUID, reflection_id: uuid.UUID
) -> tuple[ChatSession, ChatMessage]:
    """建立新 chat session 並寫入 Coddy 開場訊息。

    Returns:
        (session, assistant_message)；反思不存在或非本人 → 404。
    """
    reflection = (
        await db.execute(select(Reflection).where(Reflection.id == reflection_id))
    ).scalar_one_or_none()
    if reflection is None or reflection.user_id != user_id:
        raise AppError(404, "REFLECTION_NOT_FOUND", "反思不存在")

    question: Question | None = None
    if reflection.source_type == ReflectionSourceType.QUIZ.value:
        question = await db.get(Question, reflection.source_id)

    content = await _generate_opening(reflection, question)

    stem = (question.content or {}).get("stem", "") if question else ""
    title = f"實作題：{stem[:40]}" if stem else "程式實作題引導"
    session = ChatSession(user_id=user_id, title=title[:50])
    db.add(session)
    await db.flush()

    message = ChatMessage(
        session_id=session.id, role=MessageRole.ASSISTANT, content=content
    )
    db.add(message)
    await db.commit()
    await db.refresh(session)
    await db.refresh(message)
    return session, message
