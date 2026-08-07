#!/usr/bin/env python3
"""把 Claude Code 的規則檔同步成 Codex 讀得到的 `AGENTS.md`（2026-08-07）。

**要解的問題**：`.claude/rules/*.md` 在 Claude Code 是依 frontmatter 的 `globs`
自動注入（編輯 `web/**` 就注入 frontend.md）。Codex 沒有這個機制，改為讀
**從 repo root 到 cwd 沿路的 `AGENTS.md`**。兩者語意不同但可對映：

    globs: web/**                   →  web/AGENTS.md
    globs: backend/**               →  backend/AGENTS.md
    globs: backend/services/edf/**  →  backend/services/edf/AGENTS.md

⚠ **仍有一個殘留差異**：Codex 依 **cwd** 決定載入哪幾層，不是依「正在編輯哪個檔」。
在 repo root 跑 codex 去改 `web/` 底下的檔案，`web/AGENTS.md` 不會自動載入——
所以根 `AGENTS.md` 另外寫了一張路由表，明文要求動這些路徑前先讀對應檔案。

用法：`python3 scripts/sync_agents_md.py [--check]`
`--check` 只回報是否同步（CI / hook 用），不寫檔。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / ".claude/rules"
GENERATED_BANNER = (
    "<!-- 由 scripts/sync_agents_md.py 自動產生，請勿直接編輯；"
    "改動請改來源檔，再重跑同步 -->\n<!-- 來源：{source} -->\n\n"
)


def _target_dir_from_globs(rule: Path) -> Path | None:
    """從 frontmatter 的 `globs:` 推導目標目錄；無 globs 或無法對映回 None。"""
    head = rule.read_text(errors="ignore").split("---", 2)
    if len(head) < 3:
        return None
    match = re.search(r"^globs:\s*(.+)$", head[1], re.M)
    if not match:
        return None
    # 只處理單一 glob 且以 /** 結尾的形式（本專案三份規則皆如此）
    pattern = match.group(1).strip()
    if not pattern.endswith("/**") or "," in pattern or "{" in pattern:
        return None
    return ROOT / pattern[: -len("/**")]


def _pairs() -> list[tuple[Path, Path]]:
    """(來源, 目標 AGENTS.md)；含根層 CLAUDE.md。"""
    out = [(ROOT / "CLAUDE.md", ROOT / "AGENTS.md")]
    for rule in sorted(RULES_DIR.glob("*.md")):
        target_dir = _target_dir_from_globs(rule)
        if target_dir and target_dir.is_dir():
            out.append((rule, target_dir / "AGENTS.md"))
    return out


def _render(source: Path) -> str:
    """根 CLAUDE.md 原樣複製（hook 也是這樣做，保持一致）；規則檔加來源註記。"""
    body = source.read_text(errors="ignore")
    if source.name == "CLAUDE.md":
        return body
    rel = source.relative_to(ROOT)
    return GENERATED_BANNER.format(source=rel) + body


def main() -> int:
    check_only = "--check" in sys.argv
    stale: list[str] = []
    for source, target in _pairs():
        if not source.exists():
            continue
        want = _render(source)
        if target.exists() and target.read_text(errors="ignore") == want:
            continue
        stale.append(str(target.relative_to(ROOT)))
        if not check_only:
            target.write_text(want)

    if not stale:
        print("AGENTS.md 全部已同步")
        return 0
    verb = "需要同步" if check_only else "已同步"
    for path in stale:
        print(f"- {verb}: {path}")
    return 1 if check_only else 0


if __name__ == "__main__":
    sys.exit(main())
