"""建立 API、DB、環境與部署的靜態 contract inventories。"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
DB_TABLE_RE = re.compile(r"^([a-z][a-z_]+)(?:\s+.*)?$")
DB_COLUMN_RE = re.compile(r"^[├└]── ([a-z][a-z0-9_]*)")
ENV_RE = re.compile(r"^#?\s*([A-Z][A-Z0-9_]*)=", re.MULTILINE)


def _string(node: ast.AST | None, default: str = "") -> str:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else default


def _router_prefixes(tree: ast.Module) -> dict[str, str]:
    prefixes: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        if not isinstance(node.value.func, ast.Name) or node.value.func.id != "APIRouter":
            continue
        prefix = next((_string(k.value) for k in node.value.keywords if k.arg == "prefix"), "")
        for target in node.targets:
            if isinstance(target, ast.Name):
                prefixes[target.id] = prefix
    return prefixes


def api_signatures(root: Path) -> list[dict[str, object]]:
    """擷取會改變 OpenAPI / auth 契約的 route signature。"""
    signatures: list[dict[str, object]] = []
    for path in sorted((root / "backend/api/routes").glob("*.py")):
        tree = ast.parse(path.read_text())
        prefixes = _router_prefixes(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            params = {
                arg.arg: ast.unparse(arg.annotation)
                for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
                if arg.annotation is not None and arg.arg not in {"request", "db", "current_user"}
            }
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                owner = decorator.func.value
                method = decorator.func.attr
                if method not in HTTP_METHODS or not isinstance(owner, ast.Name) or not decorator.args:
                    continue
                kwargs = {k.arg: ast.unparse(k.value) for k in decorator.keywords if k.arg}
                dependency_text = " ".join(
                    [
                        *kwargs.get("dependencies", "").split(),
                        *(ast.unparse(d) for d in (*node.args.defaults, *node.args.kw_defaults) if d),
                    ]
                )
                signatures.append(
                    {
                        "method": method.upper(),
                        "path": f"{prefixes.get(owner.id, '')}{_string(decorator.args[0])}",
                        "params": params,
                        "response": kwargs.get("response_model", ""),
                        "status": kwargs.get("status_code", "200"),
                        "auth": "public" if method == "get" and _string(decorator.args[0]) == "/health" else dependency_text,
                    }
                )
    return sorted(signatures, key=lambda item: (str(item["path"]), str(item["method"])))


def api_signature_digest(root: Path) -> str:
    payload = json.dumps(api_signatures(root), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def model_columns(root: Path) -> dict[str, set[str]]:
    """從 declarative models 取得 table → mapped columns。"""
    inventory: dict[str, set[str]] = {}
    for path in (root / "backend/models").glob("*.py"):
        tree = ast.parse(path.read_text())
        for cls in (node for node in tree.body if isinstance(node, ast.ClassDef)):
            table = next(
                (_string(node.value) for node in cls.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__tablename__" for t in node.targets)),
                "",
            )
            if not table:
                continue
            inventory[table] = {
                node.target.id
                for node in cls.body
                if isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "mapped_column"
            }
    return inventory


def db_signature_digest(root: Path) -> str:
    """雜湊 column type/options、FK、index、unique 與 check constraints。"""
    signatures: list[dict[str, object]] = []
    for path in sorted((root / "backend/models").glob("*.py")):
        tree = ast.parse(path.read_text())
        for cls in (node for node in tree.body if isinstance(node, ast.ClassDef)):
            table = next(
                (_string(node.value) for node in cls.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__tablename__" for t in node.targets)),
                "",
            )
            if not table:
                continue
            fields = {
                node.target.id: {"type": ast.unparse(node.annotation), "column": ast.unparse(node.value)}
                for node in cls.body
                if isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "mapped_column"
            }
            table_args = [
                ast.unparse(node.value)
                for node in cls.body
                if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "__table_args__" for target in node.targets)
            ]
            signatures.append({"table": table, "fields": fields, "table_args": table_args})
    payload = json.dumps(signatures, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def alembic_heads(root: Path) -> set[str]:
    """靜態解析 revision graph，回傳沒有 child 的 heads。"""
    revisions: dict[str, str | None] = {}
    for path in (root / "backend/alembic/versions").glob("*.py"):
        tree = ast.parse(path.read_text())
        values: dict[str, str] = {}
        for node in tree.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                values[node.target.id] = _string(node.value)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        values[target.id] = _string(node.value)
        if values.get("revision"):
            revisions[values["revision"]] = values.get("down_revision") or None
    parents = {parent for parent in revisions.values() if parent}
    return set(revisions) - parents


def documented_columns(root: Path) -> dict[str, set[str]]:
    inventory: dict[str, set[str]] = {}
    current = ""
    for line in (root / "docs/db-schema.md").read_text().splitlines():
        table_match = DB_TABLE_RE.fullmatch(line)
        if table_match:
            current = table_match.group(1)
            inventory.setdefault(current, set())
            continue
        column_match = DB_COLUMN_RE.match(line)
        if current and column_match:
            inventory[current].add(column_match.group(1))
    return inventory


def settings_names(root: Path) -> set[str]:
    tree = ast.parse((root / "backend/core/config.py").read_text())
    settings = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Settings")
    return {
        node.target.id
        for node in settings.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id.isupper()
    }


def env_example_names(root: Path) -> set[str]:
    return set(ENV_RE.findall((root / "backend/.env.example").read_text()))


def frontend_pages(root: Path) -> set[str]:
    pages: set[str] = set()
    for path in (root / "web/app").glob("**/page.tsx"):
        parts = [part for part in path.relative_to(root / "web/app").parts[:-1] if not part.startswith("(")]
        pages.add("/" + "/".join(parts))
    return pages


def zeabur_services(root: Path) -> set[str]:
    data = json.loads((root / "zeabur.json").read_text())
    return {service["id"] for service in data["services"]}


if __name__ == "__main__":
    print(api_signature_digest(Path(__file__).resolve().parent.parent))
