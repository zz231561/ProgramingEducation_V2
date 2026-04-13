# 技術棧與系統架構

## 技術棧

| 層級 | 技術 | 說明 |
|------|------|------|
| **Frontend** | Next.js 15 + TypeScript + Tailwind CSS | SSR/CSR 混合、型別安全、元件化 |
| **Backend** | FastAPI + Python 3.12 | 非同步 API、WebSocket、型別驗證 |
| **Database** | PostgreSQL | 學生資料、學習紀錄、知識圖譜持久化 |
| **Cache** | Redis | Session cache、rate limiting |
| **ORM** | SQLAlchemy 2.0 (async) | 非同步 ORM、migration 透過 Alembic |
| **Code Execution** | Judge0 (Self-hosted) | 開源、免費、60+ 語言、沙箱隔離 |
| **LLM** | OpenAI GPT-4o | 結構化輸出、Socratic 教學 |
| **RAG** | LlamaIndex + pgvector | 向量搜尋直接整合在 PostgreSQL 中 |
| **Auth** | NextAuth.js (Google OAuth) | Session-based 驗證 |
| **Deployment** | Zeabur | 前後端 + DB + Redis 各為獨立 service |

---

## 系統架構

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

---

## 專案目錄結構

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
│   ├── types/                    # TypeScript 型別定義
│   └── package.json
│
├── backend/                      # FastAPI 後端
│   ├── main.py                   # FastAPI 進入點
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── code.py           # 程式碼執行
│   │   │   ├── chat.py           # AI 對話
│   │   │   ├── quiz.py           # 出題 / 作答
│   │   │   ├── learn.py          # 學習路徑
│   │   │   ├── knowledge.py      # 知識圖譜
│   │   │   └── health.py
│   │   ├── middleware/
│   │   │   ├── auth.py           # JWT 驗證
│   │   │   └── rate_limit.py
│   │   └── deps.py               # 依賴注入
│   ├── models/                   # SQLAlchemy Models
│   │   ├── user.py
│   │   ├── concept.py
│   │   ├── question.py
│   │   ├── session.py
│   │   ├── learning.py
│   │   └── document.py
│   ├── services/
│   │   ├── edf/                  # EDF 教學管線
│   │   │   ├── evidence.py       # 程式碼分析
│   │   │   ├── decision.py       # Bloom × Hint 策略
│   │   │   ├── feedback.py       # 回應生成
│   │   │   └── prompt.py         # Prompt 組裝
│   │   ├── code_executor.py      # Judge0 API client
│   │   ├── rag.py                # RAG 檢索
│   │   ├── quiz_generator.py     # 智慧出題
│   │   ├── learning_path.py      # 學習路徑生成
│   │   ├── knowledge_graph.py    # 圖譜查詢
│   │   └── security/
│   │       ├── sanitizer.py
│   │       └── validator.py
│   ├── core/
│   │   ├── config.py             # 環境變數管理
│   │   ├── database.py           # DB 連線
│   │   └── redis.py              # Redis 連線
│   ├── alembic/                  # DB Migration
│   ├── requirements.txt
│   └── Dockerfile
│
├── judge0/                       # Judge0 部署配置
│   └── docker-compose.yml
│
├── docs/                         # 計畫文件（本目錄）
├── CLAUDE.md                     # 專案級 AI 指引
└── README.md
```
