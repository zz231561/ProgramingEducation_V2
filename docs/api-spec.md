# API 規格

> 本文件記錄 FastAPI 對外契約；路由 inventory 以 `backend/main.py` 註冊後的 OpenAPI 為準。
> Backend routes 不帶 `/api`；瀏覽器端由 Next.js `/api/**` proxy 轉送。修改 router 時需同步本表。
> request annotations、response model、success status 與 auth/rate-limit dependencies 由
> `doc_selfcheck.py` 的 signature fingerprint 防 drift；變更契約時須一併更新本文件與 fingerprint。
> 新 fingerprint：`python3 scripts/doc_contract_inventory.py`。
<!-- contract: api-signature-sha256=335c1d9311826e6e4851d7ba5816a9bdac17523fcedc08b118083a30f2a59566 -->

## Auth、使用者與 Profile

| Method | Path | 用途 |
|---|---|---|
| GET | `/auth/me` | 驗證 JWT 並取得目前使用者 |
| GET | `/users/me` | 取得使用者與 onboarding 狀態 |
| POST | `/users/role` | 首次選擇 student / teacher 身分 |
| GET / POST | `/profile` | 取得或建立學生身分資料 |

Google OAuth callback、session 與 logout 由 NextAuth.js 處理，不是 FastAPI routes。

## 程式碼、檔案與 Terminal

| Method | Path | 用途 |
|---|---|---|
| POST | `/code/execute` | 批次執行 C++；自建 runner 為主、Judge0 fallback |
| GET / PUT | `/code/draft` | 讀取／儲存自動草稿 |
| GET / PUT / PATCH | `/code/files` | 列表、儲存、改名命名檔案 |
| GET / DELETE | `/code/files/{file_id}` | 讀取／刪除命名檔案 |
| POST | `/terminal/ticket` | 簽發 WebSocket terminal 一次性 ticket |

## Chat（EDF Pipeline）

| Method | Path | 用途 |
|---|---|---|
| POST | `/chat/interact` | SSE 教學互動；stage → done / error events |
| POST | `/chat/run-help` | 依執行結果主動說明 |
| POST | `/chat/reflection-kickoff` | 由反思內容建立對話情境 |
| GET | `/chat/sessions` | 列出對話 sessions |
| GET / DELETE | `/chat/sessions/{session_id}` | 讀取／刪除 session |

## Quiz 與理解驗證

| Method | Path | 用途 |
|---|---|---|
| GET | `/quiz/from-bank` | 依 concept 與題型取 validated 題目 |
| GET | `/quiz/unit-set` | LEARN 單元題組 |
| POST | `/quiz/generate` | 即時生成題目 |
| POST | `/quiz/weakness-set` | 依弱項產生自適應題組 |
| POST | `/quiz/hint` | 取得題目提示 |
| POST | `/quiz/submit` | 提交作答並更新 mastery |
| GET | `/quiz/history` | 作答歷史 |
| GET | `/quiz/bank` | 教師檢視 validated 題庫與正解 |
| GET | `/quiz/questions/{question_id}` | 診斷微測驗單題 |
| GET | `/quiz/answers/{answer_id}/feedback` | 取得作答回饋 |
| GET | `/comprehension/trigger-suggestion/{student_answer_id}` | 建議理解驗證類型 |
| GET / PUT | `/comprehension/{student_answer_id}` | 讀取／更新理解驗證狀態 |
| POST | `/comprehension/{student_answer_id}/epl/generate` | 產生 EPL 題目 |
| POST | `/comprehension/{student_answer_id}/epl/grade` | 評分 EPL |
| POST | `/comprehension/{student_answer_id}/predict_output/generate` | 產生預測輸出題 |
| POST | `/comprehension/{student_answer_id}/predict_output/grade` | 評分預測輸出 |
| POST | `/comprehension/{student_answer_id}/variation/generate` | 產生變體題 |
| POST | `/comprehension/{student_answer_id}/variation/grade` | 評分變體題 |

## Pre-Coding Reflection

| Method | Path | 用途 |
|---|---|---|
| POST | `/reflection` | 建立反思；source_type 為 quiz / learning_unit |
| GET / PATCH | `/reflection/{reflection_id}` | 取得／更新反思 |

## 學習路徑與知識圖譜

| Method | Path | 用途 |
|---|---|---|
| GET / POST | `/learning/paths` | 列出／建立學習路徑 |
| GET | `/learning/paths/default` | 取得預設路徑 |
| GET / DELETE | `/learning/paths/{path_id}` | 取得／刪除路徑 |
| PATCH | `/learning/units/{unit_id}` | 轉換單元狀態 |
| GET | `/concepts/graph` | 完整 K-Graph |
| GET | `/concepts/mastery` | effective / raw mastery 與複習狀態 |
| GET | `/concepts/{tag}` | concept 詳情與鄰居 |
| GET | `/concepts/{tag}/diagnosis` | 根源弱點診斷 |
| POST | `/concepts/{tag}/diagnosis/remediate` | 開放補救路徑 |

## 班級、Dashboard 與作業

| Method | Path | 用途 |
|---|---|---|
| GET / POST | `/classes` | 教師列出／建立班級 |
| GET | `/classes/mine` | 學生的班級 |
| POST | `/classes/join` | 以 invite code 加入 |
| PATCH | `/classes/{class_id}` | 編輯班級 |
| GET | `/classes/{class_id}/members` | 班級成員 |
| GET | `/dashboard/timeline` | 行為時間線 |
| GET | `/dashboard/mastery-overview` | 精熟度總覽 |
| GET | `/dashboard/stats` | Dashboard 統計 |
| GET / POST | `/assignments` | 教師列出／建立作業 |
| GET / PATCH / DELETE | `/assignments/{assignment_id}` | 取得／編輯／刪除作業 |
| POST | `/assignments/{assignment_id}/attachments` | 上傳作業附件 |
| GET | `/assignments/mine` | 學生作業列表 |
| GET | `/assignments/mine/{assignment_id}` | 學生作業詳情 |
| PUT | `/assignments/{assignment_id}/submission` | upsert 繳交 |
| GET | `/assignments/{assignment_id}/submissions` | 教師檢視繳交狀態 |
| POST | `/submissions/{submission_id}/attachments` | 上傳繳交附件 |
| PATCH | `/submissions/{submission_id}/grade` | 評分與評語 |
| GET / DELETE | `/attachments/{attachment_id}` | 授權下載／刪除附件 |

## Dev 與 Health

`/dev/**` 僅在 `DEBUG=true` 使用；不是正式環境功能。

| Method | Path | 用途 |
|---|---|---|
| GET | `/dev/status` | dev mode 狀態 |
| POST | `/dev/reset` | 重設測試資料 |
| PUT | `/dev/mastery` | 設定測試 mastery |
| PUT | `/dev/role` | 切換測試角色 |
| GET | `/dev/questions` | 檢視題庫 |
| POST | `/dev/simulate-failures` | 模擬連續答錯 |
| GET | `/health` | DB、Redis 與服務健康狀態 |

## 標準錯誤格式

```json
{ "error": "UPPER_SNAKE_CASE", "message": "繁體中文訊息", "detail": {} }
```

常見狀態：401 認證失敗、403 權限不足、404 資源隱匿／不存在、409 狀態衝突、
422 validation、429 rate limit / daily quota、502 upstream LLM、503 runner / LLM unavailable、
504 execution / backend timeout。實際 error code 由 `backend/core/errors.py` 與各 route 的 `AppError` 定義。
