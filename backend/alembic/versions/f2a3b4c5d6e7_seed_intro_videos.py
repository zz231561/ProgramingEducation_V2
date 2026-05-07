"""seed video_order 1-3 intro concepts (course intro / install / language overview)

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-05-07 00:00:00.000000

Phase 6-1c：把原 e1f2a3b4c5d6 排除的 3 部介紹影片補回為 concept node：
- video_order 1：甚麼是程式語言
- video_order 2：C++程式語言簡介
- video_order 3：如何下戴和安裝DevC++

設計：
- category="課程介紹" → learning_path generator 會自動 filter 這個 category 不進路徑
  （見 services/learning/generator.py EXCLUDED_FROM_PATH_CATEGORIES）
- 知識圖譜頁仍會顯示這 3 節點（不受 path filter 影響）
- **不**為 1-3 加 PREREQUISITE 邊（保持 isolated；前後彼此沒有強制順序，亦非後續節點先備）
- difficulty_level=1（最易）

idempotency：本 migration 為 additive；downgrade 反向 DELETE by tag。
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (order, tag_suffix, name_zh, name_en)
_INTRO_CONCEPTS: list[tuple[int, str, str, str]] = [
    (1, "language-intro", "甚麼是程式語言", "What is a Programming Language"),
    (2, "cpp-overview", "C++程式語言簡介", "C++ Language Overview"),
    (3, "devcpp-install", "如何下戴和安裝DevC++", "Install DevC++"),
]

_INTRO_CATEGORY = "課程介紹"
_INTRO_DIFFICULTY = 1


def upgrade() -> None:
    """INSERT video_order 1-3 三筆 concept，無 PREREQUISITE 邊。"""
    records = [
        {
            "id": str(uuid.uuid4()),
            "tag": f"cpp-{order:02d}-{suffix}",
            "name_zh": name_zh,
            "name_en": name_en,
            "description": "",
            "difficulty_level": _INTRO_DIFFICULTY,
            "category": _INTRO_CATEGORY,
            "video_youtube_id": None,
            "video_duration_seconds": None,
            "video_order": order,
        }
        for order, suffix, name_zh, name_en in _INTRO_CONCEPTS
    ]

    concepts_table = sa.table(
        "concepts",
        sa.column("id", sa.UUID()),
        sa.column("tag", sa.String()),
        sa.column("name_zh", sa.String()),
        sa.column("name_en", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("difficulty_level", sa.Integer()),
        sa.column("category", sa.String()),
        sa.column("video_youtube_id", sa.String()),
        sa.column("video_duration_seconds", sa.Integer()),
        sa.column("video_order", sa.Integer()),
    )
    op.bulk_insert(concepts_table, records)


def downgrade() -> None:
    """DELETE 3 個介紹 concept（by tag 精確匹配）。"""
    tags = [f"cpp-{order:02d}-{suffix}" for order, suffix, *_ in _INTRO_CONCEPTS]
    op.execute(
        sa.text(
            "DELETE FROM concepts WHERE tag IN :tags"
        ).bindparams(sa.bindparam("tags", expanding=True))
        .params(tags=tags)
    )
