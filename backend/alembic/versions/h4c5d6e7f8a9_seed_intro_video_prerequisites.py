"""seed PREREQUISITE edges for intro videos (1→2→3→4)

Revision ID: h4c5d6e7f8a9
Revises: g3b4c5d6e7f8
Create Date: 2026-05-22 00:00:00.000000

設計反轉（2026-05-22）：原 6-1c 把 video_order 1-3 列為「課程介紹」且不進學習路徑；
使用者決定把 1-3 加回學習路徑（線性教學上 1=語言介紹/2=C++ 概述/3=DevC++ 安裝
應排在 video 4「撰寫第一個 C++ 程式」之前）。

做法：
- 補 3 條 PREREQUISITE 邊 1→2, 2→3, 3→4 → 路徑必為 1,2,3,4,...,62
- 保留 1-3 的 category="課程介紹"（未來知識圖譜可用此 styling 區分）
- 移除 generator.py / batch_generator.py 的 EXCLUDED_FROM_PATH_CATEGORIES 過濾（程式碼變更同 commit）

idempotency：upgrade 為 additive；downgrade 精確 DELETE 這 3 條邊。
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h4c5d6e7f8a9"
down_revision: Union[str, Sequence[str], None] = "g3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (source_tag, target_tag) — 1→2→3→4
_INTRO_EDGES: list[tuple[str, str]] = [
    ("cpp-01-language-intro", "cpp-02-cpp-overview"),
    ("cpp-02-cpp-overview", "cpp-03-devcpp-install"),
    ("cpp-03-devcpp-install", "cpp-04-first-program"),
]


def upgrade() -> None:
    """補 3 條 PREREQUISITE 邊；以 tag 查 concept_id。"""
    conn = op.get_bind()
    tag_to_id: dict[str, str] = {}
    for src_tag, tgt_tag in _INTRO_EDGES:
        for tag in (src_tag, tgt_tag):
            if tag in tag_to_id:
                continue
            row = conn.execute(
                sa.text("SELECT id FROM concepts WHERE tag = :tag"),
                {"tag": tag},
            ).fetchone()
            if row is None:
                raise RuntimeError(
                    f"concept tag '{tag}' 不存在；e1f2a3b4c5d6 + f2a3b4c5d6e7 seed 是否已套用？"
                )
            tag_to_id[tag] = str(row[0])

    edge_records = [
        {
            "id": str(uuid.uuid4()),
            "source_id": tag_to_id[src_tag],
            "target_id": tag_to_id[tgt_tag],
            "edge_type": "prerequisite",
            "weight": 1.0,
        }
        for src_tag, tgt_tag in _INTRO_EDGES
    ]

    edge_type_enum = sa.Enum(
        "prerequisite", "contains", "specialization", "related",
        name="concept_edge_type",
        create_type=False,
    )
    edges_table = sa.table(
        "concept_edges",
        sa.column("id", sa.UUID()),
        sa.column("source_id", sa.UUID()),
        sa.column("target_id", sa.UUID()),
        sa.column("edge_type", edge_type_enum),
        sa.column("weight", sa.Float()),
    )
    op.bulk_insert(edges_table, edge_records)


def downgrade() -> None:
    """DELETE 這 3 條邊（by source/target tag 精確匹配）。"""
    for src_tag, tgt_tag in _INTRO_EDGES:
        op.execute(
            sa.text(
                """
                DELETE FROM concept_edges
                WHERE edge_type = 'prerequisite'
                  AND source_id = (SELECT id FROM concepts WHERE tag = :src)
                  AND target_id = (SELECT id FROM concepts WHERE tag = :tgt)
                """
            ).bindparams(sa.bindparam("src", src_tag), sa.bindparam("tgt", tgt_tag))
        )
