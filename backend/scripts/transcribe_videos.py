"""Phase 6-1e Step 1: Whisper transcription via OpenAI API (B1 plan).

讀 `data/teaching_content/videos.csv` → 對每部影片：
  1. yt-dlp 抓 audio（cached at `audio_cache/{order:02d}.{m4a|webm}`）
  2. 呼叫 OpenAI `whisper-1` API（verbose_json，含 segment timestamps）
  3. 存 transcript 到 `data/teaching_content/transcripts/{order:02d}.json`

設計取捨：
- idempotent：transcripts/ 已存的 JSON 不重抓；audio_cache/ 已存的 audio 不重下
- 失敗安全：單部失敗不影響其他；最後彙總 failed orders 供 retry
- 成本上限：估計超過 $5 → abort（CLAUDE.md 守則：執行前說明假設）
- 預設刪 audio：節省磁碟（每部 ~5MB × 62 = ~300MB）；`--keep-audio` 保留
- prompt 注入 title_zh：提升 Whisper 對技術術語的辨識（如 `for 迴圈` / `pointer`）

用法：
    cd backend
    .venv/bin/python -m scripts.transcribe_videos --only 4    # sample 1 部
    .venv/bin/python -m scripts.transcribe_videos             # 全 62 部
    .venv/bin/python -m scripts.transcribe_videos --keep-audio  # 保留 audio cache
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from core.config import settings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CSV = _PROJECT_ROOT / "data" / "teaching_content" / "videos.csv"
TRANSCRIPTS_DIR = _PROJECT_ROOT / "data" / "teaching_content" / "transcripts"
AUDIO_CACHE_DIR = _PROJECT_ROOT / "data" / "teaching_content" / "audio_cache"

WHISPER_MODEL = "whisper-1"
WHISPER_RATE_USD_PER_MIN = 0.006  # OpenAI 2026-05 published rate
COST_CAP_USD = 5.0  # 超過此估計值 → abort
AUDIO_EXTS = ("m4a", "webm", "mp3", "opus")


@dataclass(frozen=True)
class VideoRow:
    video_order: int
    youtube_id: str
    duration_seconds: int
    title_zh: str


def parse_csv(path: Path) -> list[VideoRow]:
    if not path.exists():
        sys.exit(f"❌ CSV not found: {path}")
    rows: list[VideoRow] = []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(
                VideoRow(
                    video_order=int(row["video_order"]),
                    youtube_id=row["youtube_id"].strip(),
                    duration_seconds=int(row["duration_seconds"]),
                    title_zh=row["title_zh"].strip(),
                )
            )
    return rows


def find_cached_audio(out_dir: Path, order: int) -> Path | None:
    for ext in AUDIO_EXTS:
        candidate = out_dir / f"{order:02d}.{ext}"
        if candidate.exists():
            return candidate
    return None


def download_audio(yt_id: str, out_dir: Path, order: int) -> Path:
    """yt-dlp 抓 audio；已有快取直接返回。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    cached = find_cached_audio(out_dir, order)
    if cached is not None:
        return cached

    output_template = str(out_dir / f"{order:02d}.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f", "bestaudio[ext=m4a]/bestaudio",
        "--no-warnings",
        "--no-progress",
        "-o", output_template,
        f"https://www.youtube.com/watch?v={yt_id}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"yt-dlp failed for {yt_id}: {result.stderr.strip()[:300]}"
        )
    found = find_cached_audio(out_dir, order)
    if found is None:
        raise RuntimeError(
            f"No audio file found for {yt_id} after download (template={output_template})"
        )
    return found


def transcribe(client: OpenAI, audio_path: Path, title_zh: str) -> dict:
    """Call OpenAI Whisper API；回 verbose_json dict（含 segments + timestamps）。"""
    with audio_path.open("rb") as f:
        result = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=f,
            language="zh",
            prompt=f"繁體中文 C++ 程式設計教學影片：{title_zh}",
            response_format="verbose_json",
        )
    return result.model_dump()


def save_transcript(row: VideoRow, raw: dict, out_path: Path) -> int:
    """寫 transcript JSON；回傳 segment 數量。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    segments = [
        {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
        for s in raw.get("segments", [])
    ]
    payload = {
        "video_order": row.video_order,
        "youtube_id": row.youtube_id,
        "title_zh": row.title_zh,
        "duration_seconds": row.duration_seconds,
        "language": raw.get("language", "zh"),
        "model": WHISPER_MODEL,
        "segments": segments,
        "full_text": raw.get("text", "").strip(),
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return len(segments)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default=str(DEFAULT_CSV))
    parser.add_argument(
        "--only",
        type=int,
        default=None,
        help="Only transcribe this video_order (sample mode)",
    )
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="Don't delete audio files after successful transcription",
    )
    args = parser.parse_args()

    if not settings.OPENAI_API_KEY:
        sys.exit("❌ OPENAI_API_KEY not set (check backend/.env)")

    rows = parse_csv(Path(args.csv))
    if args.only is not None:
        rows = [r for r in rows if r.video_order == args.only]
        if not rows:
            sys.exit(f"❌ No video with video_order={args.only}")

    # 先估成本（已存的 transcripts 不算入）
    pending = [
        r for r in rows
        if not (TRANSCRIPTS_DIR / f"{r.video_order:02d}.json").exists()
    ]
    pending_seconds = sum(r.duration_seconds for r in pending)
    estimated_cost = pending_seconds / 60 * WHISPER_RATE_USD_PER_MIN

    print(f"Plan: {len(rows)} total / {len(pending)} pending / {len(rows) - len(pending)} already done")
    print(f"      pending audio: {pending_seconds / 60:.1f} min")
    print(f"      estimated cost: ${estimated_cost:.3f}")
    if estimated_cost > COST_CAP_USD:
        sys.exit(
            f"❌ Estimated cost ${estimated_cost:.2f} exceeds cap "
            f"${COST_CAP_USD:.2f}; aborting"
        )

    if not pending:
        print("\n✅ Nothing to do (all transcripts already exist)")
        return 0

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    actual_seconds = 0
    failed: list[tuple[int, str]] = []
    skipped = len(rows) - len(pending)

    for i, row in enumerate(rows, 1):
        out_path = TRANSCRIPTS_DIR / f"{row.video_order:02d}.json"
        if out_path.exists():
            print(f"  [{i}/{len(rows)}] {row.video_order:02d} {row.title_zh} → SKIP (exists)")
            continue

        try:
            t0 = time.time()
            audio = download_audio(row.youtube_id, AUDIO_CACHE_DIR, row.video_order)
            audio_mb = audio.stat().st_size / 1024 / 1024
            raw = transcribe(client, audio, row.title_zh)
            seg_count = save_transcript(row, raw, out_path)
            elapsed = time.time() - t0
            actual_seconds += row.duration_seconds
            if not args.keep_audio:
                audio.unlink(missing_ok=True)
            print(
                f"  [{i}/{len(rows)}] {row.video_order:02d} {row.title_zh} "
                f"({row.duration_seconds}s/{audio_mb:.1f}MB → {seg_count} segs, "
                f"{elapsed:.1f}s wall)"
            )
        except Exception as e:
            print(f"  [{i}/{len(rows)}] {row.video_order:02d} ❌ FAILED: {e}")
            failed.append((row.video_order, str(e)))

    actual_cost = actual_seconds / 60 * WHISPER_RATE_USD_PER_MIN
    processed = len(rows) - skipped - len(failed)
    print(f"\n=== Summary ===")
    print(f"  processed: {processed} / skipped: {skipped} / failed: {len(failed)}")
    print(f"  actual cost (this run): ${actual_cost:.3f}")
    if failed:
        print(f"  failed orders: {[f[0] for f in failed]}")
        print("  → re-run script to retry failed ones (idempotent)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
