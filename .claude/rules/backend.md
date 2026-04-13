---
description: 後端開發規範 — 錯誤處理、安全防護、環境變數
globs: backend/**
---

# 後端開發規範

## 錯誤處理

| 錯誤類型 | Status | 處理 |
|----------|--------|------|
| 未登入 | 401 | 重導登入頁 |
| 權限不足 | 403 | 提示訊息 |
| 輸入驗證失敗 | 422 | Pydantic 自動回傳欄位錯誤 |
| Judge0 逾時 | 504 | 「編譯/執行逾時」+ 建議縮短程式 |
| Judge0 不可用 | 503 | 「執行服務暫時不可用」+ retry-after |
| OpenAI 失敗 | 502 | 「AI 服務暫時不可用」+ 快取最近回應 |
| Rate limit | 429 | 回傳剩餘冷卻時間 |
| 內部錯誤 | 500 | 記錄 traceback，回傳通用錯誤 |

## 安全規範

### 輸入防護（三層設計，保留 V1）
1. **Regex 層**：偵測已知 prompt injection 模式（中英文）
2. **XML 標籤隔離**：`<student_input>` / `<student_code>` 包裝使用者輸入
3. **System Preamble**：不可覆寫的 LLM 行為規則（RULE-1 ~ RULE-5）

### 輸出防護
- 阻擋 AI 回傳完整程式碼（> 8 行且無 TODO/FIXME）
- 偵測「直接給答案」訊號並截斷

### 應用層
- CORS：僅允許 NEXTAUTH_URL origin
- Rate Limiting：per-user，LLM 端點 10 次/分鐘
- JWT：HttpOnly cookie，短效 token + refresh
- SQL Injection：SQLAlchemy ORM 參數化查詢
- XSS：React 自動 escape + CSP header
- CSRF：NextAuth 內建 CSRF token
- 敏感資訊：.env 不進 git，Zeabur 環境變數管理

## 環境變數

```bash
# 必要
OPENAI_API_KEY=sk-proj-...
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
NEXTAUTH_SECRET=xxx
NEXTAUTH_URL=https://your-domain.com

# Judge0
JUDGE0_API_URL=https://judge0-ce.p.rapidapi.com
JUDGE0_API_KEY=xxx  # 自架不需要

# 可選
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o
RATE_LIMIT_PER_MINUTE=10
LOG_LEVEL=INFO
```

## 測試策略

- **Unit**: pytest + pytest-asyncio → services（EDF pipeline、quiz generator）
- **Integration**: pytest + httpx.AsyncClient → API endpoints（含 DB）
- **Security**: pytest → sanitizer regex、output validator
- Phase 1 優先：EDF pipeline unit test + 登入 E2E test
