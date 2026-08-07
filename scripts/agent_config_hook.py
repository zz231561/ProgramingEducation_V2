"""Claude Code 與 Codex 共用的 agent config lifecycle hook。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / ".agent-source"
SYNC_SCRIPT = ROOT / "scripts/sync_agents_md.py"
GENERATED_DIRS = (
    ROOT / ".claude/rules",
    ROOT / ".claude/skills",
    ROOT / ".agents/skills",
)
PATCH_PATH_PATTERN = re.compile(
    r"^\*\*\* (?:Update File|Add File|Delete File|Move to): (.+)$",
    re.MULTILINE,
)


def _parse_args() -> argparse.Namespace:
    """解析 hook mode。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("check", "guard-generated", "sync-after-edit"),
    )
    return parser.parse_args()


def _read_payload() -> dict[str, Any]:
    """讀取 lifecycle hook 傳入的 JSON；無 stdin 時視為空事件。"""
    if sys.stdin.isatty():
        return {}
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise TypeError("hook payload 必須是 JSON object")
    return payload


def _is_within(path: Path, directory: Path) -> bool:
    """判斷路徑是否位於指定目錄內，支援 Python 3.9。"""
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True


def _resolve_path(raw_path: str, payload: dict[str, Any]) -> Path:
    """依 hook cwd 將工具輸入正規化為絕對路徑。"""
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    cwd = Path(str(payload.get("cwd") or ROOT))
    return (cwd / path).resolve()


def _extract_paths(payload: dict[str, Any]) -> set[Path]:
    """同時解析 Claude file_path 與 Codex apply_patch command。"""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return set()

    raw_paths: set[str] = set()
    for key in ("file_path", "path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            raw_paths.add(value.strip())

    command = tool_input.get("command")
    if isinstance(command, str):
        raw_paths.update(match.strip() for match in PATCH_PATH_PATTERN.findall(command))
    return {_resolve_path(raw_path, payload) for raw_path in raw_paths}


def _is_generated(path: Path) -> bool:
    """辨識同步器管理的 generated guidance、rules 與 skills。"""
    if path in (ROOT / "CLAUDE.md", ROOT / "AGENTS.md"):
        return True
    if path.name == "AGENTS.md" and _is_within(path, ROOT):
        return True
    return any(_is_within(path, directory) for directory in GENERATED_DIRS)


def _run_sync(check_only: bool) -> int:
    """使用目前 Python interpreter 執行同步器。"""
    command = [sys.executable, str(SYNC_SCRIPT)]
    if check_only:
        command.append("--check")
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    output = result.stdout if result.returncode == 0 else result.stdout + result.stderr
    if output:
        stream = sys.stdout if result.returncode == 0 else sys.stderr
        stream.write(output)
    return result.returncode


def _guard_generated(payload: dict[str, Any]) -> int:
    """阻止 Edit/Write/apply_patch 直接修改 generated files。"""
    generated = sorted(path for path in _extract_paths(payload) if _is_generated(path))
    if not generated:
        return 0

    paths = ", ".join(str(path.relative_to(ROOT)) for path in generated)
    sys.stderr.write(
        f"禁止直接修改 generated file：{paths}。請改 .agent-source/ 後執行同步。\n"
    )
    return 2


def _sync_after_edit(payload: dict[str, Any]) -> int:
    """canonical source 被修改後才執行同步，避免每次工具呼叫都寫檔。"""
    if not any(_is_within(path, SOURCE_DIR) for path in _extract_paths(payload)):
        return 0
    return _run_sync(check_only=False)


def main() -> int:
    """依 lifecycle mode 執行 drift check、guard 或同步。"""
    args = _parse_args()
    if args.mode == "check":
        return _run_sync(check_only=True)

    payload = _read_payload()
    if args.mode == "guard-generated":
        return _guard_generated(payload)
    return _sync_after_edit(payload)


if __name__ == "__main__":
    raise SystemExit(main())
