"""從 agent-neutral canonical source 產生 Claude Code 與 Codex 規則檔。

用法：``python3 scripts/sync_agents_md.py [--check]``。
``--check`` 僅檢查 drift，不寫入檔案，供 CI 與 lifecycle hook 使用。
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / ".agent-source"
GUIDANCE_SOURCE = SOURCE_DIR / "guidance/project.md"
RULES_SOURCE_DIR = SOURCE_DIR / "rules"
CLAUDE_RULES_DIR = ROOT / ".claude/rules"
GENERATED_BANNER = (
    "<!-- 由 scripts/sync_agents_md.py 自動產生，請勿直接編輯；"
    "改動請改來源檔，再重跑同步 -->\n<!-- 來源：{source} -->\n\n"
)


@dataclass(frozen=True)
class GeneratedFile:
    """一份生成檔及其預期內容。"""

    path: Path
    content: str


def _parse_args() -> argparse.Namespace:
    """解析 CLI 參數。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只檢查 drift，不寫檔")
    return parser.parse_args()


def _read_source(path: Path) -> str:
    """以 UTF-8 讀取 canonical source；缺檔時立即失敗。"""
    if not path.is_file():
        raise FileNotFoundError(f"找不到 canonical source：{path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _target_dir_from_glob(rule: Path, body: str) -> Path:
    """從單一 ``path/**`` glob 推導 Codex 巢狀 AGENTS.md 目錄。"""
    frontmatter = body.split("---", 2)
    if len(frontmatter) < 3:
        raise ValueError(f"缺少 frontmatter：{rule.relative_to(ROOT)}")

    match = re.search(r"^globs:\s*(.+)$", frontmatter[1], re.MULTILINE)
    if match is None:
        raise ValueError(f"缺少 globs：{rule.relative_to(ROOT)}")

    pattern = match.group(1).strip()
    if not pattern.endswith("/**") or any(token in pattern for token in (",", "{", "}")):
        raise ValueError(
            f"不支援的 globs（僅接受單一 path/**）：{rule.relative_to(ROOT)}: {pattern}"
        )

    relative_dir = Path(pattern.removesuffix("/**"))
    if relative_dir.is_absolute() or ".." in relative_dir.parts:
        raise ValueError(f"globs 不得超出 repository：{pattern}")

    target_dir = ROOT / relative_dir
    if not target_dir.is_dir():
        raise ValueError(f"globs 目標目錄不存在：{relative_dir}")
    return target_dir


def _generated_files() -> list[GeneratedFile]:
    """建立所有 Claude Code 與 Codex guidance 的預期輸出。"""
    project_guidance = _read_source(GUIDANCE_SOURCE)
    generated = [
        GeneratedFile(ROOT / "CLAUDE.md", project_guidance),
        GeneratedFile(ROOT / "AGENTS.md", project_guidance),
    ]

    rules = sorted(RULES_SOURCE_DIR.glob("*.md"))
    if not rules:
        raise FileNotFoundError(".agent-source/rules/ 內沒有規則檔")

    seen_targets: set[Path] = set()
    for rule in rules:
        body = _read_source(rule)
        claude_target = CLAUDE_RULES_DIR / rule.name
        codex_target = _target_dir_from_glob(rule, body) / "AGENTS.md"
        if codex_target in seen_targets:
            raise ValueError(f"多份 rule 指向同一目標：{codex_target.relative_to(ROOT)}")
        seen_targets.add(codex_target)

        generated.append(GeneratedFile(claude_target, body))
        source_label = claude_target.relative_to(ROOT)
        codex_body = GENERATED_BANNER.format(source=source_label) + body
        generated.append(GeneratedFile(codex_target, codex_body))
    return generated


def _find_drift(generated: list[GeneratedFile]) -> list[GeneratedFile]:
    """回傳不存在或內容與 canonical source 不同的生成檔。"""
    return [
        item
        for item in generated
        if not item.path.is_file()
        or item.path.read_text(encoding="utf-8") != item.content
    ]


def _write(files: list[GeneratedFile]) -> None:
    """寫入 drift 檔案，並確保目標目錄存在。"""
    for item in files:
        item.path.parent.mkdir(parents=True, exist_ok=True)
        item.path.write_text(item.content, encoding="utf-8")


def main() -> int:
    """檢查或同步所有生成檔。"""
    args = _parse_args()
    generated = _generated_files()
    drift = _find_drift(generated)

    if not drift:
        print("Claude Code / Codex guidance 全部已同步")
        return 0

    if not args.check:
        _write(drift)

    verb = "需要同步" if args.check else "已同步"
    for item in drift:
        print(f"- {verb}: {item.path.relative_to(ROOT)}")
    return 1 if args.check else 0


if __name__ == "__main__":
    raise SystemExit(main())
