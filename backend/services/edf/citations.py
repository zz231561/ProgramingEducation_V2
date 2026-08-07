"""教材引用的格式化與驗證 — Coddy 回應中的影片出處防幻覺。

背景：prompt 原本只注入 chunk 純文字，LLM 手上沒有任何
時間資訊卻仍輸出「影片 01:22～01:40」。修正後 prompt 帶上真實 metadata，但
**光靠 prompt 約束不足以保證 LLM 聽話**——本模組再加一道機械式驗證，把不在
檢索結果內的影片連結直接從回應中移除。

分層：
1. `format_rag_chunk` / `CITATION_RULE`  — 餵正確資料 + 明確規則（prompt 層）
2. `strip_ungrounded_citations`          — 機械攔截（不依賴 LLM 自律）
3. `extract_citations`                   — 供前端顯示原文，讓學生自行核對
"""

import logging
import re
from urllib.parse import parse_qs, urlparse

from services.rag import RetrievedChunk

logger = logging.getLogger(__name__)

__all__ = [
    "CITATION_RULE",
    "NO_SOURCE_RULE",
    "extract_citations",
    "format_rag_chunk",
    "format_timestamp",
    "strip_ungrounded_citations",
]

# LLM 引用影片時必須遵守的規則（有檢索結果時附在教材片段之後）
CITATION_RULE = (
    "引用影片時的規則：\n"
    "- 只能使用上面每則片段標示的「出處」資訊，**嚴禁自行推測或編造時間點**\n"
    "- 必須寫成 Markdown 連結格式：[章節名稱 分:秒](連結)，例如 [甚麼是程式語言 01:03](https://...)\n"
    "- 沒有出處資訊的片段就不要提時間點，直接說明概念即可\n"
    "- 若片段內容不含學生詢問的主題，誠實說這幾段沒講到；**不要**要求學生"
    "提供影片標題、連結或時間戳（學生無從提供，教材在系統這邊）"
)

# 檢索無結果時的誠實性規則——避免學生誤以為所有回答都出自教授教材
NO_SOURCE_RULE = (
    "本次沒有檢索到相關的教材片段。回答時：\n"
    "- **不可以**提及任何影片章節或時間點（你沒有這些資訊）\n"
    "- 若學生問的是「老師在哪裡講過」，要誠實說明這部分教材沒有直接對應的段落\n"
    "- 仍可用一般 C++ 知識引導，但不要宣稱那是課程教材的內容\n"
    "- **不要**反過來要求學生提供課程清單或影片連結（學生無從提供，教材在系統這邊）；"
    "找不到就直說找不到，並建議學生可到 Learn 頁瀏覽章節標題自行確認"
)

# 允許 t 參數與 chunk 起點的誤差（秒）——LLM 可能四捨五入到整分鐘
_TIMESTAMP_TOLERANCE = 90

_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\((https?://[^\s)]+)\)")
_YT_HOSTS = ("youtube.com", "youtu.be")


def format_timestamp(seconds: float) -> str:
    """秒數 → mm:ss。"""
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes:02d}:{secs:02d}"


def format_rag_chunk(index: int, chunk: RetrievedChunk) -> str:
    """組裝單則教材片段，metadata 齊全時附章節名稱與帶時間參數的 YouTube 連結。"""
    meta = chunk.metadata or {}
    title, youtube_id = meta.get("title_zh"), meta.get("youtube_id")
    start = meta.get("start_time_seconds")

    if title and youtube_id and start is not None:
        url = f"https://www.youtube.com/watch?v={youtube_id}&t={int(start)}s"
        header = f"[{index}] 出處：{title} {format_timestamp(start)}｜連結：{url}"
    else:
        # ingest 較早的片段可能缺 metadata — 不附出處，規則會要求該片段不提時間
        header = f"[{index}]"
    return f"{header}\n{chunk.text.strip()}"


def _parse_youtube_ref(url: str) -> tuple[str, int] | None:
    """從 YouTube URL 取出 (video_id, 起始秒數)；非 YouTube 連結回 None。"""
    parsed = urlparse(url)
    if not any(h in parsed.netloc for h in _YT_HOSTS):
        return None

    if "youtu.be" in parsed.netloc:
        video_id = parsed.path.lstrip("/")
    else:
        video_id = (parse_qs(parsed.query).get("v") or [""])[0]

    raw_t = (parse_qs(parsed.query).get("t") or ["0"])[0]
    try:
        seconds = int(raw_t.rstrip("s") or 0)
    except ValueError:
        seconds = 0
    return (video_id, seconds) if video_id else None


def _allowed_refs(chunks: list[RetrievedChunk]) -> dict[str, list[tuple[float, float]]]:
    """由檢索結果建立「合法出處」表：video_id → [(start, end), ...]。"""
    allowed: dict[str, list[tuple[float, float]]] = {}
    for c in chunks:
        meta = c.metadata or {}
        vid, start = meta.get("youtube_id"), meta.get("start_time_seconds")
        if not vid or start is None:
            continue
        end = meta.get("end_time_seconds", start)
        allowed.setdefault(vid, []).append((float(start), float(end)))
    return allowed


def strip_ungrounded_citations(
    text: str, chunks: list[RetrievedChunk]
) -> tuple[str, int]:
    """移除不在檢索結果內的影片連結，回傳 (清理後文字, 移除數量)。

    只處理 YouTube 連結——其他連結（如官方文件）不在本次 grounding 範圍內，保留。
    整段 Markdown 連結一併移除：連結標籤本身就含編造的時間，留著同樣是假資訊。
    """
    allowed = _allowed_refs(chunks)
    removed = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal removed
        ref = _parse_youtube_ref(match.group(2))
        if ref is None:
            return match.group(0)  # 非 YouTube 連結不管

        video_id, seconds = ref
        ranges = allowed.get(video_id)
        if ranges and any(
            start - _TIMESTAMP_TOLERANCE <= seconds <= end + _TIMESTAMP_TOLERANCE
            for start, end in ranges
        ):
            return match.group(0)

        removed += 1
        logger.warning(
            "攔截未 grounded 的影片引用：video=%s t=%ss label=%r",
            video_id, seconds, match.group(1)[:40],
        )
        return ""

    cleaned = _MD_LINK_RE.sub(_replace, text)
    if removed:
        # 清掉因移除而產生的空列表項與連續空行
        cleaned = re.sub(r"^[ \t]*[-*]\s*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned, removed


def extract_citations(chunks: list[RetrievedChunk]) -> list[dict]:
    """整理供前端顯示的引用資料（讓學生點開核對原文）。"""
    items: list[dict] = []
    for c in chunks:
        meta = c.metadata or {}
        title, youtube_id = meta.get("title_zh"), meta.get("youtube_id")
        start = meta.get("start_time_seconds")
        if not (title and youtube_id and start is not None):
            continue
        items.append({
            "title": title,
            "timestamp": format_timestamp(start),
            "url": f"https://www.youtube.com/watch?v={youtube_id}&t={int(start)}s",
            "excerpt": c.text.strip()[:400],
            "score": round(c.score, 3),
        })
    return items
