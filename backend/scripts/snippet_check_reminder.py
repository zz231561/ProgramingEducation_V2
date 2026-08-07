"""Session 開始時核對：教材程式碼健檢是否仍有未完成項目（SessionStart hook 用）。

只讀 `snippet_check_state.json`，僅用標準函式庫（hook 不經過 venv）。
全量完成且上次無問題 → 靜默；否則提醒並附上指令。
"""

import json
from pathlib import Path

STATE_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "teaching_content"
    / "snippet_check_state.json"
)
CMD = "cd backend && .venv/bin/python -m scripts.verify_code_snippets"


def main() -> None:
    if not STATE_FILE.exists():
        print(f"[教材健檢] 尚未執行過。今天要跑嗎？→ {CMD}")
        return

    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print(f"[教材健檢] 狀態檔讀取失敗，建議重跑一次 → {CMD}")
        return

    runs = state.get("runs", [])
    last = state.get("last_run_date") or "從未"
    snippets = state.get("snippets", {})
    tail = runs[-1] if runs else {}
    remaining = state.get("remaining")
    if remaining == 0 and not tail.get("compile_failures") and not tail.get("static_findings"):
        return
    extra = ""
    if tail.get("compile_failures") or tail.get("static_findings"):
        extra = (
            f"；上次留有 靜態 {tail.get('static_findings', 0)} / "
            f"編譯 {tail.get('compile_failures', 0)} 個問題"
        )
    print(
        f"[教材健檢] 上次是 {last}（已驗 {len(snippets)} 支 starter_code）{extra}\n"
        f"            預設全量檢查 → {CMD}"
    )


if __name__ == "__main__":
    main()
