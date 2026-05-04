"""seed concept_edges with C++ curriculum prerequisites

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-04 00:00:00.000000

對應 roadmap 2-2e Part 1：補先修/相關邊。

語意約定：source --[prerequisite]--> target = source 是 target 的先修
（讀「target 必須先學 source」）。Detail Panel 中：
  outgoing = 進階概念（這個概念之後可以學的）
  incoming = 先修概念（學這個之前要懂的）

依據：常見 C++ 教學順序（語法 → 控制流 → 函式 → 陣列指標 → 記憶體 → OOP → STL → 進階）。
數量刻意保守（23 條），避免圖譜過密；之後可依教師意見增刪。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (source_tag, target_tag, edge_type) — 順序：source 是 target 的先修
_EDGES: list[tuple[str, str, str]] = [
    # --- 入門基礎放射 ---
    ("syntax-basic", "control-flow", "prerequisite"),
    ("syntax-basic", "io-streams", "prerequisite"),
    ("syntax-basic", "function-design", "prerequisite"),
    ("syntax-basic", "arrays-strings", "prerequisite"),
    ("syntax-basic", "namespaces", "prerequisite"),
    # --- 控制流支線 ---
    ("control-flow", "recursion", "prerequisite"),
    ("control-flow", "algorithm-complexity", "prerequisite"),
    ("function-design", "recursion", "prerequisite"),
    ("function-design", "error-handling", "prerequisite"),
    # --- 記憶體支線 ---
    ("arrays-strings", "pointer-arithmetic", "prerequisite"),
    ("references", "memory-management", "prerequisite"),
    ("pointer-arithmetic", "memory-management", "prerequisite"),
    ("memory-management", "undefined-behavior", "prerequisite"),
    ("memory-management", "concurrency", "prerequisite"),
    # --- OOP 線 ---
    ("function-design", "oop-encapsulation", "prerequisite"),
    ("oop-encapsulation", "oop-inheritance", "prerequisite"),
    ("oop-inheritance", "oop-polymorphism", "prerequisite"),
    ("oop-polymorphism", "template-meta", "prerequisite"),
    # --- STL 線 ---
    ("arrays-strings", "stl-containers", "prerequisite"),
    ("stl-containers", "stl-algorithms", "prerequisite"),
    # --- 跨支線「相關」邊（沒有先後關係但概念相關）---
    ("recursion", "algorithm-complexity", "related"),
    ("references", "pointer-arithmetic", "related"),
    ("template-meta", "stl-algorithms", "related"),
]


def upgrade() -> None:
    # 用 VALUES + JOIN concepts on tag 一次插入；gen_random_uuid() 內建於 PG 13+
    values_sql = ",\n            ".join(
        f"('{src}', '{tgt}', '{etype}')" for src, tgt, etype in _EDGES
    )
    op.execute(
        sa.text(
            f"""
            INSERT INTO concept_edges (id, source_id, target_id, edge_type)
            SELECT gen_random_uuid(), src.id, tgt.id, e.edge_type::concept_edge_type
            FROM (VALUES
                {values_sql}
            ) AS e(source_tag, target_tag, edge_type)
            JOIN concepts src ON src.tag = e.source_tag
            JOIN concepts tgt ON tgt.tag = e.target_tag
            """
        )
    )


def downgrade() -> None:
    # 只刪本 migration 種的邊（依 (source_tag, target_tag, edge_type) 三元組精準對位）
    deletes_sql = " OR ".join(
        f"(src.tag = '{src}' AND tgt.tag = '{tgt}' AND e.edge_type = '{etype}')"
        for src, tgt, etype in _EDGES
    )
    op.execute(
        sa.text(
            f"""
            DELETE FROM concept_edges e
            USING concepts src, concepts tgt
            WHERE e.source_id = src.id
              AND e.target_id = tgt.id
              AND ({deletes_sql})
            """
        )
    )
