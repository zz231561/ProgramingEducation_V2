#!/usr/bin/env python3
"""
Phase 6-1a/6-1b 前置：YouTube playlist → CSV 對應 DB concepts.video_order。

Pipeline:
  1. 用 yt-dlp 抓 playlist 全部影片的 (id, title, duration)
  2. 從標題 `C++：XX-...` 抽 video_order；過濾 XX ∉ [4, 62] 的影片
  3. 對齊驗證：缺漏 / 重複 / 多餘 全部報告
  4. 輸出 CSV：欄位 video_order, youtube_id, duration_seconds, title_zh

Usage:
    python backend/scripts/fetch_playlist_metadata.py \
        "https://youtube.com/playlist?list=PLxxxxx" \
        [output.csv]

Default output: data/teaching_content/videos.csv

Pre-req: brew install yt-dlp
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

# 標題格式：「C++：XX-(中文)」，XX = video_order
TITLE_PATTERN = re.compile(r"^C\+\+：(\d+)-(.+)$")
EXPECTED_VIDEO_ORDERS = set(range(4, 63))  # DB seed 4..62 共 59 部
DEFAULT_OUTPUT = Path("data/teaching_content/videos.csv")


def fetch_playlist(url: str) -> list[dict]:
    """呼叫 yt-dlp 抓全部影片 metadata（含 duration，較慢，~1-3 分鐘）。"""
    cmd = [
        "yt-dlp",
        "--no-warnings",
        "--ignore-errors",
        "--print",
        "%(id)s\t%(title)s\t%(duration)s",
        url,
    ]
    print(f"  → yt-dlp fetching (this may take 1-3 min for ~60 videos)...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and not result.stdout:
        print(result.stderr, file=sys.stderr)
        sys.exit(f"yt-dlp failed (exit {result.returncode})")

    rows: list[dict] = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            print(f"  ⚠ skip malformed line: {line!r}", file=sys.stderr)
            continue
        vid, title, duration_str = parts
        if duration_str in ("NA", "None", ""):
            print(f"  ⚠ no duration for {vid} ({title}) — skip")
            continue
        rows.append({"id": vid, "title": title, "duration": int(duration_str)})
    return rows


def align(entries: list[dict]) -> tuple[list[dict], list[dict]]:
    """過濾 + 對齊到 DB video_order；回傳 (aligned, skipped)。"""
    aligned: list[dict] = []
    skipped: list[dict] = []
    for e in entries:
        m = TITLE_PATTERN.match(e["title"])
        if not m:
            skipped.append({**e, "reason": "title_pattern_mismatch"})
            continue
        order = int(m.group(1))
        if order not in EXPECTED_VIDEO_ORDERS:
            skipped.append({**e, "reason": f"video_order={order}_out_of_range"})
            continue
        aligned.append(
            {
                "video_order": order,
                "youtube_id": e["id"],
                "duration_seconds": e["duration"],
                "title_zh": m.group(2),
            }
        )
    aligned.sort(key=lambda r: r["video_order"])
    return aligned, skipped


def report(aligned: list[dict], skipped: list[dict]) -> bool:
    """輸出對齊報告；回傳是否完美對齊。"""
    print("\n=== Alignment Report ===")
    print(f"  aligned: {len(aligned)}  /  skipped: {len(skipped)}")

    if skipped:
        print("\n  Skipped entries:")
        for s in skipped:
            print(f"    - [{s['reason']}] {s['id']} | {s['title']}")

    actual = [r["video_order"] for r in aligned]
    actual_set = set(actual)
    missing = sorted(EXPECTED_VIDEO_ORDERS - actual_set)
    duplicates = sorted({v for v in actual if actual.count(v) > 1})

    perfect = not missing and not duplicates and len(aligned) == 59
    if missing:
        print(f"  ❌ MISSING video_order: {missing}")
    if duplicates:
        print(f"  ❌ DUPLICATE video_order: {duplicates}")
    if perfect:
        print("  ✅ All 59 expected video_orders (4-62) present, no duplicates")
    return perfect


def write_csv(rows: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["video_order", "youtube_id", "duration_seconds", "title_zh"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    url = sys.argv[1]
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT

    entries = fetch_playlist(url)
    print(f"  ← fetched {len(entries)} entries")

    aligned, skipped = align(entries)
    perfect = report(aligned, skipped)

    write_csv(aligned, output)
    print(f"\n✅ Wrote {len(aligned)} rows to {output}")
    return 0 if perfect else 1


if __name__ == "__main__":
    sys.exit(main())
