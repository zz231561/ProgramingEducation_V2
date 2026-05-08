"""Phase 6-1e Stage 1：套用 corrections.json 到 transcripts/ → transcripts_corrected/。

讀取：
  data/teaching_content/transcripts/{order:02d}.json   ← Whisper raw（不修改）
  data/teaching_content/corrections.json               ← 修正配置

寫入：
  data/teaching_content/transcripts_corrected/{order:02d}.json

兩層替換：
  1. global_replacements: dict[str, str]
     對所有 segment.text + full_text 套 str.replace（case-sensitive）
  2. per_video: dict[order_str, list[{segment_id, old, new}]]
     對單一影片的特定 segment 修正（segment_id = segments array 0-based index）

修正後重新合成 full_text = " ".join(seg.text)，確保 segments 與 full_text 一致。
產出 JSON 加 metadata `corrections_applied` 列出該 video 實際發生的替換次數。

用法：
    cd backend
    .venv/bin/python -m scripts.apply_corrections        # 全跑
    .venv/bin/python -m scripts.apply_corrections --only 4  # 單一 video
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TRANSCRIPTS_DIR = _PROJECT_ROOT / "data" / "teaching_content" / "transcripts"
CORRECTED_DIR = _PROJECT_ROOT / "data" / "teaching_content" / "transcripts_corrected"
CORRECTIONS_FILE = _PROJECT_ROOT / "data" / "teaching_content" / "corrections.json"


def load_corrections() -> tuple[dict[str, str], dict[str, list[dict]]]:
    if not CORRECTIONS_FILE.exists():
        sys.exit(f"❌ corrections.json not found: {CORRECTIONS_FILE}")
    data = json.loads(CORRECTIONS_FILE.read_text(encoding="utf-8"))
    return (
        data.get("global_replacements", {}) or {},
        data.get("per_video", {}) or {},
    )


def apply_to_transcript(
    transcript: dict,
    global_repl: dict[str, str],
    per_video_fixes: list[dict],
) -> tuple[dict, Counter]:
    """套用替換；回傳 (new_transcript, replacement_counter)。"""
    counter: Counter = Counter()

    new_segments = []
    for idx, seg in enumerate(transcript.get("segments", [])):
        text = seg["text"]

        # Layer 1: global replacements
        for old, new in global_repl.items():
            if old in text:
                count = text.count(old)
                counter[old] += count
                text = text.replace(old, new)

        # Layer 2: per-video segment-specific
        for fix in per_video_fixes:
            if fix.get("segment_id") == idx:
                old = fix["old"]
                new = fix["new"]
                if old in text:
                    counter[f"per-video[{idx}]:{old}"] += text.count(old)
                    text = text.replace(old, new)

        new_segments.append({"start": seg["start"], "end": seg["end"], "text": text})

    # 重新合成 full_text 與 segments 一致
    full_text = " ".join(s["text"] for s in new_segments).strip()

    new_transcript = {
        **{k: v for k, v in transcript.items() if k not in ("segments", "full_text")},
        "segments": new_segments,
        "full_text": full_text,
        "corrections_applied": dict(counter),
    }
    return new_transcript, counter


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", type=int, default=None,
                        help="Only apply to this video_order")
    args = parser.parse_args()

    global_repl, per_video = load_corrections()
    if not global_repl and not per_video:
        print("⚠ corrections.json is empty (no replacements defined); copy-only mode")

    transcript_files = sorted(TRANSCRIPTS_DIR.glob("*.json"))
    if not transcript_files:
        sys.exit(f"❌ No transcripts in {TRANSCRIPTS_DIR}; run transcribe_videos first")

    if args.only is not None:
        transcript_files = [
            f for f in transcript_files
            if int(f.stem) == args.only
        ]
        if not transcript_files:
            sys.exit(f"❌ No transcript file for video_order={args.only}")

    CORRECTED_DIR.mkdir(parents=True, exist_ok=True)

    total_counter: Counter = Counter()
    files_with_changes = 0

    for tf in transcript_files:
        transcript = json.loads(tf.read_text(encoding="utf-8"))
        order_str = f"{transcript['video_order']:02d}"
        per_video_fixes = per_video.get(order_str, [])

        new_transcript, counter = apply_to_transcript(
            transcript, global_repl, per_video_fixes,
        )
        if counter:
            files_with_changes += 1
            total_counter.update(counter)

        out_path = CORRECTED_DIR / tf.name
        out_path.write_text(
            json.dumps(new_transcript, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(f"✅ Wrote {len(transcript_files)} corrected transcripts to {CORRECTED_DIR}")
    print(f"   Files with at least 1 replacement: {files_with_changes} / {len(transcript_files)}")
    if total_counter:
        print(f"\n   Replacements summary (top 10):")
        for pattern, count in total_counter.most_common(10):
            print(f"     {pattern!r:40s} × {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
