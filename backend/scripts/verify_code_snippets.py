"""教材／題庫程式碼健檢（2026-08-05 章節 41 `extern` 事件後新增）。

背景：grounded 生成會忠實複製逐字稿的錯誤——v41 把 `extern` 教成 `external`，
兩題全錯卻無人察覺，因為**沒有任何檢查會去驗證教材裡的程式碼真的能編譯**。

兩層檢查，成本天差地遠：

1. **靜態掃描（免費、每次都跑）**：拿 `corrections.json` 的 global_replacements
   當「已知錯誤拼法字典」掃全部教材與題目。任何一個鍵出現在 DB 內容裡＝退步。
2. **Judge0 編譯（有配額）**：把 coding 題的 `starter_code` 送去真的編譯一次。
   **每天上限 20 次**（Judge0 免費額度 50/天），未檢查過的優先、其次是最久沒檢查的，
   狀態寫入 `snippet_check_state.json`，跨天接續跑完整輪。

用法：
    .venv/bin/python -m scripts.verify_code_snippets --static-only   # 零成本
    .venv/bin/python -m scripts.verify_code_snippets                 # 靜態 + 最多 20 次編譯
    .venv/bin/python -m scripts.verify_code_snippets --limit 5
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import text as sa_text

from core.database import async_session
from services.judge0 import submit_and_poll

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORRECTIONS_FILE = _PROJECT_ROOT / "data" / "teaching_content" / "corrections.json"
STATE_FILE = _PROJECT_ROOT / "data" / "teaching_content" / "snippet_check_state.json"

DAILY_BUDGET = 20


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"last_run_date": None, "runs": [], "snippets": {}}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def bad_spellings() -> dict[str, str]:
    """已知錯誤拼法 → 正確寫法（沿用 corrections.json，不另維護第二份清單）。"""
    data = json.loads(CORRECTIONS_FILE.read_text(encoding="utf-8"))
    return data.get("global_replacements", {})


async def static_scan() -> list[str]:
    """掃描教材與題庫是否出現已知錯誤拼法；回傳問題描述清單。"""
    findings: list[str] = []
    async with async_session() as db:
        for bad, good in bad_spellings().items():
            for table, column in (
                ("questions", "content::text"),
                ("unit_content_staging", "content::text"),
                ("learning_units", "content::text"),
            ):
                result = await db.execute(
                    sa_text(
                        f"select count(*) from {table} where {column} like :pat"  # noqa: S608
                    ).bindparams(pat=f"%{bad}%")
                )
                n = result.scalar() or 0
                if n:
                    findings.append(f"{table}: {n} 筆含「{bad}」（應為「{good}」）")
    return findings


async def load_snippets() -> list[tuple[str, str]]:
    """取出所有 coding 題的 starter_code；回傳 (question_id, code)。"""
    async with async_session() as db:
        result = await db.execute(
            sa_text(
                "select id::text, content->>'starter_code' from questions "
                "where type = 'coding' and content->>'starter_code' is not null"
            )
        )
        return [(qid, code) for qid, code in result.all() if code and code.strip()]


def pick_targets(
    snippets: list[tuple[str, str]], state: dict, limit: int
) -> list[tuple[str, str]]:
    """未檢查過（或內容已變動）的優先，其次最久沒檢查的。"""
    records = state.get("snippets", {})

    def sort_key(item: tuple[str, str]) -> tuple[int, str]:
        qid, code = item
        rec = records.get(qid)
        digest = hashlib.sha256(code.encode()).hexdigest()[:12]
        if rec is None or rec.get("hash") != digest:
            return (0, "")  # 沒驗過或內容已變 → 最優先
        return (1, rec.get("checked_at", ""))

    return sorted(snippets, key=sort_key)[:limit]


async def compile_check(
    targets: list[tuple[str, str]], state: dict
) -> list[str]:
    """逐一送 Judge0 編譯；回傳失敗描述清單，並更新 state。"""
    failures: list[str] = []
    records = state.setdefault("snippets", {})
    for qid, code in targets:
        try:
            result = await submit_and_poll(source_code=code)
            status = result.status_description
            detail = (result.compile_output or "").strip().splitlines()
            problem = status if result.compile_output else ""
        except Exception as e:  # noqa: BLE001
            status, problem, detail = "EXCEPTION", repr(e), []
        records[qid] = {
            "hash": hashlib.sha256(code.encode()).hexdigest()[:12],
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status": status,
        }
        if problem:
            first = detail[0] if detail else ""
            failures.append(f"{qid} → {status}｜{first[:100]}")
        print(f"  {qid[:8]}… {status}")
    return failures


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--static-only", action="store_true", help="只做免費靜態掃描，不送 Judge0"
    )
    parser.add_argument(
        "--limit", type=int, default=DAILY_BUDGET,
        help=f"本次最多送幾支去編譯（預設 {DAILY_BUDGET}）",
    )
    args = parser.parse_args()

    print("=== 1) 靜態掃描：已知錯誤拼法 ===")
    findings = await static_scan()
    if findings:
        for f in findings:
            print(f"  ❌ {f}")
    else:
        print("  ✅ 無已知錯誤拼法")

    state = load_state()
    compile_failures: list[str] = []
    checked = 0

    if not args.static_only:
        snippets = await load_snippets()
        limit = max(0, min(args.limit, DAILY_BUDGET))
        targets = pick_targets(snippets, state, limit)
        print(f"\n=== 2) Judge0 編譯：{len(targets)}/{len(snippets)} 支（每日上限 {DAILY_BUDGET}）===")
        compile_failures = await compile_check(targets, state)
        checked = len(targets)

        done = sum(
            1
            for qid, code in snippets
            if state["snippets"].get(qid, {}).get("hash")
            == hashlib.sha256(code.encode()).hexdigest()[:12]
        )
        print(f"\n  累計已驗：{done}/{len(snippets)} 支")

    # 只有真的編譯過才算「今天跑過」——靜態掃描是免費的，不該用來消掉提醒
    if checked:
        state["last_run_date"] = date.today().isoformat()
        state.setdefault("runs", []).append(
            {
                "date": date.today().isoformat(),
                "compiled": checked,
                "static_findings": len(findings),
                "compile_failures": len(compile_failures),
            }
        )
        state["runs"] = state["runs"][-60:]  # 只留最近 60 次
        save_state(state)

    print("\n=== 摘要 ===")
    print(f"  靜態問題：{len(findings)}")
    print(f"  編譯失敗：{len(compile_failures)}")
    for f in compile_failures:
        print(f"    ❌ {f}")
    return 1 if (findings or compile_failures) else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
