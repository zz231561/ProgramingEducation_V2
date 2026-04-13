# DB Schema

## Module 1: Auth

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

## Module 4: RAG

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

## Module 5: 知識圖譜

```
concepts
├── id (UUID, PK)
├── tag (varchar, unique)      -- 對應 ConceptTag enum
├── name_zh (varchar)
├── name_en (varchar)
├── description (text)
├── difficulty_level (int 1-5)
└── category (varchar)         -- "基礎語法", "物件導向", "STL"

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

## Module 6: 智慧出題

```
questions
├── id (UUID, PK)
├── type (enum: multiple_choice/fill_blank/coding)
├── concept_tags (text[])
├── bloom_level (enum)
├── difficulty (int 1-5)
├── content (jsonb)         -- 題幹、選項、答案
├── explanation (text)
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

## Module 7: 學習路徑

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

## Module 8: 教師端

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
