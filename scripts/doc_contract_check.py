"""比對 API、DB、環境、前端頁面與部署文件契約。"""

from __future__ import annotations

import re
from pathlib import Path

from doc_contract_inventory import (
    alembic_heads,
    api_signature_digest,
    api_signatures,
    db_signature_digest,
    documented_columns,
    env_example_names,
    frontend_pages,
    model_columns,
    settings_names,
    zeabur_services,
)

API_ROW_RE = re.compile(r"\| ([A-Z /]+) \| `([^`]+)` \|")
MARKER_RE = re.compile(r"<!-- contract: ([a-z0-9-]+)=([^>]+) -->")


def _markers(root: Path) -> dict[str, str]:
    markers: dict[str, str] = {}
    for path in (root / "docs").glob("*.md"):
        markers.update((key, value.strip()) for key, value in MARKER_RE.findall(path.read_text()))
    return markers


def documented_api_operations(root: Path) -> set[tuple[str, str]]:
    text = (root / "docs/api-spec.md").read_text()
    return {(method, path) for methods, path in API_ROW_RE.findall(text) for method in methods.split(" / ")}


def contract_drift(root: Path) -> dict[str, list[str]]:
    """回傳各類契約 drift；空 list 表示一致。"""
    markers = _markers(root)
    actual_api = {(str(item["method"]), str(item["path"])) for item in api_signatures(root)}
    documented_api = documented_api_operations(root)
    actual_columns = model_columns(root)
    doc_columns = documented_columns(root)
    missing_columns = [
        f"{table}.{column}"
        for table, columns in sorted(actual_columns.items())
        for column in sorted(columns - doc_columns.get(table, set()))
    ]
    stale_columns = [
        f"{table}.{column}"
        for table, columns in sorted(doc_columns.items())
        if table in actual_columns
        for column in sorted(columns - actual_columns[table])
    ]
    expected_pages = {item for item in markers.get("frontend-pages", "").split(",") if item}
    expected_services = {item for item in markers.get("zeabur-services", "").split(",") if item}
    return {
        "api_missing": [f"{m} {p}" for m, p in sorted(actual_api - documented_api)],
        "api_stale": [f"{m} {p}" for m, p in sorted(documented_api - actual_api)],
        "api_signature": []
        if markers.get("api-signature-sha256") == api_signature_digest(root)
        else ["request/response/status/auth signature changed"],
        "db_missing": missing_columns,
        "db_stale": stale_columns,
        "db_signature": []
        if markers.get("db-signature-sha256") == db_signature_digest(root)
        else ["column type/nullability/FK/index/check signature changed"],
        "alembic_heads": []
        if markers.get("alembic-heads") == ",".join(sorted(alembic_heads(root))) and len(alembic_heads(root)) == 1
        else [f"actual={','.join(sorted(alembic_heads(root)))}"],
        "env_missing": sorted(settings_names(root) - env_example_names(root)),
        "frontend_missing": sorted(frontend_pages(root) - expected_pages),
        "frontend_stale": sorted(expected_pages - frontend_pages(root)),
        "services_missing": sorted(zeabur_services(root) - expected_services),
        "services_stale": sorted(expected_services - zeabur_services(root)),
    }
