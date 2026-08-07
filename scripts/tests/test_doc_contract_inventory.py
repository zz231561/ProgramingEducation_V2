"""doc contract inventory 的離線回歸測試。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doc_contract_inventory import alembic_heads, api_signatures, frontend_pages


class ContractInventoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_api_signature_includes_schema_status_and_auth(self) -> None:
        routes = self.root / "backend/api/routes"
        routes.mkdir(parents=True)
        (routes / "items.py").write_text(
            """from fastapi import APIRouter, Depends
router = APIRouter(prefix='/items')
@router.post('', response_model=ItemOut, status_code=201)
async def create(body: ItemIn, user: User = Depends(require_user)) -> ItemOut:
    pass
"""
        )

        signature = api_signatures(self.root)[0]

        self.assertEqual(signature["path"], "/items")
        self.assertEqual(signature["params"], {"body": "ItemIn", "user": "User"})
        self.assertEqual(signature["response"], "ItemOut")
        self.assertEqual(signature["status"], "201")
        self.assertIn("require_user", str(signature["auth"]))

    def test_alembic_heads_supports_mixed_assignment_styles(self) -> None:
        versions = self.root / "backend/alembic/versions"
        versions.mkdir(parents=True)
        (versions / "one.py").write_text('revision: str = "one"\ndown_revision = None\n')
        (versions / "two.py").write_text('revision = "two"\ndown_revision: str = "one"\n')

        self.assertEqual(alembic_heads(self.root), {"two"})

    def test_frontend_pages_omit_route_groups(self) -> None:
        page = self.root / "web/app/(app)/teacher/page.tsx"
        page.parent.mkdir(parents=True)
        page.write_text("export default function Page() {}")

        self.assertEqual(frontend_pages(self.root), {"/teacher"})


if __name__ == "__main__":
    unittest.main()
