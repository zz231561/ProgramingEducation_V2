"""離題訊息的輕量回應路徑（成本分流）。

Evidence 層以 `is_on_topic` 標記後，離題訊息不再走完整教學管線——跳過 RAG 檢索與
persona/strategy/K-Graph 組裝，input token 約降至 1/8。

設計原則：**分流不是攔截**。學生仍會收到回應，只是簡短並引導回課程；
以關鍵字黑名單擋人會誤傷「這題老師上課有講嗎」這類合法提問。
"""

import logging

from openai import AsyncOpenAI

from core.config import settings
from core.llm_params import chat_model_kwargs
from services.security.sanitizer import wrap_student_input

logger = logging.getLogger(__name__)


OFF_TOPIC_PROMPT = """\
你是 C++ 程式教學助教 Coddy。學生剛才的訊息與程式學習無關。

用 2-3 句繁體中文回應：
- 先自然承接一句，不說教也不責備
- 說明你專門協助這門 C++ 課程的學習
- 邀請他提出程式相關的問題，並給一個他現在就能問的具體例子
"""


async def generate_off_topic_reply(client: AsyncOpenAI, student_message: str) -> str:
    """離題訊息的輕量回應（跳過 RAG 與教學 prompt 組裝）。

    失敗時回固定文案而非拋錯：離題本來就不是需要 AI 才能處理的情境，
    沒必要為它讓學生看到錯誤畫面。
    """
    try:
        response = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": OFF_TOPIC_PROMPT},
                {"role": "user", "content": wrap_student_input(student_message)},
            ],
            **chat_model_kwargs(
                model=settings.LLM_MODEL, temperature=0.7, max_tokens=200
            ),
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.warning("離題輕量回應失敗，改用固定文案：%s: %s", type(e).__name__, e)
        return (
            "這個我幫不上忙耶——我專門協助你學這門 C++ 課程。\n\n"
            "有程式上的問題隨時問我，例如「這段迴圈為什麼跑不出我要的結果？」"
        )
