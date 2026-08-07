"""跨平台 agent config bootstrap 測試。"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from scripts.bootstrap_agent_config import BootstrapError, bootstrap

ROOT = Path(__file__).resolve().parent.parent


def _copy_bootstrap_fixture(target: Path) -> None:
    """建立不含 credential 的最小 repository fixture。"""
    shutil.copytree(ROOT / ".agent-source", target / ".agent-source")
    (target / ".claude").mkdir()
    shutil.copy(ROOT / ".claude/settings.json", target / ".claude/settings.json")
    (target / ".codex").mkdir()
    shutil.copy(ROOT / ".codex/hooks.json", target / ".codex/hooks.json")
    (target / "scripts").mkdir()
    shutil.copy(ROOT / "scripts/sync_agents_md.py", target / "scripts/sync_agents_md.py")
    for directory in ("web", "backend", "backend/services/edf"):
        (target / directory).mkdir(parents=True, exist_ok=True)


def test_bootstrap_rebuilds_all_generated_config(tmp_path: Path) -> None:
    """首次執行可從 canonical source 重建雙端設定。"""
    _copy_bootstrap_fixture(tmp_path)

    bootstrap(tmp_path, sys.executable)

    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == (
        tmp_path / ".agent-source/guidance/project.md"
    ).read_text(encoding="utf-8")
    assert (tmp_path / "CLAUDE.md").is_file()
    assert (tmp_path / ".agents/skills/code-health/SKILL.md").is_file()
    assert (tmp_path / ".claude/skills/code-health/SKILL.md").is_file()
    assert not (tmp_path / ".claude/settings.local.json").exists()


def test_bootstrap_rejects_missing_adapter(tmp_path: Path) -> None:
    """缺少任一 lifecycle adapter 時明確失敗。"""
    _copy_bootstrap_fixture(tmp_path)
    (tmp_path / ".codex/hooks.json").unlink()

    with pytest.raises(BootstrapError, match="Missing adapter"):
        bootstrap(tmp_path, sys.executable)
