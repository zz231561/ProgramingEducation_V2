# DB Schema

> 標記 `★` 為需要建立的 index/constraint

## Module 1: Auth

```
users
├── id (UUID, PK)
├── email (unique) ★
├── name
├── avatar_url
├── role (enum: student/teacher/admin)  -- 預設 student
├── google_id (unique) ★
├── created_at
└── last_login_at
```

## Module 3: Chat Session

```
chat_sessions
├── id (UUID, PK)
├── user_id (FK → users) ★ index
├── title                              -- 自動取首條訊息摘要
├── created_at
└── updated_at

chat_messages
├── id (UUID, PK)
├── session_id (FK → chat_sessions, ON DELETE CASCADE) ★ index
├── role (enum: user/assistant/system)
├── content (text)
├── code_snapshot (text, nullable)     -- 當時的程式碼快照
├── execution_result (jsonb, nullable) -- Judge0 執行結果
├── evidence (jsonb, nullable)         -- EDF Evidence 層輸出
├── created_at ★ index (session_id, created_at) 複合索引供歷史排序
```

## Module 4: RAG

```
documents
├── id (UUID, PK)
├── title
├── source (enum: textbook/reference/lecture/custom)
├── content_text
├── concept_tags (text[]) ★ GIN index
├── created_at
└── updated_at

document_chunks
├── id (UUID, PK)
├── document_id (FK → documents, ON DELETE CASCADE)
├── chunk_text
├── chunk_index (int)
├── embedding (vector(1536)) ★ HNSW index (cosine)
└── metadata (jsonb)
```

## Module 5: 知識圖譜

```
concepts
├── id (UUID, PK)
├── tag (varchar, unique) ★          -- 對應 ConceptTag enum
├── name_zh (varchar)
├── name_en (varchar)
├── description (text)
├── difficulty_level (int 1-5)
└── category (varchar)               -- "基礎語法", "物件導向", "STL"

concept_edges
├── id (UUID, PK)
├── source_id (FK → concepts, ON DELETE CASCADE)
├── target_id (FK → concepts, ON DELETE CASCADE)
├── edge_type (enum: prerequisite/contains/specialization/related)
├── weight (float, default 1.0)
└── UNIQUE (source_id, target_id, edge_type) ★

student_mastery
├── id (UUID, PK)
├── user_id (FK → users, ON DELETE CASCADE)
├── concept_id (FK → concepts, ON DELETE CASCADE)
├── confidence (float 0.0-1.0, default 0.0)
├── exposure_count (int, default 0)
├── success_count (int, default 0)
├── error_count (int, default 0)
├── bloom_level (enum: REMEMBER/UNDERSTAND/APPLY/ANALYZE/EVALUATE/CREATE)
├── last_practiced_at (timestamp)
└── UNIQUE (user_id, concept_id) ★
```

## Module 6: 智慧出題

```
questions
├── id (UUID, PK)
├── type (enum: multiple_choice/fill_blank/coding)
├── concept_tags (text[]) ★ GIN index
├── bloom_level (enum: REMEMBER/UNDERSTAND/APPLY/ANALYZE/EVALUATE/CREATE)
├── difficulty (int 1-5)
├── content (jsonb)                   -- 題幹、選項、答案
├── explanation (text)
├── source (enum: generated/imported/leetcode)
├── created_at
└── validated (boolean, default false)

student_answers
├── id (UUID, PK)
├── user_id (FK → users) ★ index
├── question_id (FK → questions)
├── answer (jsonb)
├── is_correct (boolean)
├── time_spent_seconds (int)
├── hint_level_used (int 0-5)
├── feedback (text)
├── answered_at (timestamp)
└── ★ index (user_id, answered_at) 供歷史查詢
```

## Module 7: 學習路徑

```
learning_paths
├── id (UUID, PK)
├── user_id (FK → users, ON DELETE CASCADE) ★ index
├── title
├── description
├── created_at
└── updated_at

learning_units
├── id (UUID, PK)
├── path_id (FK → learning_paths, ON DELETE CASCADE)
├── concept_id (FK → concepts)
├── order_index (int)
├── content (jsonb)
├── status (enum: locked/available/in_progress/completed)
├── completed_at (timestamp, nullable)
└── UNIQUE (path_id, order_index) ★
```

## Module 8: 教師端

```
classes
├── id (UUID, PK)
├── name
├── teacher_id (FK → users)
├── invite_code (varchar, unique) ★
├── created_at
└── is_active (boolean, default true)

class_members
├── class_id (FK → classes, ON DELETE CASCADE)
├── user_id (FK → users, ON DELETE CASCADE)
├── joined_at
└── PRIMARY KEY (class_id, user_id)
```

## Module 9: 學習行為分析

```
coding_events
├── id (UUID, PK)
├── user_id (FK → users, ON DELETE CASCADE) ★ index
├── session_id (FK → chat_sessions, nullable)
├── event_type (enum: submit/compile_error/runtime_error/success/hint_request/fix)
├── concept_tags (text[], nullable) ★ GIN index
├── code_snapshot (text, nullable)
├── execution_result (jsonb, nullable)     -- Judge0 結果摘要
├── hint_level (int 0-5, nullable)         -- 觸發的 hint 等級
├── metadata (jsonb, nullable)             -- 額外資訊（error_type, fix_duration_ms 等）
├── created_at ★ index (user_id, created_at) 複合索引供時序查詢
```

> `chat_messages` 表擴充欄位（Phase 4-2c）：
> - `dialogue_act (enum: asking_hint/clarification/debugging/off_topic/acknowledgment, nullable)`
> - 用於分類學生與 AI Tutor 的互動類型

```
behavior_aggregates                         -- 預聚合表，定期計算避免即時查詢壓力
├── id (UUID, PK)
├── user_id (FK → users, ON DELETE CASCADE)
├── period_start (date) ★ index
├── period_end (date)
├── submit_count (int)
├── success_rate (float)
├── avg_fix_duration_seconds (float)        -- 平均修復時間
├── hint_distribution (jsonb)               -- { "0": 3, "1": 5, "2": 2, ... }
├── dialogue_act_distribution (jsonb)       -- { "asking_hint": 4, "debugging": 7, ... }
├── active_seconds (int)                    -- session 總活躍時間
├── concept_error_counts (jsonb)            -- { "pointer-arithmetic": 5, "memory-management": 3 }
├── UNIQUE (user_id, period_start) ★
```
