"""教材程式碼健檢解除每日配額後的回歸測試。"""

from __future__ import annotations

import json

from scripts import snippet_check_reminder, verify_code_snippets


def test_pick_targets_allows_full_inventory() -> None:
    snippets = [(str(index), f"int main() {{ return {index}; }}") for index in range(30)]

    targets = verify_code_snippets.pick_targets(snippets, {"snippets": {}}, limit=len(snippets))

    assert targets == snippets


def test_reminder_is_quiet_after_full_clean_run(tmp_path, monkeypatch, capsys) -> None:
    state_file = tmp_path / "state.json"
    state_file.write_text(
        json.dumps(
            {
                "last_run_date": "2026-08-08",
                "remaining": 0,
                "snippets": {"one": {}},
                "runs": [{"compile_failures": 0, "static_findings": 0}],
            }
        )
    )
    monkeypatch.setattr(snippet_check_reminder, "STATE_FILE", state_file)

    snippet_check_reminder.main()

    assert capsys.readouterr().out == ""


def test_reminder_uses_full_run_wording(tmp_path, monkeypatch, capsys) -> None:
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"last_run_date": "從未", "snippets": {}, "runs": []}))
    monkeypatch.setattr(snippet_check_reminder, "STATE_FILE", state_file)

    snippet_check_reminder.main()

    output = capsys.readouterr().out
    assert "預設全量檢查" in output
    assert "每天上限" not in output
