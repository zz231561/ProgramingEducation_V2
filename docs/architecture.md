# 系統架構

```
┌─────────────────────────────────────────────────────────┐
│                      Zeabur                              │
│                                                          │
│  ┌────────────────┐      ┌────────────────────────────┐ │
│  │   Frontend      │      │        Backend             │ │
│  │   Next.js 15    │─────▶│        FastAPI             │ │
│  │   + NextAuth    │ API  │                            │ │
│  │   + CodeMirror 6│◀─────│  ┌─────┐ ┌──────┐ ┌────┐ │ │
│  │                 │      │  │ EDF │ │ RAG  │ │Auth│ │ │
│  └────────────────┘      │  │Pipe │ │Serv. │ │ MW │ │ │
│                           │  └──┬──┘ └──┬───┘ └────┘ │ │
│  ┌──────────┐             │     │       │             │ │
│  │  Judge0   │◀───────────│─────┘       │             │ │
│  │  (自架)   │            │             ▼             │ │
│  └──────────┘             │  ┌──────────────────────┐ │ │
│                           │  │    PostgreSQL         │ │ │
│  ┌──────────┐             │  │  + pgvector (RAG)    │ │ │
│  │  Redis    │◀───────────│  │  + 學生/課程/紀錄    │ │ │
│  │  (Cache)  │            │  │  + 知識圖譜 (鄰接表)  │ │ │
│  └──────────┘             │  └──────────────────────┘ │ │
│                           └────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 前後端通訊模式

```
Browser → Next.js API Routes (/app/api/**) → FastAPI (backend)
                  ↑ proxy 層                      ↑ 業務邏輯
```

**流程：**
1. Browser 發 request 到 Next.js API Routes（同源，無 CORS 問題）
2. Next.js API Route 從 NextAuth session 取出 user info
3. 簽發/附加 JWT token，proxy 轉發至 FastAPI
4. FastAPI middleware 驗證 JWT，執行業務邏輯

**為何不讓 Browser 直打 FastAPI：**
- NextAuth session 是 HttpOnly cookie，只有 Next.js server 能讀取
- 統一進出口，前端只需 `fetch('/api/...')`，不需管後端 URL
- 部署時前端 + API Routes 同一 service，後端可設為 internal 不暴露

**Chat streaming：** Next.js API Route 用 SSE 轉發 FastAPI 的 streaming response

**標準錯誤回應格式（前後端共用）：**
```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "已超過每分鐘請求上限，請稍後再試",
  "detail": { "retry_after_seconds": 42 }
}
```
- `error`: 機器可讀的錯誤碼（UPPER_SNAKE_CASE）
- `message`: 使用者可見的繁中訊息
- `detail`: 可選，額外資訊（各 error 自定義）

常用 error codes: `UNAUTHORIZED`, `FORBIDDEN`, `VALIDATION_ERROR`, `RATE_LIMIT_EXCEEDED`, `JUDGE0_TIMEOUT`, `JUDGE0_UNAVAILABLE`, `LLM_UNAVAILABLE`, `INTERNAL_ERROR`

## 目錄結構

```
ProgramingEducation_V2/
├── web/                          # Next.js 前端
│   ├── app/                      # App Router
│   │   ├── (auth)/               # 登入頁面
│   │   ├── (main)/               # 主要頁面（需登入）
│   │   │   ├── workspace/        # 程式碼編輯 + AI 對話
│   │   │   ├── learn/            # 結構化學習路徑
│   │   │   ├── quiz/             # 智慧出題 + 測驗
│   │   │   ├── knowledge/        # 知識圖譜視覺化
│   │   │   └── dashboard/        # 教師 Dashboard
│   │   ├── api/                  # Next.js API Routes (proxy/auth)
│   │   └── layout.tsx
│   ├── components/               # React 元件
│   │   ├── editor/               # CodeMirror 6
│   │   ├── chat/                 # AI 對話面板
│   │   ├── graph/                # 知識圖譜
│   │   ├── quiz/                 # 測驗介面
│   │   └── ui/                   # 共用 UI 元件
│   ├── lib/                      # 工具函式
│   ├── hooks/                    # Custom Hooks
│   └── types/                    # TypeScript 型別定義
│
├── backend/                      # FastAPI 後端
│   ├── main.py                   # 進入點
│   ├── api/
│   │   ├── routes/               # auth, code, chat, quiz, learn, knowledge, health
│   │   ├── middleware/           # auth (JWT), rate_limit
│   │   └── deps.py              # 依賴注入
│   ├── models/                   # SQLAlchemy Models
│   ├── services/
│   │   ├── edf/                  # EDF 教學管線 (evidence, decision, feedback, prompt)
│   │   ├── analytics/            # 學習行為分析 (event logging, aggregation, clustering)
│   │   ├── code_executor.py      # Judge0 API client
│   │   ├── rag.py                # RAG 檢索
│   │   ├── quiz_generator.py     # 智慧出題
│   │   ├── learning_path.py      # 學習路徑
│   │   ├── knowledge_graph.py    # 圖譜查詢
│   │   └── security/            # sanitizer, validator
│   ├── core/                     # config, database, redis
│   └── alembic/                  # DB Migration
│
├── judge0/                       # Judge0 部署配置
├── docs/                         # 計畫文件
└── .claude/rules/                # Claude Code 自動注入規則
```
