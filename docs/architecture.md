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
