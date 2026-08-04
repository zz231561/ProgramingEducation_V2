"""教材引用格式化與防幻覺驗證測試（services/edf/citations.py）。"""

from services.edf.citations import (
    extract_citations,
    format_rag_chunk,
    format_timestamp,
    strip_ungrounded_citations,
)
from services.rag import RetrievedChunk


def _chunk(youtube_id="BOSnYUGCU8I", start=63.0, end=125.0, title="甚麼是程式語言"):
    return RetrievedChunk(
        text="這段在講程式語言的基本概念",
        score=0.55,
        doc_id="doc-1",
        metadata={
            "title_zh": title,
            "youtube_id": youtube_id,
            "start_time_seconds": start,
            "end_time_seconds": end,
        },
    )


# === 時間格式 ===

def test_format_timestamp():
    assert format_timestamp(63.0) == "01:03"
    assert format_timestamp(245.0) == "04:05"
    assert format_timestamp(0) == "00:00"


# === prompt 片段格式化 ===

def test_format_rag_chunk_includes_source_and_link():
    out = format_rag_chunk(1, _chunk())
    assert "甚麼是程式語言 01:03" in out
    assert "https://www.youtube.com/watch?v=BOSnYUGCU8I&t=63s" in out


def test_format_rag_chunk_without_metadata_omits_source():
    bare = RetrievedChunk(text="片段內容", score=0.5, doc_id=None, metadata={})
    out = format_rag_chunk(2, bare)
    assert out.startswith("[2]\n")
    assert "出處" not in out


# === 防幻覺：移除未 grounded 的引用 ===

def test_keeps_citation_matching_retrieved_chunk():
    text = "看這裡 [甚麼是程式語言 01:03](https://www.youtube.com/watch?v=BOSnYUGCU8I&t=63s)"
    cleaned, removed = strip_ungrounded_citations(text, [_chunk()])
    assert removed == 0
    assert "BOSnYUGCU8I" in cleaned


def test_strips_citation_with_unknown_video():
    text = "老師說過 [某章節 02:00](https://www.youtube.com/watch?v=FAKEVIDEO01&t=120s)"
    cleaned, removed = strip_ungrounded_citations(text, [_chunk()])
    assert removed == 1
    assert "FAKEVIDEO01" not in cleaned
    assert "某章節" not in cleaned  # 標籤含編造時間，一併移除


def test_strips_citation_with_timestamp_far_outside_chunk():
    """影片對但時間差太遠 → 仍屬編造。"""
    text = "[甚麼是程式語言 15:00](https://www.youtube.com/watch?v=BOSnYUGCU8I&t=900s)"
    cleaned, removed = strip_ungrounded_citations(text, [_chunk()])
    assert removed == 1
    assert "youtube.com" not in cleaned


def test_tolerates_small_timestamp_drift():
    """LLM 常把 63 秒寫成 01:00 — 容差內視為合法。"""
    text = "[甚麼是程式語言 01:00](https://www.youtube.com/watch?v=BOSnYUGCU8I&t=60s)"
    _, removed = strip_ungrounded_citations(text, [_chunk()])
    assert removed == 0


def test_keeps_non_youtube_links():
    text = "參考 [cppreference](https://en.cppreference.com/w/cpp/io) 的說明"
    cleaned, removed = strip_ungrounded_citations(text, [_chunk()])
    assert removed == 0
    assert "cppreference" in cleaned


def test_strips_all_citations_when_no_chunks_retrieved():
    """完全沒檢索到教材時，任何影片引用都是幻覺。"""
    text = "老師有講 [章節 01:03](https://www.youtube.com/watch?v=BOSnYUGCU8I&t=63s)"
    cleaned, removed = strip_ungrounded_citations(text, [])
    assert removed == 1
    assert "youtube.com" not in cleaned


def test_cleans_empty_list_items_after_stripping():
    text = (
        "可以看這幾段：\n"
        "- [假章節 02:00](https://www.youtube.com/watch?v=FAKEVIDEO01&t=120s)\n"
        "- 另一個重點"
    )
    cleaned, removed = strip_ungrounded_citations(text, [_chunk()])
    assert removed == 1
    assert "另一個重點" in cleaned
    assert "\n\n\n" not in cleaned


def test_youtu_be_short_url_is_parsed():
    text = "[章節 01:03](https://youtu.be/BOSnYUGCU8I?t=63s)"
    _, removed = strip_ungrounded_citations(text, [_chunk()])
    assert removed == 0


# === 供前端顯示的引用資料 ===

def test_extract_citations_shape():
    items = extract_citations([_chunk()])
    assert len(items) == 1
    assert items[0]["title"] == "甚麼是程式語言"
    assert items[0]["timestamp"] == "01:03"
    assert items[0]["url"].endswith("&t=63s")
    assert items[0]["excerpt"]


def test_extract_citations_skips_chunks_without_metadata():
    bare = RetrievedChunk(text="無 metadata", score=0.5, doc_id=None, metadata={})
    assert extract_citations([bare]) == []
