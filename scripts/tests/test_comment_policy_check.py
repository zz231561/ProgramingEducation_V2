"""comment policy checker 離線回歸測試。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from comment_policy_check import check_file


class CommentPolicyTest(unittest.TestCase):
    def _check(self, suffix: str, source: str) -> set[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"sample{suffix}"
            path.write_text(source, encoding="utf-8")
            return {item.code for item in check_file(path)}

    def test_accepts_design_reason_contract_and_tracked_todo(self) -> None:
        source = """# 保留 fallback，避免外部服務故障時中斷學生流程。
# TODO(#123): 移除舊格式相容層。
def run() -> None:
    pass
"""
        self.assertEqual(self._check(".py", source), set())

    def test_rejects_python_policy_violations_but_ignores_strings(self) -> None:
        source = '''"""Module added in roadmap 7-D7."""
# Phase 4 再處理。
# === Schemas ===
# TODO: 之後修。
value = "# roadmap 7-D7"
result = call()  # type: ignore[arg-type]
'''
        self.assertEqual(self._check(".py", source), {"CP001", "CP002", "CP003", "CP004"})

    def test_domain_todo_inside_docstring_is_not_action_item(self) -> None:
        source = '''"""要求模型輸出保留 TODO 的程式碼片段。"""
'''
        self.assertEqual(self._check(".py", source), set())

    def test_rejects_typescript_policy_violations_but_ignores_strings(self) -> None:
        source = '''const label = "// Phase 2";
// roadmap 7-D7 新增
// eslint-disable-next-line react-hooks/set-state-in-effect
setReady(true);
'''
        self.assertEqual(self._check(".tsx", source), {"CP001", "CP004"})


if __name__ == "__main__":
    unittest.main()
