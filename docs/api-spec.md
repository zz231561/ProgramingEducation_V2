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
POST   /api/chat/interact         -- 主要教學互動（程式碼 + 問題 → AI 回饋）
  body: { code, question, session_id, stdin_data?, is_review? }
  resp: { llm_response, execution_output, error_output, session_id }

GET    /api/chat/history/{sid}    -- 取得對話歷史
  resp: { messages: [{ role, content, timestamp }] }

DELETE /api/chat/history/{sid}    -- 清除對話歷史
```

## Quiz

```
POST   /api/quiz/generate         -- 根據弱項生成題目
  body: { count?, difficulty?, concept_tags? }
  resp: { questions: [Question] }

POST   /api/quiz/submit           -- 提交作答
  body: { question_id, answer, time_spent_seconds }
  resp: { is_correct, explanation, feedback, mastery_update }

GET    /api/quiz/history          -- 作答歷史
  query: { page?, limit?, concept_tag? }
  resp: { answers: [StudentAnswer], total }
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

## Health

```
GET    /api/health                -- { status, db, redis, judge0 }
```
