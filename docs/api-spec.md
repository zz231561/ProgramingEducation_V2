# API 規格

## Auth

```
POST   /api/auth/google          -- Google OAuth callback
GET    /api/auth/me               -- 取得當前使用者資訊
POST   /api/auth/logout           -- 登出
```

## Code Execution

```
POST   /api/code/execute          -- 提交程式碼至 Judge0 執行
  body: { code, language_id, stdin? }
  resp: { stdout, stderr, compile_output, exit_code, time, memory }

GET    /api/code/languages        -- 取得支援的語言列表
  resp: [{ id, name }]
```

## Chat (EDF Pipeline)

```
POST   /api/chat/interact         -- 主要教學互動（SSE streaming response）
  body: { code, question, session_id?, stdin_data?, is_review? }
  resp: text/event-stream → { type: "token"|"done", data: string }
        done event 包含: { session_id, evidence_summary }

GET    /api/chat/sessions         -- 取得使用者所有對話 session
  query: { page?, limit? }
  resp: { sessions: [{ id, title, updated_at }], total }

GET    /api/chat/sessions/{sid}   -- 取得特定 session 的訊息歷史
  resp: { session, messages: [{ role, content, code_snapshot?, created_at }] }

DELETE /api/chat/sessions/{sid}   -- 刪除對話 session（cascade 刪除訊息）
```

## Quiz

```
POST   /api/quiz/generate         -- 根據弱項生成題目
  body: { count?, difficulty?, concept_tags? }
  resp: { questions: [Question] }

POST   /api/quiz/submit           -- 提交作答
  body: { question_id, answer, time_spent_seconds }
  resp: { is_correct, explanation, feedback, mastery_update,
          comprehension_check?: { type, prompt } }

GET    /api/quiz/history          -- 作答歷史
  query: { page?, limit?, concept_tag? }
  resp: { answers: [StudentAnswer], total }

POST   /api/quiz/comprehension    -- 提交理解驗證回答
  body: { answer_id, comprehension_answer }
  resp: { passed, feedback, mastery_update }
```

## Pre-Coding Reflection

```
POST   /api/reflection            -- 提交解題前反思
  body: { source_type: "quiz"|"learning_unit", source_id,
          problem_understanding, planned_steps, expected_concepts }
  resp: { reflection_id, quality_score,
          followup_question?: string }   -- 品質不足時回傳追問

PATCH  /api/reflection/{id}       -- 更新反思（補充回答或 coding 中修改計畫）
  body: { followup_answer?, planned_steps?, expected_concepts? }
  resp: { updated: true }

GET    /api/reflection/{id}       -- 取得反思內容（供 UI 側邊欄顯示）
  resp: { Reflection }
```

## Learning Path

```
GET    /api/learn/paths           -- 取得使用者的學習路徑
POST   /api/learn/paths           -- 建立新學習路徑
  body: { title?, goal_concepts? }

GET    /api/learn/paths/{id}      -- 取得特定路徑的所有單元
PATCH  /api/learn/units/{id}      -- 更新單元狀態
  body: { status }
```

## Knowledge Graph

```
GET    /api/knowledge/graph       -- 完整概念圖 (nodes + edges)
GET    /api/knowledge/mastery     -- 學生精熟度
GET    /api/knowledge/concepts/{tag}  -- 特定概念詳情 + mastery + prerequisites
```

## Dashboard

```
GET    /api/dashboard/summary     -- 學生學習總覽（聚合資料）
  resp: {
    concepts_learned, concepts_total,
    total_practices, avg_confidence,
    streak_days,
    weak_concepts: [{ tag, confidence }],
    next_learning_unit: { path_id, unit_id, concept_tag }
  }

GET    /api/dashboard/activity    -- 最近活動時間線
  query: { page?, limit? }
  resp: { activities: [{ type, description, date }], total }
```

## Behavior Analytics（教師專屬，需 role=teacher）

```
GET    /api/analytics/class/{class_id}/overview  -- 班級行為總覽
  resp: {
    student_count, avg_submit_count, avg_success_rate,
    avg_hint_level, avg_fix_duration_seconds,
    cluster_distribution: { active: N, passive: N, struggling: N }
  }

GET    /api/analytics/class/{class_id}/scatter   -- 行為-成效散佈圖資料
  query: { metric: "submit_count"|"hint_avg"|"fix_duration"|"chat_count" }
  resp: { points: [{ user_id, name, x: metric_value, y: confidence_delta }] }

GET    /api/analytics/class/{class_id}/heatmap   -- 錯誤類型熱力圖
  resp: { students: [name], concepts: [tag], matrix: [[int]] }

GET    /api/analytics/student/{user_id}/timeline -- 個人學習行為時序
  query: { from?, to? }
  resp: { events: [{ type, concept_tags, hint_level, created_at }] }

GET    /api/analytics/student/{user_id}/summary  -- 個人行為摘要
  resp: {
    submit_count, success_rate, avg_fix_duration,
    hint_distribution, dialogue_act_distribution,
    confidence_trend: [{ date, avg_confidence }]
  }
```

## Health

```
GET    /api/health                -- { status, db, redis, judge0 }
```
