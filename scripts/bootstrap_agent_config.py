"""重建並驗證 Claude Code / Codex 專案設定，不處理 credential。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
HOOK_MODES = ("check", "guard-generated", "sync-after-edit")


class BootstrapError(RuntimeError):
    """表示 agent config 無法安全重建。"""


def _collect_commands(value: Any, key: str) -> list[str]:
    """遞迴收集 adapter JSON 內指定 command 欄位。"""
    if isinstance(value, dict):
        commands = [value[key]] if isinstance(value.get(key), str) else []
        return commands + [
            command
            for child in value.values()
            for command in _collect_commands(child, key)
        ]
    if isinstance(value, list):
        return [command for child in value for command in _collect_commands(child, key)]
    return []


def _load_json(path: Path) -> dict[str, Any]:
    """讀取並驗證 JSON object。"""
    if not path.is_file():
        raise BootstrapError(f"Missing adapter: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BootstrapError(f"Adapter must be a JSON object: {path}")
    return data


def _validate_commands(commands: list[str], label: str) -> None:
    """確認三種 lifecycle mode 都已接線。"""
    normalized = [command.replace("\\", "/") for command in commands]
    for mode in HOOK_MODES:
        if not any(f"scripts/agent_config_hook.py\" {mode}" in command for command in normalized):
            raise BootstrapError(f"{label} missing lifecycle mode: {mode}")


def _validate_adapters(root: Path) -> None:
    """驗證兩端 adapter 與 Windows 原生命令。"""
    claude = _load_json(root / ".claude/settings.json")
    codex = _load_json(root / ".codex/hooks.json")
    _validate_commands(_collect_commands(claude, "command"), "Claude Code")
    _validate_commands(_collect_commands(codex, "command"), "Codex")

    windows_commands = _collect_commands(codex, "commandWindows")
    _validate_commands(windows_commands, "Codex Windows")
    if any("$(" in command for command in windows_commands):
        raise BootstrapError("Codex Windows command contains Unix command substitution")


def _run_sync(root: Path, executable: str) -> None:
    """使用目前 Python 重建 generated config，並以 check mode 複驗。"""
    script = root / "scripts/sync_agents_md.py"
    if not script.is_file():
        raise BootstrapError(f"Missing sync script: {script}")
    for arguments in ([executable, str(script)], [executable, str(script), "--check"]):
        result = subprocess.run(arguments, cwd=root, check=False)
        if result.returncode != 0:
            raise BootstrapError(f"Agent config sync failed with exit code {result.returncode}")


def bootstrap(root: Path = ROOT, executable: str = sys.executable) -> None:
    """執行可重複的 agent config bootstrap。"""
    _validate_adapters(root)
    _run_sync(root, executable)
    print("Agent config bootstrap complete (credentials unchanged)")


def main() -> int:
    """CLI entry point。"""
    try:
        bootstrap()
    except (BootstrapError, json.JSONDecodeError, OSError) as error:
        print(f"Agent config bootstrap failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
