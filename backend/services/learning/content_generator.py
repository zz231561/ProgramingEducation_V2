"""Phase 6-2a: Grounded LLM content generation for learning_units (NotebookLM mode).

2 content sections per unit（U2b 2026-07-06：summary section 已移除——提供現成摘要
屬被動學習效益低，前端摘要 tab 同步移除，批次生成省 1/3 LLM calls）：
  - concept_explanation：概念說明（Markdown，含 [mm:ss] citation）
  - code_examples：程式範例（1-3 個，必須源自字幕；課程介紹單元跳過，見 U2c）

Grounding rules（prompt + Pydantic 雙重把關）：
  1. 只能基於提供的 transcript_chunks 生成；嚴禁引入字幕未提及的概念
  2. 每段論述必須引用 [mm:ss] timestamp 作為佐證
  3. transcript 不足 → `needs_more_source=true` + `reason`，content 留空，**不 hallucinate**
  4. 繁體中文（台灣），程式碼/keyword 保留英文

Caller (6-2b) 負責：
  - 用 `retrieve_chunks` 配 video_order metadata filter 取出該 unit 的字幕 chunks
  - 將 result 持久化到 `learning_units.content`
"""

import json

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

from core.config import settings
from core.errors import AppError
from models.concept import Concept
from services.rag.retrieve import RetrievedChunk

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise AppError(503, "LLM_UNAVAILABLE", "OpenAI API Key 未設定")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


# === Pydantic 輸出模型（同時規範 LLM JSON shape 與下游使用）===


class Citation(BaseModel):
    """單筆 transcript citation：時間戳 + 原文節錄。"""

    timestamp: str = Field(..., description="mm:ss 或 mm:ss-mm:ss")
    text_excerpt: str = Field(..., max_length=120, description="原字幕節錄")


class ConceptExplanation(BaseModel):
    """概念說明 tab 內容。"""

    needs_more_source: bool = False
    reason: str = ""
    markdown: str = ""
    citations: list[Citation] = Field(default_factory=list)


class CodeExample(BaseModel):
    """單一程式範例。"""

    title: str
    code: str
    explanation: str = Field(max_length=200)
    citation: Citation | None = None


class CodeExamples(BaseModel):
    """範例 tab 內容。"""

    needs_more_source: bool = False
    reason: str = ""
    examples: list[CodeExample] = Field(default_factory=list, max_length=3)


class UnitContent(BaseModel):
    """單一 learning_unit 的完整 content（2 section 聚合）。"""

    concept_explanation: ConceptExplanation
    code_examples: CodeExamples


# === Prompt templates ===


_PREAMBLE = """你是 C++ 教材編輯，依教授實際 YouTube 教學影片字幕為學生製作學習單元內容。

【絕對規則 - 不可違反】
1. 你只能基於下方 TRANSCRIPT 區塊內容生成；嚴禁引入字幕未提及的概念、範例、公式
2. 每段論述必須引用 transcript 的 [mm:ss] 時間戳作為佐證
3. 若 TRANSCRIPT 不足以支持本節要求 → 設 needs_more_source=true、reason 簡短說明缺什麼，content 留空
4. 繁體中文（台灣用語），C++ 程式碼/關鍵字保留英文
5. 不臆測教授觀點；不補充字幕外的「常見補充」「業界做法」
"""


_CONCEPT_TASK = """\
【任務】生成「概念說明」段落，回傳 JSON：
{
  "needs_more_source": bool,
  "reason": "若 true 簡短說明缺什麼",
  "markdown": "Markdown 說明文（200-500 字），可內嵌 [mm:ss] citation",
  "citations": [{"timestamp": "mm:ss", "text_excerpt": "原字幕節錄 < 120 字"}]
}

撰寫指引：
- markdown 依影片實際教學脈絡組織，至少 2 個 citation
- transcript 太短 / 偏離主題 → needs_more_source=true
"""


_EXAMPLES_TASK = """\
【任務】生成「程式範例」段落，回傳 JSON：
{
  "needs_more_source": bool,
  "reason": "若 true 簡短說明缺什麼",
  "examples": [
    {"title": "範例標題", "code": "完整 C++ 程式碼", "explanation": "< 200 字",
     "citation": {"timestamp": "mm:ss", "text_excerpt": "..."}}
  ]
}

撰寫指引：
- 1-3 個範例（0 個 → needs_more_source=true）
- 範例必須與字幕中提到的程式碼或情境一致；不發明字幕未提到的程式碼
- 字幕只是純概念講解、無程式碼例子 → needs_more_source=true
"""


def _build_context_block(concept: Concept, chunks: list[RetrievedChunk]) -> str:
    """組裝 UNIT 上下文 + TRANSCRIPT 區塊。"""
    if not chunks:
        chunks_text = "(無檢索到 transcript chunks — 應 needs_more_source=true)"
    else:
        chunks_text = "\n\n".join(
            f"[chunk {i}]\n{c.text}" for i, c in enumerate(chunks, 1)
        )
    return f"""\
【UNIT 上下文】
- concept tag: {concept.tag}
- 中文名稱：{concept.name_zh}
- 英文名稱：{concept.name_en}
- 主題分類：{concept.category}
- 難度（1-5）：{concept.difficulty_level}
- 影片編號：{concept.video_order}

【TRANSCRIPT — 此 unit 對應字幕片段（依 video_order 過濾）】
{chunks_text}
"""


# === Generate functions ===


async def _call_llm_json(system: str, user: str, output_model: type) -> BaseModel:
    """共用 helper：呼叫 LLM、解析 JSON、Pydantic 驗證。"""
    client = _get_client()
    try:
        resp = await client.chat.completions.create(
            model=settings.llm_model_content,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
    except Exception as e:
        raise AppError(503, "LLM_UNAVAILABLE", f"OpenAI 失敗：{e}") from e

    content = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
        return output_model.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise AppError(502, "LLM_PARSE_ERROR", f"LLM 輸出格式錯誤：{e}") from e


async def generate_concept_explanation(
    concept: Concept, chunks: list[RetrievedChunk],
) -> ConceptExplanation:
    user = _build_context_block(concept, chunks) + "\n" + _CONCEPT_TASK
    return await _call_llm_json(_PREAMBLE, user, ConceptExplanation)


async def generate_code_examples(
    concept: Concept, chunks: list[RetrievedChunk],
) -> CodeExamples:
    user = _build_context_block(concept, chunks) + "\n" + _EXAMPLES_TASK
    return await _call_llm_json(_PREAMBLE, user, CodeExamples)


# U2c：課程介紹影片（video 1-3）無程式範例可教，批次生成跳過 examples LLM call
INTRO_CATEGORY = "課程介紹"


async def generate_unit_content(
    concept: Concept, chunks: list[RetrievedChunk],
) -> UnitContent:
    """Orchestrator：依序生 2 section（caller 控制 chunks 來源）。

    課程介紹單元（U2c）：code_examples 直接回空（前端也不顯示範例 tab），
    不標 needs_more_source 以免 6-4 抽查誤判為待補內容。
    """
    explanation = await generate_concept_explanation(concept, chunks)
    if concept.category == INTRO_CATEGORY:
        examples = CodeExamples()
    else:
        examples = await generate_code_examples(concept, chunks)
    return UnitContent(concept_explanation=explanation, code_examples=examples)
