"""6-3c：影片知識點萃取——題量依知識量決定的前置步驟。

設計意圖：每部影片的觀念題數 = LLM 從該影片完整字幕萃取的重要知識點數
（3-8 點），每個知識點對應 1 題。萃取時明確排除「操作細節」類資訊
（介面位置、滑鼠點擊步驟等）——這類內容不構成可測驗的概念知識。

模型：分析組預設 LLM_MODEL（gpt-5.4-mini），任務屬理解歸納非生成。
"""

import json
import logging

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

from core.config import settings
from core.errors import AppError
from core.llm_params import chat_model_kwargs
from models.concept import Concept
from services.rag.retrieve import RetrievedChunk

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

MIN_POINTS = 3
MAX_POINTS = 8


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise AppError(503, "LLM_UNAVAILABLE", "OpenAI API Key 未設定")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


class _PointsResponse(BaseModel):
    # 不設 max_length：LLM 偶爾超量時由 caller 截斷（extract_knowledge_points），
    # 比硬性 ValidationError 更穩健
    points: list[str] = Field(min_length=1)


_PROMPT = f"""\
你是 C++ 教材分析師。閱讀以下教學影片字幕，列出學生看完本片後「必須掌握的重要知識點」。

規則：
1. {MIN_POINTS}-{MAX_POINTS} 個知識點；知識量少的短片列少、內容密集的長片列多
2. 每個知識點一句話（< 40 字），描述一個可被測驗的概念、語法規則或行為
3. **嚴禁列入操作細節**：軟體安裝步驟、介面按鈕位置、滑鼠點擊順序、
   「左上角/右下角」等畫面資訊——這些不是概念知識
4. 嚴禁列入字幕未提到的內容；不補充「常見補充知識」
5. 繁體中文，C++ 技術名詞保留英文

回傳嚴格 JSON：{{"points": ["知識點1", "知識點2", ...]}}
"""


async def extract_knowledge_points(
    concept: Concept, chunks: list[RetrievedChunk]
) -> list[str]:
    """LLM 從影片字幕萃取重要知識點清單。

    Returns:
        知識點字串列表（1-{MAX_POINTS} 項）

    Raises:
        AppError 503/502 — LLM 不可用 / 回傳不符 schema
    """
    client = _get_client()
    transcript = "\n\n".join(c.text for c in chunks) or "(無字幕)"
    user = f"""\
【影片資訊】v{concept.video_order:02d} {concept.name_zh}（{concept.name_en}）

【字幕（依時間順序）】
{transcript}
"""
    try:
        resp = await client.chat.completions.create(
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _PROMPT},
                {"role": "user", "content": user},
            ],
            **chat_model_kwargs(
                model=settings.LLM_MODEL, temperature=0.2, max_tokens=800
            ),
        )
    except Exception as e:
        raise AppError(503, "LLM_UNAVAILABLE", f"知識點萃取失敗：{e}") from e

    raw = resp.choices[0].message.content or "{}"
    try:
        parsed = _PointsResponse(**json.loads(raw))
    except (json.JSONDecodeError, ValidationError) as e:
        raise AppError(502, "LLM_PARSE_ERROR", f"知識點回傳格式異常：{e}") from e

    points = [p.strip() for p in parsed.points if p.strip()]
    if not points:
        raise AppError(502, "LLM_PARSE_ERROR", "知識點清單為空")
    return points[:MAX_POINTS]
