"""replace linear PREREQUISITE chain with curated cross-chapter dependency DAG

Revision ID: i5d6e7f8a9b0
Revises: h4c5d6e7f8a9
Create Date: 2026-07-04 00:00:00.000000

對應 roadmap Phase 6-K K1a（功能一：跨章依賴重構多對多圖）：
- 原狀：線性鏈 1→2→...→62 共 61 條邊 — 無法表達真實概念依賴
  （例：47 遞迴實際依賴 37 參數 + 38 回傳值 + 25 if-else，而非 46 函式多載）
- 新狀：curated 依賴 map（每 concept 1-3 個「真實直接前置」）共 89 條多對多邊
- 無環保證：所有邊 source.video_order < target.video_order（課程順序即拓撲序）
- 連通保證：除 video 1 外每個 concept 至少 1 條入邊 → 拓撲排序仍覆蓋全部節點
- 依賴判斷依據：概念內容的教學相依性（C++ 課綱慣例）+ 6-1e RAG 字幕輔助
  （2026-07-04 已決議移除教授人工標註，由 AI curated + K1c 自行驗證）

downgrade：還原線性鏈 61 條。
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "i5d6e7f8a9b0"
down_revision: Union[str, Sequence[str], None] = "h4c5d6e7f8a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# curated 依賴 map：{target_video_order: [source_video_orders]}
# 語意：學 target 前需先學 sources（sources 是 target 的直接 prerequisite）
_PREREQ_MAP: dict[int, list[int]] = {
    # --- 課程介紹 (1-3) + 入門 (4-7) ---
    2: [1], 3: [2], 4: [3], 5: [4],
    6: [5], 7: [5], 8: [5],
    # --- 變數與型別 (8-14) ---
    9: [8], 10: [8], 11: [9], 12: [10], 13: [9], 14: [9],
    # --- 運算子 (15-24) ---
    15: [6, 8],       # 四則運算需要 I/O 顯示結果 + 變數
    16: [15], 17: [15], 18: [15], 19: [18],
    20: [9, 15],      # 位元運算需理解型別底層
    21: [8, 15], 22: [21],
    23: [15, 19, 21], # 優先順序綜合算術/邏輯/指定
    24: [23],
    # --- 流程控制 (25-28) ---
    25: [18, 19],     # if-else 需要比較 + 邏輯運算子
    26: [25], 27: [25], 28: [25],
    # --- 迴圈 (29-35) ---
    29: [17, 25],     # for 需要遞增遞減 + 條件判斷
    30: [25], 31: [30],
    32: [29, 30], 33: [30], 34: [29, 30], 35: [25],
    # --- 函式 (36-47) ---
    36: [5, 8],       # 函式需要語法結構 + 變數
    37: [36], 38: [36],
    39: [8, 36], 40: [39], 41: [40],
    42: [37, 38],
    43: [12, 36],     # 巨集函式需要巨集常數概念
    44: [37, 38], 45: [37, 38], 46: [37, 38],
    47: [25, 37, 38], # 遞迴 = 函式參數/回傳 + 終止條件（if-else）
    # --- 陣列 (48-50) ---
    48: [8, 29],      # 陣列操作依賴 for 迴圈
    49: [48],
    50: [32, 48],     # 多維陣列需要巢狀迴圈
    # --- 指標與記憶體 (51-58) ---
    51: [8, 9],       # 指標需理解變數 + 型別大小
    52: [48, 51],     # 指標與陣列（tech-debt 原例）
    53: [52], 54: [51], 55: [51],
    56: [37, 51], 57: [37, 55],
    58: [49, 52],     # main 參數 = char* argv[]（字元陣列 + 指標與陣列）
    # --- 物件導向 (59-62) ---
    59: [8, 36],      # 類別 = 資料成員（變數）+ 成員函式（函式）
    60: [37, 59],
    61: [11, 59],     # 常數成員需要唯讀變數概念
    62: [40, 59],     # 靜態成員的生命週期類比全域變數
}

_EDGES_TABLE = sa.table(
    "concept_edges",
    sa.column("id", sa.UUID()),
    sa.column("source_id", sa.UUID()),
    sa.column("target_id", sa.UUID()),
    sa.column("edge_type", sa.Enum(
        "prerequisite", "contains", "specialization", "related",
        name="concept_edge_type",
        create_type=False,
    )),
    sa.column("weight", sa.Float()),
)


def _load_order_to_id() -> dict[int, str]:
    """查 DB 建 video_order → concept_id 對照；缺影片時對應邊會被跳過（防呆）。"""
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, video_order FROM concepts WHERE video_order IS NOT NULL")
    )
    return {row.video_order: str(row.id) for row in rows}


def _insert_edges(pairs: list[tuple[int, int]]) -> None:
    """以 (source_order, target_order) 列表 bulk insert PREREQUISITE 邊。"""
    order_to_id = _load_order_to_id()
    records = [
        {
            "id": str(uuid.uuid4()),
            "source_id": order_to_id[src],
            "target_id": order_to_id[tgt],
            "edge_type": "prerequisite",
            "weight": 1.0,
        }
        for src, tgt in pairs
        if src in order_to_id and tgt in order_to_id
    ]
    if records:
        op.bulk_insert(_EDGES_TABLE, records)


def upgrade() -> None:
    """清空線性鏈，seed curated 多對多 DAG（89 條）。"""
    op.execute("DELETE FROM concept_edges WHERE edge_type = 'prerequisite'")
    pairs = [
        (src, tgt) for tgt, sources in _PREREQ_MAP.items() for src in sources
    ]
    _insert_edges(pairs)


def downgrade() -> None:
    """還原線性鏈 1→2→...→62（61 條）。"""
    op.execute("DELETE FROM concept_edges WHERE edge_type = 'prerequisite'")
    pairs = [(n, n + 1) for n in range(1, 62)]
    _insert_edges(pairs)
