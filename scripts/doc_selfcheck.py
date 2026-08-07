#!/usr/bin/env python3
"""文件自檢 — 掃出「文件寫的」與「實際的」不一致（roadmap 8-1d）。

背景：文件中的機械事實（行數 / 測試數 / 檔案是否存在）全靠手寫敘述，
沒有任何機制會在它失真時報錯。2026-08-06 稽核當場抓到兩例（tech-debt 宣稱
「無任何檔案超過硬上限」實際有 4 個；CLAUDE.md 自訂 ≤60 行實際 89 行）。

**手動跑，不掛 pre-commit**（會擋下想先存檔的中途 commit）：
    python3 scripts/doc_selfcheck.py

輸出為可直接貼進 tech-debt / changelog 的 markdown。
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# 2026-08-07 重新校準：判準是「AI 能否用檔名預測內容 + 能否一次讀完」，
# 不是人類認知負荷，故用原始行數。原 150/250 的 150 產生 78 個警告＝警告失效。
WARN_LINES, HARD_LINES = 250, 400
# 檔案前幾行內出現此標記即視為已舉證豁免（理由須對應 code-health skill 的三問）
EXEMPT_MARKER = "code-health: allow-large"
EXEMPT_SCAN_LINES = 5
SOURCE_GLOBS = ("backend/**/*.py", "web/**/*.ts", "web/**/*.tsx", "runner/**/*.py")
# 路徑解析的搜尋根（文件常以各專案內的相對路徑書寫）
PREFIXES = ("", "backend/", "web/", "runner/", "docs/")
# 歷史日誌不掃路徑：它們如實記錄「當時」的檔案，事後被刪除是正常的
# （如 R5d 移除的 stdin-panel.tsx），報成失效反而是雜訊
HISTORICAL = {"docs/changelog.md", "docs/roadmap-archive.md"}
DOC_FILES = ["CLAUDE.md", *sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("docs/*.md"))]
DOC_FILES += sorted(str(p.relative_to(ROOT)) for p in ROOT.glob(".claude/rules/*.md"))
DOC_FILES = [d for d in DOC_FILES if d not in HISTORICAL]

_PATH_RE = re.compile(r"`([a-zA-Z0-9_][a-zA-Z0-9_./-]*\.(?:py|ts|tsx|sh|yml|yaml|json))`")


def _git_files(include_untracked: bool = False) -> list[str]:
    """追蹤中的檔案；include_untracked 時併入「未追蹤但未被 ignore」的新檔。

    路徑存在性檢查必須含未追蹤檔，否則「本次新增、尚未 commit」的檔案會被誤報失效。
    """
    cmd = ["git", "ls-files"]
    if include_untracked:
        cmd += ["--cached", "--others", "--exclude-standard"]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)
    return out.stdout.splitlines()


def oversized() -> tuple[list[tuple[int, str]], list[tuple[int, str]], list[tuple[int, str]]]:
    """(超硬上限, 提醒線, 已舉證豁免)；測試檔不計（性質為條列案例非邏輯複雜度）。"""
    tracked = set(_git_files())
    hard: list[tuple[int, str]] = []
    warn: list[tuple[int, str]] = []
    exempt: list[tuple[int, str]] = []
    for pattern in SOURCE_GLOBS:
        for path in ROOT.glob(pattern):
            rel = str(path.relative_to(ROOT))
            if rel not in tracked or "/tests/" in rel or "/node_modules/" in rel:
                continue
            lines = path.read_text(errors="ignore").splitlines()
            n = len(lines)
            if n <= WARN_LINES:
                continue
            if any(EXEMPT_MARKER in line for line in lines[:EXEMPT_SCAN_LINES]):
                exempt.append((n, rel))
            elif n > HARD_LINES:
                hard.append((n, rel))
            else:
                warn.append((n, rel))
    return (
        sorted(hard, reverse=True),
        sorted(warn, reverse=True),
        sorted(exempt, reverse=True),
    )


def missing_paths() -> list[tuple[str, str]]:
    """文件中以 backtick 標注、但實際不存在的檔案路徑 → (doc, path)。

    解析採寬鬆比對（寧可漏報也不誤報）：完整相對路徑命中即可，
    只寫檔名（`chat.py`）或尾段（`edf/feedback.py`）則比對追蹤檔案的結尾。
    """
    known = _git_files(include_untracked=True)
    found: list[tuple[str, str]] = []
    for doc in DOC_FILES:
        doc_path = ROOT / doc
        if not doc_path.exists():
            continue
        for line in _live_lines(doc_path.read_text(errors="ignore")):
            for raw in set(_PATH_RE.findall(line)):
                if any((ROOT / f"{p}{raw}").exists() for p in PREFIXES):
                    continue
                if any(t.endswith(f"/{raw}") for t in known):
                    continue
                found.append((doc, raw))
    return sorted(set(found))


def _live_lines(text: str):
    """只回傳「描述現況」的行——跳過已消除區塊與刪除線行。

    `~~刪除線~~` 與「✅ 已消除」節記錄的是歷史（修好前的舊路徑），
    把它們算成失效路徑會讓報告永遠有雜訊、失去可信度。
    """
    in_resolved = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_resolved = "已消除" in line or "已完成" in line
        if in_resolved or "~~" in line:
            continue
        yield line


def test_counts() -> dict[str, int]:
    """各專案的測試函式數（不執行測試，純靜態計數，離線可跑）。"""
    counts: dict[str, int] = {}
    for name, folder in (("backend", "backend/tests"), ("runner", "runner/tests")):
        d = ROOT / folder
        if not d.exists():
            continue
        counts[name] = sum(
            len(re.findall(r"^\s*(?:async )?def test", f.read_text(errors="ignore"), re.M))
            for f in d.glob("*.py")
        )

    # web 走 vitest，計數單位是 `it(...)`（7-D1）
    web_tests = ROOT / "web/tests"
    if web_tests.exists():
        counts["web"] = sum(
            len(re.findall(r"^\s*it\(", f.read_text(errors="ignore"), re.M))
            for f in web_tests.glob("*.test.ts")
        )
    return counts


def main() -> int:
    hard, warn, exempt = oversized()
    missing = missing_paths()

    print("## 文件自檢報告\n")
    print("### 測試函式數")
    for name, n in test_counts().items():
        print(f"- {name}: {n}")

    print(f"\n### 🚫 超過硬上限 {HARD_LINES} 行（{len(hard)} 個）")
    for n, rel in hard:
        print(f"- `{rel}` {n}")
    if not hard:
        print("（無）")

    print(f"\n### ⚠ 介於 {WARN_LINES}–{HARD_LINES} 行，待逐案判斷（{len(warn)} 個）")
    print(", ".join(f"`{rel}` {n}" for n, rel in warn) or "（無）")

    print(f"\n### ✅ 已舉證豁免（{len(exempt)} 個）")
    print(", ".join(f"`{rel}` {n}" for n, rel in exempt) or "（無）")

    print(f"\n### 文件指向不存在的檔案（{len(missing)} 筆）")
    for doc, path in missing:
        print(f"- `{doc}` → `{path}`")
    if not missing:
        print("（無）")

    # 超硬上限或有失效路徑時回非零，方便未來接 CI
    return 1 if (hard or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
