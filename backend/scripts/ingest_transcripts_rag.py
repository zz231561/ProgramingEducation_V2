"""Phase 6-1e 後半：把 transcripts_corrected/ ingest 進 RAG（NotebookLM 核心）。

流程（每 video）：
  1. INSERT 1 documents 行（source='video_transcript' / title=f'video_{order:02d}: {title_zh}'）
  2. 把 segments 分組成 ~60 秒時間視窗
  3. 每視窗組成 1 個 LlamaIndex Document，text 含 timestamp markers，
     metadata 標 video_order / youtube_id / start_time_seconds / end_time_seconds
  4. pipeline.arun 一次餵入該 video 所有 windows → 寫入 data_codedge_rag 向量表

設計取捨：
- timestamp 嵌在 chunk text 裡 `[mm:ss]` markers → 6-2 LLM 可直接引用做 citation，
  不依賴 metadata（雖然 metadata 也有，但 LLM 看 text 比看 metadata 自然）
- 1 video = 1 documents row：簡化父子關係；chunks 透過 metadata.video_order 識別
- 每個 chunk 都有 metadata.video_order → 6-2b 可用 metadata filter 限縮 retrieve 範圍
- idempotent：已 ingest 過的 video（依 documents.title 判斷）skip

用法：
    cd backend
    .venv/bin/python -m scripts.ingest_transcripts_rag           # 全 62 部
    .venv/bin/python -m scripts.ingest_transcripts_rag --only 4  # 單一 video
    .venv/bin/python -m scripts.ingest_transcripts_rag --reset   # 砍重來（DELETE FROM data_codedge_rag WHERE source='video_transcript'）

成本估計：~93k tokens × $0.02/1M = ~$0.002 USD（embedding 很便宜）
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID, uuid4

from llama_index.core import Document
from sqlalchemy import text as sa_text

from core.database import async_session
from services.rag.pipeline import VECTOR_TABLE_NAME, get_ingestion_pipeline

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CORRECTED_DIR = _PROJECT_ROOT / "data" / "teaching_content" / "transcripts_corrected"
TIME_WINDOW_SECONDS = 60.0  # 每 60 秒語音切一個 chunk pre-pipeline


def fmt_timestamp(seconds: float) -> str:
    """3.2 → '00:03'；72.5 → '01:12'。"""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def group_segments(
    segments: list[dict], window_seconds: float = TIME_WINDOW_SECONDS
) -> list[list[dict]]:
    """把連續 segments 分組成 ~window_seconds 一組。"""
    groups: list[list[dict]] = []
    current: list[dict] = []
    window_start: float | None = None
    for seg in segments:
        if window_start is None:
            window_start = seg["start"]
        current.append(seg)
        if seg["end"] - window_start >= window_seconds:
            groups.append(current)
            current = []
            window_start = None
    if current:
        groups.append(current)
    return groups


def build_chunk_text(segments: list[dict]) -> str:
    """把該 window 的 segments 組成含 timestamp marker 的 chunk text。"""
    lines = []
    for seg in segments:
        ts = fmt_timestamp(seg["start"])
        lines.append(f"[{ts}] {seg['text']}")
    return "\n".join(lines)


async def video_already_ingested(doc_title: str) -> bool:
    """依 documents.title 判斷是否已 ingest 過（idempotent 保險）。"""
    async with async_session() as db:
        result = await db.execute(
            sa_text("SELECT 1 FROM documents WHERE title = :title LIMIT 1"
                   ).bindparams(title=doc_title)
        )
        return result.scalar_one_or_none() is not None


async def ingest_video(transcript: dict) -> int:
    """Ingest 單一 video 的 transcript；回傳 chunks 寫入數量。"""
    video_order = transcript["video_order"]
    youtube_id = transcript["youtube_id"]
    title_zh = transcript["title_zh"]
    doc_title = f"video_{video_order:02d}: {title_zh}"

    if await video_already_ingested(doc_title):
        print(f"  [{video_order:02d}] {title_zh} → SKIP (already ingested)")
        return 0

    segments = transcript.get("segments", [])
    if not segments:
        print(f"  [{video_order:02d}] {title_zh} → SKIP (no segments)")
        return 0

    groups = group_segments(segments)
    doc_id = uuid4()

    # 1) 建立 documents 行
    async with async_session() as db:
        await db.execute(
            sa_text(
                """
                INSERT INTO documents (id, source, title, version)
                VALUES (:id, 'video_transcript', :title, 1)
                """
            ).bindparams(id=doc_id, title=doc_title)
        )
        await db.commit()

    # 2) 組裝 LlamaIndex Documents（每時間視窗一個）
    documents = []
    for group in groups:
        chunk_text = build_chunk_text(group)
        documents.append(
            Document(
                text=chunk_text,
                metadata={
                    "doc_id": str(doc_id),
                    "video_order": video_order,
                    "youtube_id": youtube_id,
                    "title_zh": title_zh,
                    "start_time_seconds": group[0]["start"],
                    "end_time_seconds": group[-1]["end"],
                    "source_type": "video_transcript",
                },
            )
        )

    # 3) 跑 pipeline 一次餵入所有 windows
    pipeline = get_ingestion_pipeline()
    nodes = await pipeline.arun(documents=documents)

    # 4) 更新 documents.indexed_at
    async with async_session() as db:
        await db.execute(
            sa_text(
                "UPDATE documents SET indexed_at = NOW() WHERE id = :doc_id"
            ).bindparams(doc_id=doc_id)
        )
        await db.commit()

    print(
        f"  [{video_order:02d}] {title_zh} → "
        f"{len(groups)} windows → {len(nodes)} chunks"
    )
    return len(nodes)


async def reset_video_transcripts() -> int:
    """DELETE FROM documents WHERE source='video_transcript' + 對應 vector chunks。"""
    actual_table = f"data_{VECTOR_TABLE_NAME}"
    async with async_session() as db:
        # 先刪向量 chunks（依 metadata.source_type 過濾）
        result = await db.execute(
            sa_text(
                f"""
                DELETE FROM {actual_table}
                WHERE metadata_->>'source_type' = 'video_transcript'
                """  # noqa: S608
            )
        )
        chunks_deleted = result.rowcount or 0

        # 再刪 documents
        result = await db.execute(
            sa_text("DELETE FROM documents WHERE source = 'video_transcript'")
        )
        docs_deleted = result.rowcount or 0
        await db.commit()

        print(f"  Reset: {chunks_deleted} chunks + {docs_deleted} documents deleted")
    return chunks_deleted + docs_deleted


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", type=int, default=None,
                        help="Only ingest this video_order")
    parser.add_argument("--reset", action="store_true",
                        help="DELETE existing video_transcript chunks + docs first")
    args = parser.parse_args()

    if args.reset:
        await reset_video_transcripts()

    files = sorted(CORRECTED_DIR.glob("*.json"))
    if not files:
        sys.exit(
            f"❌ No corrected transcripts in {CORRECTED_DIR}; "
            f"run apply_corrections first"
        )

    if args.only is not None:
        files = [f for f in files if int(f.stem) == args.only]
        if not files:
            sys.exit(f"❌ No transcript file for video_order={args.only}")

    print(f"Ingesting {len(files)} transcripts to {VECTOR_TABLE_NAME}...")

    total_chunks = 0
    failed: list[tuple[int, str]] = []
    for f in files:
        transcript = json.loads(f.read_text(encoding="utf-8"))
        try:
            n = await ingest_video(transcript)
            total_chunks += n
        except Exception as e:
            print(f"  [{transcript['video_order']:02d}] ❌ FAILED: {e}")
            failed.append((transcript["video_order"], str(e)))

    print(f"\n=== Summary ===")
    print(f"  total chunks written: {total_chunks}")
    print(f"  failed videos: {len(failed)}")
    if failed:
        print(f"  failed orders: {[f[0] for f in failed]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
