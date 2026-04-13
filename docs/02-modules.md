# 模組規劃與 DB Schema

## Module 1：Auth 與使用者管理

**功能：**
- Google OAuth 登入（NextAuth.js）
- JWT token 驗證（前後端共用）
- 使用者角色：student / teacher / admin
- Rate limiting（per-user，防止 LLM API 濫用）

**DB Schema：**
```
users
├── id (UUID, PK)
├── email (unique)
├── name
├── avatar_url
├── role (enum: student/teacher/admin)
├── google_id (unique)
├── created_at
└── last_login_at
```

---

## Module 2：程式碼編輯與執行

**功能：**
- CodeMirror 6 編輯器（C++ 語法高亮、自動補全）
- 程式碼提交 → Judge0 API 編譯執行
- 支援 stdin 輸入
- 執行結果顯示（stdout / stderr / 編譯錯誤 / 執行時間）

**設計決策：**
- 開發期使用 Judge0 RapidAPI hosted（免費 50 次/天），上線後自架
- 語言透過 language_id 抽象化，未來擴充其他語言只需新增 ID
- 執行 timeout 統一為 10 秒（可依題目調整）
- Batch 模式：支援 stdin 預先輸入，不需即時互動式 terminal

---

## Module 3：EDF 教學管線（保留 V1 核心設計）

**Evidence → Decision → Feedback 三層管線：**

**Evidence（程式碼分析）：**
- LLM 結構化輸出：錯誤分類、ConceptTag、Bloom 認知等級
- 注入 Judge0 執行結果（stdout/stderr）作為分析脈絡

**Decision（教學策略）：**
- Bloom × Hint Ladder 6×6 策略矩陣（保留 V1 設計）
- RAG 觸發條件：hint_level >= 2 且 bloom_level 屬於 {ANALYZE, EVALUATE, CREATE}

**Feedback（回應生成）：**
- 分層 prompt 組裝（preamble → persona → strategy → context → RAG）
- 輸出驗證：阻擋完整程式碼洩漏，保持教學引導

**ConceptTag（初始 20 個，保留 V1 定義）：**
```
syntax-basic, io-streams, control-flow, function-design, arrays-strings,
pointer-arithmetic, memory-management, references, oop-encapsulation,
oop-inheritance, oop-polymorphism, stl-containers, stl-algorithms,
template-meta, recursion, error-handling, undefined-behavior,
algorithm-complexity, concurrency, namespaces
```

---

## Module 4：RAG 知識檢索

**功能：**
- 索引 C++ 教材、cppreference 文件、課程講義
- 根據當前 ConceptTag + 學生問題進行向量搜尋
- 檢索結果注入 EDF Feedback 層的 prompt

**技術方案：**
- pgvector 擴充套件（PostgreSQL 內建向量搜尋，不需額外服務）
- LlamaIndex 作為索引 / 檢索框架
- Embedding Model：OpenAI text-embedding-3-small

**DB Schema：**
```
documents
├── id (UUID, PK)
├── title
├── source (enum: textbook/reference/lecture/custom)
├── content_text
├── concept_tags (text[])
├── created_at
└── updated_at

document_chunks
├── id (UUID, PK)
├── document_id (FK → documents)
├── chunk_text
├── chunk_index (int)
├── embedding (vector(1536))  -- pgvector
└── metadata (jsonb)
```

---

## Module 5：知識圖譜

**功能：**
- C++ 概念之間的先修 / 包含 / 相關關係
- 視覺化概念圖（前端用 Cytoscape.js 或 D3.js）
- 根據學生精熟度標記節點顏色（紅/黃/綠）
- 學習路徑推薦（拓撲排序 + 弱項優先）

**設計決策 — 使用 PostgreSQL 鄰接表而非 Neo4j：**
- 100 人規模不需要圖資料庫的效能
- 20 個 ConceptTag + 4 種邊類型 = 極小圖（< 200 邊）
- 減少基礎設施複雜度（少一個 service）
- 未來若圖譜規模爆發，可遷移至 Neo4j

**DB Schema：**
```
concepts
├── id (UUID, PK)
├── tag (varchar, unique)      -- 對應 ConceptTag enum
├── name_zh (varchar)          -- 中文名稱
├── name_en (varchar)          -- 英文名稱
├── description (text)
├── difficulty_level (int 1-5)
└── category (varchar)         -- 如 "基礎語法", "物件導向", "STL"

concept_edges
├── id (UUID, PK)
├── source_id (FK → concepts)
├── target_id (FK → concepts)
├── edge_type (enum: prerequisite/contains/specialization/related)
└── weight (float, default 1.0)

student_mastery
├── id (UUID, PK)
├── user_id (FK → users)
├── concept_id (FK → concepts)
├── confidence (float 0.0-1.0)
├── exposure_count (int)
├── success_count (int)
├── error_count (int)
├── bloom_level (enum)
└── last_practiced_at (timestamp)
```

---

## Module 6：智慧出題

**功能：**
- 根據學生精熟度弱項自動選題
- 支援多種題型：選擇題、填空題、程式撰寫題
- 難度自適應（基於 Bloom 等級 + concept confidence）
- 題目驗證（LLM 檢查答案正確性）

**出題流程（4 階段）：**
```
1. 選題（Select）
   └─ 從 student_mastery 找出 confidence < 0.4 的弱項概念
   └─ 依知識圖譜找出相關的先修/後續概念

2. 生成（Generate）
   └─ LLM 根據概念 + 難度 + 題型生成題目
   └─ 注入 RAG 檢索的教材片段作為出題依據

3. 驗證（Validate）
   └─ LLM 自我檢查答案正確性
   └─ 確認題目不超出目標 Bloom 等級

4. 呈現（Present）
   └─ 前端渲染題目
   └─ 學生作答後觸發 EDF Pipeline 進行教學引導
```

**DB Schema：**
```
questions
├── id (UUID, PK)
├── type (enum: multiple_choice/fill_blank/coding)
├── concept_tags (text[])
├── bloom_level (enum)
├── difficulty (int 1-5)
├── content (jsonb)         -- 題目內容（題幹、選項、答案）
├── explanation (text)      -- 解析
├── source (enum: generated/imported/leetcode)
├── created_at
└── validated (boolean)

student_answers
├── id (UUID, PK)
├── user_id (FK → users)
├── question_id (FK → questions)
├── answer (jsonb)
├── is_correct (boolean)
├── time_spent_seconds (int)
├── hint_level_used (int)
├── feedback (text)         -- EDF 回饋內容
└── answered_at (timestamp)
```

---

## Module 7：結構化學習路徑

**功能：**
- 基於知識圖譜拓撲排序生成學習路徑
- 每個節點 = 一個學習單元（概念說明 + 範例 + 練習題）
- 進度追蹤與視覺化
- 弱項自動補強（偵測到概念 confidence 下降時插入複習單元）

**學習單元結構：**
```
LearningUnit
├── concept (FK → concepts)
├── order_index (int)
├── content_sections:
│   ├── explanation   -- 概念說明（RAG 檢索 + LLM 生成）
│   ├── examples      -- 程式碼範例（可執行）
│   ├── practice      -- 練習題（從 questions 表選取）
│   └── summary       -- 重點摘要
├── prerequisites     -- 需先完成的 unit
└── estimated_minutes -- 預估學習時間
```

**DB Schema：**
```
learning_paths
├── id (UUID, PK)
├── user_id (FK → users)
├── title
├── description
├── created_at
└── updated_at

learning_units
├── id (UUID, PK)
├── path_id (FK → learning_paths)
├── concept_id (FK → concepts)
├── order_index (int)
├── content (jsonb)
├── status (enum: locked/available/in_progress/completed)
└── completed_at (timestamp)
```

---

## Module 8：教師 Dashboard（Phase 4）

**功能（先設計 Schema，後續實作）：**
- 班級學生學習進度總覽
- 概念精熟度熱力圖
- 常見錯誤模式統計
- 出題 / 指派作業功能

**DB Schema：**
```
classes
├── id (UUID, PK)
├── name
├── teacher_id (FK → users)
├── invite_code (varchar, unique)
├── created_at
└── is_active (boolean)

class_members
├── class_id (FK → classes)
├── user_id (FK → users)
├── joined_at
└── PRIMARY KEY (class_id, user_id)
```
