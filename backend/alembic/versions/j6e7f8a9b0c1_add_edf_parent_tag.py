"""add concepts.edf_parent_tag + seed EDF tag -> video concept mapping

Revision ID: j6e7f8a9b0c1
Revises: i5d6e7f8a9b0
Create Date: 2026-07-04 00:00:00.000000

對應 roadmap K2a（功能二：動態知識狀態追蹤）：
- 背景：Phase 3-1c+ 把 concepts 換成 62 影片 concept 後，EDF Chat 的 20 粗
  ConceptTag 在 concepts 表找不到對應 → Workspace 對話不再驅動 BKT
  （tech-debt「EDF Mastery 連動暫時退場」）
- 解法：concepts 加 edf_parent_tag 欄位，seed 粗 tag → 影片 concept 群組對映；
  update_mastery 以三層 fan-out 解析（直接命中 → 已曝光組員 → 組內入門 concept）
- 覆蓋：20 個 EDF tag 中 10 個有課綱對應；其餘（STL / template / concurrency 等
  進階主題）課綱未涵蓋，evidence 帶到時照舊跳過
- video 1-3（課程介紹）不對映（NULL）

downgrade：drop column（index 隨 column 刪除）。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "j6e7f8a9b0c1"
down_revision: Union[str, Sequence[str], None] = "i5d6e7f8a9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# {edf_tag: [video_orders]} — 依課綱章節語意對映
_MAPPING: dict[str, list[int]] = {
    # 入門 + 變數與型別 + 運算子（6 io 除外）
    "syntax-basic": [4, 5, 7, 8, 9, 10, 11, 12, 13, 14,
                     15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
    "io-streams": [6],
    "control-flow": list(range(25, 36)),        # 流程控制 + 迴圈
    "function-design": list(range(36, 47)),     # 函式（47 遞迴獨立對映）
    "recursion": [47],
    "arrays-strings": [48, 49, 50],
    "pointer-arithmetic": [51, 52, 53, 56, 58], # 含傳址呼叫 + main 參數（argv）
    "memory-management": [54],
    "references": [55, 57],                     # 參考變數 + 傳參考呼叫
    "oop-encapsulation": [59, 60, 61, 62],
}


def upgrade() -> None:
    op.add_column(
        "concepts",
        sa.Column("edf_parent_tag", sa.String(50), nullable=True),
    )
    op.create_index("ix_concepts_edf_parent_tag", "concepts", ["edf_parent_tag"])

    conn = op.get_bind()
    for edf_tag, orders in _MAPPING.items():
        conn.execute(
            sa.text(
                "UPDATE concepts SET edf_parent_tag = :tag "
                "WHERE video_order IN :orders"
            ).bindparams(
                sa.bindparam("tag"),
                sa.bindparam("orders", expanding=True),
            ),
            {"tag": edf_tag, "orders": orders},
        )


def downgrade() -> None:
    op.drop_index("ix_concepts_edf_parent_tag", table_name="concepts")
    op.drop_column("concepts", "edf_parent_tag")
