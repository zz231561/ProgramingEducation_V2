"""create concepts + concept_edges tables and seed 20 ConceptTags

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-04 00:00:00.000000

對應 roadmap 2-2a：知識圖譜 schema 初始化。
- 建立 concepts 表（節點）：對應 EDF ConceptTag enum 的 20 個概念
- 建立 concept_edges 表（邊）：先建 schema，邊資料留給後續任務
- 一次性 seed 20 個 ConceptTag（來源：`.claude/rules/edf-pipeline.md` ConceptTag 列表）
"""

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 邊類型 — 知識圖譜上節點關係（db-schema.md Module 5）
EDGE_TYPES = ("prerequisite", "contains", "specialization", "related")

# 20 個 ConceptTag seed 資料 — 與 backend/services/edf/models.py CONCEPT_TAGS 一致
# difficulty 1-5（學生通常接觸的難度梯度）；category 對應教學分類
_CONCEPT_SEED: list[dict] = [
    # --- 基礎語法 ---
    {"tag": "syntax-basic", "name_zh": "基礎語法", "name_en": "Basic Syntax",
     "description": "C++ 程式結構、變數宣告、型別、運算子等基本語法元素。",
     "difficulty_level": 1, "category": "基礎語法"},
    {"tag": "io-streams", "name_zh": "輸入輸出", "name_en": "I/O Streams",
     "description": "iostream 函式庫：cin / cout / 格式化輸出與輸入。",
     "difficulty_level": 1, "category": "基礎語法"},
    {"tag": "control-flow", "name_zh": "流程控制", "name_en": "Control Flow",
     "description": "if/else、switch、for、while、break/continue 等控制結構。",
     "difficulty_level": 1, "category": "基礎語法"},
    {"tag": "function-design", "name_zh": "函式設計", "name_en": "Function Design",
     "description": "函式宣告、參數傳遞、回傳值、預設參數、函式重載。",
     "difficulty_level": 2, "category": "基礎語法"},
    {"tag": "arrays-strings", "name_zh": "陣列與字串", "name_en": "Arrays & Strings",
     "description": "C-style 陣列、std::string、std::array、字串操作。",
     "difficulty_level": 2, "category": "基礎語法"},
    {"tag": "namespaces", "name_zh": "命名空間", "name_en": "Namespaces",
     "description": "namespace 機制、using 宣告、避免名稱衝突。",
     "difficulty_level": 2, "category": "基礎語法"},
    # --- 記憶體與指標 ---
    {"tag": "references", "name_zh": "參考", "name_en": "References",
     "description": "左值參考 (&)、傳參考、const 參考、與指標的差異。",
     "difficulty_level": 2, "category": "記憶體"},
    {"tag": "pointer-arithmetic", "name_zh": "指標運算", "name_en": "Pointer Arithmetic",
     "description": "指標宣告、解引用、指標算術、指標與陣列關係。",
     "difficulty_level": 3, "category": "記憶體"},
    {"tag": "memory-management", "name_zh": "記憶體管理", "name_en": "Memory Management",
     "description": "stack vs heap、new/delete、智慧指標、RAII 慣例。",
     "difficulty_level": 4, "category": "記憶體"},
    {"tag": "undefined-behavior", "name_zh": "未定義行為", "name_en": "Undefined Behavior",
     "description": "解引用 nullptr、越界存取、整數溢位等 UB 與避免方式。",
     "difficulty_level": 4, "category": "記憶體"},
    # --- 物件導向 ---
    {"tag": "oop-encapsulation", "name_zh": "封裝", "name_en": "Encapsulation",
     "description": "class / struct、成員存取控制（public/private/protected）、建構/解構子。",
     "difficulty_level": 3, "category": "物件導向"},
    {"tag": "oop-inheritance", "name_zh": "繼承", "name_en": "Inheritance",
     "description": "單一/多重繼承、存取控制、建構順序、virtual 解構子。",
     "difficulty_level": 3, "category": "物件導向"},
    {"tag": "oop-polymorphism", "name_zh": "多型", "name_en": "Polymorphism",
     "description": "virtual 函式、純虛擬函式、動態綁定、抽象類別。",
     "difficulty_level": 4, "category": "物件導向"},
    # --- STL ---
    {"tag": "stl-containers", "name_zh": "STL 容器", "name_en": "STL Containers",
     "description": "vector / map / set / list 等容器與其複雜度特性。",
     "difficulty_level": 3, "category": "STL"},
    {"tag": "stl-algorithms", "name_zh": "STL 演算法", "name_en": "STL Algorithms",
     "description": "sort / find / transform / accumulate 等泛型演算法與 iterator 範式。",
     "difficulty_level": 4, "category": "STL"},
    # --- 演算法與進階 ---
    {"tag": "recursion", "name_zh": "遞迴", "name_en": "Recursion",
     "description": "遞迴函式設計、終止條件、尾遞迴、與迴圈的取捨。",
     "difficulty_level": 3, "category": "演算法"},
    {"tag": "algorithm-complexity", "name_zh": "演算法複雜度", "name_en": "Algorithm Complexity",
     "description": "Big-O 分析、時間/空間複雜度、常見資料結構操作的複雜度。",
     "difficulty_level": 3, "category": "演算法"},
    {"tag": "error-handling", "name_zh": "錯誤處理", "name_en": "Error Handling",
     "description": "try/catch、std::exception 階層、RAII 與例外安全保證。",
     "difficulty_level": 3, "category": "進階"},
    {"tag": "template-meta", "name_zh": "模板與泛型程式設計", "name_en": "Template Metaprogramming",
     "description": "function/class template、SFINAE、constexpr、type traits。",
     "difficulty_level": 5, "category": "進階"},
    {"tag": "concurrency", "name_zh": "並行", "name_en": "Concurrency",
     "description": "std::thread、mutex、condition_variable、async/future、資料競爭。",
     "difficulty_level": 5, "category": "進階"},
]


def upgrade() -> None:
    # === concepts 表（節點）===
    concepts = op.create_table(
        "concepts",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("tag", sa.String(50), nullable=False, unique=True),
        sa.Column("name_zh", sa.String(100), nullable=False),
        sa.Column("name_en", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("difficulty_level", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "difficulty_level BETWEEN 1 AND 5", name="ck_concepts_difficulty_range"
        ),
    )
    op.create_index("ix_concepts_category", "concepts", ["category"])

    # === concept_edges 表（邊）===
    # 注意：sa.Enum 在 PG 上會由 op.create_table 自動 CREATE TYPE，
    # 不可預先呼叫 edge_type.create()，否則會 DuplicateObjectError。
    op.create_table(
        "concept_edges",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "source_id",
            sa.UUID(),
            sa.ForeignKey("concepts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_id",
            sa.UUID(),
            sa.ForeignKey("concepts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "edge_type",
            sa.Enum(*EDGE_TYPES, name="concept_edge_type"),
            nullable=False,
        ),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "source_id", "target_id", "edge_type", name="uq_concept_edges_triple"
        ),
        sa.CheckConstraint("source_id <> target_id", name="ck_concept_edges_no_self"),
    )
    op.create_index("ix_concept_edges_source", "concept_edges", ["source_id"])
    op.create_index("ix_concept_edges_target", "concept_edges", ["target_id"])

    # === Seed 20 ConceptTags ===
    op.bulk_insert(
        concepts,
        [{"id": uuid4(), **row} for row in _CONCEPT_SEED],
    )


def downgrade() -> None:
    op.drop_index("ix_concept_edges_target", table_name="concept_edges")
    op.drop_index("ix_concept_edges_source", table_name="concept_edges")
    op.drop_table("concept_edges")
    sa.Enum(name="concept_edge_type").drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_concepts_category", table_name="concepts")
    op.drop_table("concepts")
