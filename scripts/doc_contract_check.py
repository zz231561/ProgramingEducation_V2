"""以靜態 AST 比對 API / DB 文件與後端契約。"""

from __future__ import annotations

import ast
import re
from pathlib import Path

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
API_ROW_RE = re.compile(r"\| ([A-Z /]+) \| `([^`]+)` \|")
DB_NAME_RE = re.compile(r"^([a-z][a-z_]+)(?:\s+.*)?$", re.MULTILINE)


def _constant_string(node: ast.AST | None, default: str = "") -> str:
    """讀取 AST 中的字串常數；動態值不納入可機械驗證契約。"""
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else default


def _router_prefixes(tree: ast.Module) -> dict[str, str]:
    """取得同檔各 APIRouter 變數的 prefix。"""
    prefixes: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        if not isinstance(node.value.func, ast.Name) or node.value.func.id != "APIRouter":
            continue
        prefix = next(
            (_constant_string(keyword.value) for keyword in node.value.keywords if keyword.arg == "prefix"),
            "",
        )
        for target in node.targets:
            if isinstance(target, ast.Name):
                prefixes[target.id] = prefix
    return prefixes


def actual_api_operations(root: Path) -> set[tuple[str, str]]:
    """從 route decorators 取得 (METHOD, path) inventory。"""
    operations: set[tuple[str, str]] = set()
    for path in (root / "backend/api/routes").glob("*.py"):
        tree = ast.parse(path.read_text())
        prefixes = _router_prefixes(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                method = decorator.func.attr
                owner = decorator.func.value
                if method not in HTTP_METHODS or not isinstance(owner, ast.Name) or not decorator.args:
                    continue
                route = _constant_string(decorator.args[0])
                operations.add((method.upper(), f"{prefixes.get(owner.id, '')}{route}"))
    return operations


def documented_api_operations(root: Path) -> set[tuple[str, str]]:
    """從 api-spec endpoint tables 取得 (METHOD, path) inventory。"""
    text = (root / "docs/api-spec.md").read_text()
    return {
        (method, path)
        for methods, path in API_ROW_RE.findall(text)
        for method in methods.split(" / ")
    }


def actual_model_tables(root: Path) -> set[str]:
    """從 SQLAlchemy models 的 __tablename__ 取得 table inventory。"""
    tables: set[str] = set()
    for path in (root / "backend/models").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if any(isinstance(target, ast.Name) and target.id == "__tablename__" for target in node.targets):
                name = _constant_string(node.value)
                if name:
                    tables.add(name)
    return tables


def documented_model_tables(root: Path) -> set[str]:
    """取得 db-schema code blocks 中的 table names。"""
    return set(DB_NAME_RE.findall((root / "docs/db-schema.md").read_text()))


def contract_drift(root: Path) -> tuple[list[str], list[str], list[str]]:
    """回傳缺少 API、過時 API、缺少 DB table。"""
    actual_api = actual_api_operations(root)
    documented_api = documented_api_operations(root)
    missing_api = [f"{method} {path}" for method, path in sorted(actual_api - documented_api)]
    stale_api = [f"{method} {path}" for method, path in sorted(documented_api - actual_api)]
    missing_tables = sorted(actual_model_tables(root) - documented_model_tables(root))
    return missing_api, stale_api, missing_tables
