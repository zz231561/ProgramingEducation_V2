# 工程規範

## 環境變數清單

```bash
# === 必要 ===
OPENAI_API_KEY=sk-proj-...            # GPT-4o API key
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
NEXTAUTH_SECRET=xxx                    # NextAuth session 加密金鑰
NEXTAUTH_URL=https://your-domain.com   # 生產環境 URL

# === Judge0 ===
JUDGE0_API_URL=https://judge0-ce.p.rapidapi.com  # 或自架 URL
JUDGE0_API_KEY=xxx                     # RapidAPI key（自架不需要）

# === 可選 ===
EMBEDDING_MODEL=text-embedding-3-small # 預設值
LLM_MODEL=gpt-4o                      # 預設值
RATE_LIMIT_PER_MINUTE=10               # 每人每分鐘 LLM 請求上限
LOG_LEVEL=INFO
```

---

## 錯誤處理策略

### Backend（FastAPI）

| 錯誤類型 | HTTP Status | 處理方式 |
|----------|-------------|---------|
| 驗證失敗（未登入） | 401 | 重導至登入頁 |
| 權限不足 | 403 | 顯示提示訊息 |
| 輸入驗證失敗 | 422 | Pydantic 自動回傳欄位錯誤 |
| Judge0 逾時 | 504 | 回傳「編譯/執行逾時」+ 建議縮短程式 |
| Judge0 不可用 | 503 | 回傳「執行服務暫時不可用」+ retry-after |
| OpenAI API 失敗 | 502 | 回傳「AI 服務暫時不可用」+ 快取最近回應 |
| Rate limit 超限 | 429 | 回傳剩餘冷卻時間 |
| 內部錯誤 | 500 | 記錄完整 traceback，回傳通用錯誤訊息 |

### Frontend（Next.js）

- 全域 Error Boundary 捕獲 React 渲染錯誤
- API client 統一攔截器：401 → 重導登入、429 → 顯示冷卻倒數、5xx → toast 通知
- 程式碼執行失敗時：顯示錯誤訊息 + 「重試」按鈕
- 網路斷線偵測：顯示 offline banner

---

## 安全規範

### 輸入防護（保留 V1 三層設計）

1. **Regex 層**：偵測已知 prompt injection 模式（中英文）
2. **XML 標籤隔離**：`<student_input>` / `<student_code>` 包裝使用者輸入
3. **System Preamble**：不可覆寫的 LLM 行為規則（RULE-1 ~ RULE-5）

### 輸出防護

- 阻擋 AI 回傳完整程式碼（> 8 行且無 TODO/FIXME）
- 偵測「直接給答案」訊號並截斷

### 應用層安全

| 項目 | 措施 |
|------|------|
| CORS | 僅允許 NEXTAUTH_URL origin |
| Rate Limiting | per-user，LLM 端點 10 次/分鐘 |
| JWT | HttpOnly cookie，短效 token + refresh |
| SQL Injection | SQLAlchemy ORM 參數化查詢 |
| XSS | React 自動 escape + CSP header |
| CSRF | NextAuth 內建 CSRF token |
| 敏感資訊 | .env 不進 git，Zeabur 環境變數管理 |

---

## 測試策略

### Backend

| 類型 | 框架 | 範圍 |
|------|------|------|
| Unit Test | pytest + pytest-asyncio | services（EDF pipeline、quiz generator） |
| Integration Test | pytest + httpx.AsyncClient | API endpoints（含 DB） |
| Security Test | pytest | sanitizer regex patterns、output validator |

### Frontend

| 類型 | 框架 | 範圍 |
|------|------|------|
| Component Test | Vitest + React Testing Library | 各 UI 元件 |
| E2E Test | Playwright | 登入 → 寫程式 → 執行 → AI 對話（golden path） |

### 優先序

Phase 1 先寫 EDF pipeline unit test + 登入 E2E test，其餘隨功能逐步補上。

---

## 第三方服務依賴

| 服務 | 用途 | 費用 | Fallback |
|------|------|------|---------|
| OpenAI GPT-4o | LLM 教學回饋 + 出題 | Pay-as-you-go | 無（核心服務） |
| OpenAI Embedding | RAG 向量化 | Pay-as-you-go | 本地模型（效果較差） |
| Judge0 (RapidAPI) | 程式碼編譯執行 | 免費 50 次/天 | 自架 Judge0 |
| Google OAuth | 使用者登入 | 免費 | 帳號密碼登入（備案） |
| Zeabur | 部署平台 | 依用量 | Docker Compose 自架 |
| PostgreSQL (Zeabur) | 主資料庫 | 含在 Zeabur 方案 | 任意 PG 服務 |
| Redis (Zeabur) | 快取 + Rate Limit | 含在 Zeabur 方案 | 記憶體內 fallback |
