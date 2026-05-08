"""Phase 6-1e Stage 2：用 LLM 自動掃描 transcripts/ 找可疑錯誤。

對每份 transcript 送 GPT-4o-mini 評估，找：
  - 語意明顯不通順的句子（被切壞、缺主詞、邏輯斷裂）
  - C++ 程式術語錯字（如「盤特」應為 pointer / 「拓」應為 int x）
  - 段落重複（Whisper 對靜音段的 hallucination 通病）

輸出 `data/teaching_content/issues_proposal.json`：
  {
    "video_order": 4,
    "issues": [
      {
        "segment_id": 12,
        "snippet": "原文 segment.text",
        "type": "semantic|term|repetition",
        "suggested_fix": "建議修正",
        "confidence": 0.0-1.0,
        "reasoning": "為什麼覺得有問題"
      }
    ]
  }

工作流程：
  1. 跑此 script 產出 issues_proposal.json（你 / 我 review）
  2. 把該採納的 fix 加進 corrections.json 的 per_video
  3. 重跑 apply_corrections 產出新版 transcripts_corrected/

成本估計：62 部 × ~5k chars × gpt-4o-mini = ~$0.07 USD（極便宜）。

用法：
    cd backend
    .venv/bin/python -m scripts.flag_transcripts            # 全 62 部
    .venv/bin/python -m scripts.flag_transcripts --only 4   # 單一 video
    .venv/bin/python -m scripts.flag_transcripts --limit 5  # 前 5 部試跑
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from openai import OpenAI

from core.config import settings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TRANSCRIPTS_DIR = _PROJECT_ROOT / "data" / "teaching_content" / "transcripts"
OUTPUT_FILE = _PROJECT_ROOT / "data" / "teaching_content" / "issues_proposal.json"

LLM_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """你是繁體中文 C++ 教學影片 Whisper 字幕的 QA 審核員。
給你一份字幕（含 segment id、timestamp、text），請找出**明顯**的錯誤：

1. **type=semantic**：句子被切壞 / 缺主詞 / 邏輯斷裂明顯（不是「斷句不漂亮」這種小問題，是「讀完一頭霧水」的程度）
2. **type=term**：C++ 程式術語錯字（變數型別 / 運算子 / 標準庫名稱被音譯成中文，例：「盤特」=pointer / 「弗洛特」=float / 「歐特」=auto）
3. **type=repetition**：相同句子在連續 segments 內重複 3 次以上（Whisper 對靜音段的 hallucination）

**只回報你 confidence ≥ 0.7 的問題**。寧可漏報，不可誤報——
我們寧願少 flag 幾個錯誤，也不要把正確的字幕誤標為錯誤導致教授浪費時間 review。

回傳 JSON：
{
  "issues": [
    {
      "segment_id": 12,
      "snippet": "原始 segment.text 內容（不要修改）",
      "type": "semantic" | "term" | "repetition",
      "suggested_fix": "建議的修正後文字",
      "confidence": 0.85,
      "reasoning": "簡短說明為什麼這是錯誤（< 30 字）"
    }
  ]
}

如無問題回傳 `{"issues": []}`。"""


def build_user_prompt(transcript: dict) -> str:
    """組裝給 LLM 看的 transcript 內容。"""
    lines = [
        f"video_order: {transcript['video_order']}",
        f"title: {transcript['title_zh']}",
        f"duration: {transcript['duration_seconds']}s",
        f"total_segments: {len(transcript['segments'])}",
        "",
        "Segments:",
    ]
    for idx, seg in enumerate(transcript["segments"]):
        lines.append(
            f"[{idx:3d}] {seg['start']:6.1f}-{seg['end']:6.1f}: {seg['text']}"
        )
    return "\n".join(lines)


def scan_transcript(client: OpenAI, transcript: dict) -> list[dict]:
    """呼叫 LLM；回傳 issues list（empty 表示無問題）。"""
    user_msg = build_user_prompt(transcript)
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    content = resp.choices[0].message.content
    if not content:
        return []
    try:
        parsed = json.loads(content)
        return parsed.get("issues", [])
    except json.JSONDecodeError as e:
        print(f"  ⚠ JSON parse failed: {e}")
        return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None,
                        help="Only scan first N transcripts (for testing)")
    args = parser.parse_args()

    if not settings.OPENAI_API_KEY:
        sys.exit("❌ OPENAI_API_KEY not set (check backend/.env)")

    files = sorted(TRANSCRIPTS_DIR.glob("*.json"))
    if not files:
        sys.exit(f"❌ No transcripts in {TRANSCRIPTS_DIR}")
    if args.only is not None:
        files = [f for f in files if int(f.stem) == args.only]
    elif args.limit:
        files = files[:args.limit]

    print(f"Scanning {len(files)} transcripts with {LLM_MODEL}...")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    all_results: list[dict] = []
    total_issues = 0

    for i, tf in enumerate(files, 1):
        transcript = json.loads(tf.read_text(encoding="utf-8"))
        t0 = time.time()
        try:
            issues = scan_transcript(client, transcript)
        except Exception as e:
            print(f"  [{i}/{len(files)}] {tf.stem} ❌ {e}")
            continue
        elapsed = time.time() - t0
        all_results.append(
            {
                "video_order": transcript["video_order"],
                "title_zh": transcript["title_zh"],
                "issues": issues,
            }
        )
        total_issues += len(issues)
        flag = f"⚠ {len(issues)} issues" if issues else "✅ clean"
        print(f"  [{i}/{len(files)}] {tf.stem} {flag} ({elapsed:.1f}s)")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(
            {"results": all_results, "total_issues": total_issues},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n✅ Wrote {OUTPUT_FILE}")
    print(f"   Total issues flagged: {total_issues}")
    print(f"   Videos with issues: {sum(1 for r in all_results if r['issues'])} / {len(all_results)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
