"""seed C++ curriculum: 59 video concepts + linear PREREQUISITE chain

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-05-05 00:00:00.000000

對應 Phase 3-1c+ 教授課程整合：62 部 C++ YT 影片中，排除 01-03（甚麼是程式語言/
C++簡介/安裝 DevC++）共 3 部介紹影片 → 剩 04-62 共 59 部 = 59 個 concept node。

⚠ DESTRUCTIVE：本 migration 會**清空**所有現有 concepts、concept_edges、
   student_mastery、learning_paths、learning_units 資料，再 seed 新內容。
   - 開發環境：dev DB 重跑無妨，已商定完全替換 V1 20 個 EDF concept
   - 生產環境：上線前若有真實學生資料，須備份；目前尚未上線
   - 連動：student_mastery 因 FK CASCADE 會被清；learning_units RESTRICT 須先手動清

設計：
- tag 命名：`cpp-NN-keyword`（NN 為兩位數編號，方便排序與識別）
- 主題分類（8 個 category，中文）：入門 / 變數與型別 / 運算子 / 流程控制 / 迴圈 /
  函式 / 陣列 / 指標與記憶體 / 物件導向
- difficulty_level：依教學順序漸進（1-5）
- video_order = 編號（04-62）
- video_youtube_id / video_duration_seconds：P1 階段先 NULL，等教授補後 PATCH
- PREREQUISITE 邊：純線性鏈（04→05→...→61→62 共 58 條）；跨章節依賴（如 47 遞迴 ←
  29 for 迴圈）由教授後續標註再 seed
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "d0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (order, tag_suffix, name_zh, name_en, difficulty, category)
_CONCEPTS_DATA: list[tuple[int, str, str, str, int, str]] = [
    # --- 入門 (04-07) ---
    (4, "first-program", "撰寫第一個C++程式", "First C++ Program", 1, "入門"),
    (5, "syntax", "C++程式的組成及語法規則", "C++ Program Structure", 1, "入門"),
    (6, "io", "C++的輸出與輸入", "C++ I/O", 1, "入門"),
    (7, "style", "良好的程式撰寫習慣", "Coding Style", 1, "入門"),
    # --- 變數與型別 (08-14) ---
    (8, "variables", "C++的變數", "Variables", 1, "變數與型別"),
    (9, "types-sizeof", "C++的資料型態與sizeof()", "Data Types & sizeof", 1, "變數與型別"),
    (10, "literals", "字面常數", "Literal Constants", 2, "變數與型別"),
    (11, "readonly-vars", "唯讀變數", "Read-only Variables", 2, "變數與型別"),
    (12, "macro-constants", "巨集常數", "Macro Constants", 2, "變數與型別"),
    (13, "enum", "以enum定義列舉型別", "Enum Types", 2, "變數與型別"),
    (14, "typedef", "利用typedef為型別定義別名", "Typedef", 2, "變數與型別"),
    # --- 運算子 (15-24) ---
    (15, "arithmetic", "C++的四則運算", "Arithmetic Operators", 2, "運算子"),
    (16, "modulo", "C++的餘數運算子", "Modulo Operator", 2, "運算子"),
    (17, "incr-decr", "C++的遞增遞減運算子", "Increment/Decrement", 2, "運算子"),
    (18, "comparison", "C++的比較運算子", "Comparison Operators", 2, "運算子"),
    (19, "logical", "C++的邏輯運算子", "Logical Operators", 2, "運算子"),
    (20, "bitwise", "C++的位元運算子", "Bitwise Operators", 2, "運算子"),
    (21, "assignment", "C++的指定運算子", "Assignment Operator", 2, "運算子"),
    (22, "compound-assign", "C++的複合運算子", "Compound Assignment", 2, "運算子"),
    (23, "precedence", "C++運算子的優先順序", "Operator Precedence", 3, "運算子"),
    (24, "expr-rules", "C++運算式的運算規則", "Expression Rules", 3, "運算子"),
    # --- 流程控制 (25-28) ---
    (25, "if-else", "C++的流程控制：if-else", "If-Else", 2, "流程控制"),
    (26, "nested-if", "C++的流程控制：巢狀if-else", "Nested If-Else", 2, "流程控制"),
    (27, "ternary", "C++的條件運算子", "Conditional Operator", 2, "流程控制"),
    (28, "switch", "C++的switch多條件分支", "Switch", 2, "流程控制"),
    # --- 迴圈 (29-35) ---
    (29, "for", "C++的for迴圈", "For Loop", 2, "迴圈"),
    (30, "while", "C++的while迴圈", "While Loop", 2, "迴圈"),
    (31, "do-while", "C++的do-while迴圈", "Do-While Loop", 2, "迴圈"),
    (32, "nested-loop", "C++的巢狀迴圈", "Nested Loops", 3, "迴圈"),
    (33, "infinite-loop", "C++的無窮迴圈", "Infinite Loop", 3, "迴圈"),
    (34, "break-continue", "C++的break與continue", "Break & Continue", 3, "迴圈"),
    (35, "goto", "C++的強制性流程控制goto", "Goto", 3, "迴圈"),
    # --- 函式 (36-47) ---
    (36, "functions", "C++的函式", "Functions", 2, "函式"),
    (37, "func-params", "C++帶有參數的函式", "Function Parameters", 2, "函式"),
    (38, "func-return", "C++函式的回傳值", "Function Return Values", 2, "函式"),
    (39, "local-vars", "C++的局部變數", "Local Variables", 3, "函式"),
    (40, "global-vars", "C++的全域變數", "Global Variables", 3, "函式"),
    (41, "extern-vars", "C++的外部變數", "Extern Variables", 3, "函式"),
    (42, "inline-func", "C++的行內函式", "Inline Functions", 3, "函式"),
    (43, "macro-func", "C++的巨集函式", "Macro Functions", 3, "函式"),
    (44, "math-lib", "C++標準函式庫之數學函式", "Math Library", 3, "函式"),
    (45, "time-lib", "C++標準函式庫之時間函式", "Time Library", 3, "函式"),
    (46, "func-overload", "C++的函式多載", "Function Overloading", 3, "函式"),
    (47, "recursion", "C++的遞迴函式", "Recursive Functions", 4, "函式"),
    # --- 陣列 (48-50) ---
    (48, "arrays", "C++的陣列", "Arrays", 3, "陣列"),
    (49, "char-arrays", "C++的字元陣列", "Character Arrays", 3, "陣列"),
    (50, "multidim-arrays", "C++的多維陣列", "Multidimensional Arrays", 4, "陣列"),
    # --- 指標與記憶體 (51-58) ---
    (51, "ptr-ref", "C++的指標與參照", "Pointers & References", 4, "指標與記憶體"),
    (52, "ptr-array", "C++的指標與陣列", "Pointers & Arrays", 4, "指標與記憶體"),
    (53, "ptr-arrays", "C++的指標陣列", "Pointer Arrays", 4, "指標與記憶體"),
    (54, "dynamic-mem", "C++的動態記憶體配置", "Dynamic Memory Allocation", 5, "指標與記憶體"),
    (55, "ref-vars", "C++參考型別變數與別名", "Reference Variables", 4, "指標與記憶體"),
    (56, "pass-addr", "C++的傳址呼叫", "Pass by Address", 4, "指標與記憶體"),
    (57, "pass-ref", "C++的傳參考呼叫", "Pass by Reference", 4, "指標與記憶體"),
    (58, "main-args", "C++main函式的參數", "Main Function Arguments", 4, "指標與記憶體"),
    # --- 物件導向 (59-62) ---
    (59, "oop-class", "C++的物件導向與類別", "OOP & Classes", 4, "物件導向"),
    (60, "member-functions", "C++類別的成員函式", "Member Functions", 4, "物件導向"),
    (61, "const-members", "C++類別的常數資料成員", "Const Members", 5, "物件導向"),
    (62, "static-members", "C++類別的靜態資料成員", "Static Members", 5, "物件導向"),
]


def upgrade() -> None:
    # ⚠ DESTRUCTIVE — 清空相關資料表（FK 連動考量：先清子表，再清父表）
    op.execute("DELETE FROM learning_units")     # FK ondelete=RESTRICT 必須先清
    op.execute("DELETE FROM learning_paths")     # 順帶清，避免 orphan
    op.execute("DELETE FROM concept_edges")      # FK ondelete=CASCADE 但保險先清
    op.execute("DELETE FROM student_mastery")    # FK ondelete=CASCADE 但保險先清
    op.execute("DELETE FROM concepts")

    # 預先生成 UUID（同一 transaction 內穩定）
    concept_records = []
    order_to_id: dict[int, str] = {}
    for order, suffix, name_zh, name_en, difficulty, category in _CONCEPTS_DATA:
        concept_id = str(uuid.uuid4())
        order_to_id[order] = concept_id
        concept_records.append({
            "id": concept_id,
            "tag": f"cpp-{order:02d}-{suffix}",
            "name_zh": name_zh,
            "name_en": name_en,
            "description": "",
            "difficulty_level": difficulty,
            "category": category,
            "video_youtube_id": None,
            "video_duration_seconds": None,
            "video_order": order,
        })

    # bulk_insert concepts
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
    op.bulk_insert(concepts_table, concept_records)

    # 線性 PREREQUISITE 鏈：04→05, 05→06, ..., 61→62（58 條邊）
    edge_records = []
    sorted_orders = sorted(order_to_id.keys())
    for src_order, tgt_order in zip(sorted_orders, sorted_orders[1:]):
        edge_records.append({
            "id": str(uuid.uuid4()),
            "source_id": order_to_id[src_order],
            "target_id": order_to_id[tgt_order],
            "edge_type": "prerequisite",
            "weight": 1.0,
        })

    # edge_type 是 PG ENUM `concept_edge_type`，不能從 VARCHAR 隱式轉型
    # → 用 sa.Enum 顯式宣告（create_type=False 避免 alembic 嘗試 CREATE TYPE）
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
    # 把 video concept 反向清除；不還原 V1 20 個 EDF concept（已正式停用）
    op.execute("DELETE FROM concept_edges WHERE edge_type = 'prerequisite'")
    op.execute(
        "DELETE FROM concepts WHERE video_order IS NOT NULL"
    )
