<!-- 由 scripts/sync_agents_md.py 自動產生，請勿直接編輯；改動請改來源檔，再重跑同步 -->
<!-- 來源：.claude/rules/backend.md -->

---
description: 後端開發規範 — 錯誤處理、安全防護、環境變數
globs: backend/**
---

# 後端開發規範

## 錯誤處理

| 錯誤類型 | Status | 處理 |
|----------|--------|------|
| 未登入 | 401 | 重導登入頁 |
| Token 過期（exp） | 401 | `TOKEN_EXPIRED`，前端統一重導登入頁 |
| 權限不足 | 403 | 提示訊息 |
| 輸入驗證失敗 | 422 | `VALIDATION_ERROR` 標準格式（欄位錯誤在 detail.errors） |
| Runner / Judge0 逾時 | 504 | 「編譯/執行逾時」+ 建議縮短程式 |
| Runner / Judge0 不可用 / 網路層例外 | 503 | httpx 連線失敗與 5xx 一律轉 503，禁止冒泡成 500 |
| OpenAI 失敗 | 502 | 「AI 服務暫時不可用」+ 快取最近回應 |
| LLM 回傳不符 schema | 502 | `LLM_PARSE_ERROR`（JSON mode 不保證 schema，ValidationError 必須捕捉）。**但 Evidence 層例外**：單一欄位越界（如 LLM 把 ConceptTag 寫進 error_type）由 `EvidenceResult.from_llm` 退回保守預設 + warning，只有 JSON 本身壞掉才 502——一個欄位不該毀掉整次教學互動 |
| Rate limit | 429 | 回傳剩餘冷卻時間（`core/rate_limit.py`，Redis 掛掉 fail-open） |
| 內部錯誤 | 500 | 記錄 traceback，回傳通用錯誤 |

**容錯 swallow 規則**：best-effort 邏輯（mastery / RAG / reflection 注入）失敗可吞例外不擋主流程，但**必須** `logger.warning` 留痕，禁止裸 `except: pass`。

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

# 執行引擎（7-R 自建 runner 主路徑，2026-08-05）
RUNNER_BACKEND=self             # self（預設）/ judge0（B 機故障時降級 RapidAPI 批次）
RUNNER_URL=http://43.133.7.93:8080  # B 機 runner endpoint（port 以 R1 實作為準）
RUNNER_TOKEN=xxx                # A→B 共享密鑰（X-Runner-Token；Zeabur Secret）

# Judge0（fallback）
JUDGE0_API_URL=https://judge0-ce.p.rapidapi.com
JUDGE0_API_KEY=xxx  # RapidAPI key 或自架 authn token；自架未開 authn 不需要
JUDGE0_AUTH_MODE=   # 可選：rapidapi / self-hosted；空 = 依 URL 自動判斷

# 可選 — 6-M 任務導向模型路由（分組變數未設定時 fallback LLM_MODEL）
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-5.6-luna         # 預設：對話組（EDF Feedback）+ 分析組（Evidence/Reflection/Comprehension 評分）
LLM_MODEL_GENERATE=gpt-5.6-luna # 生成組：Quiz generate / Hint / Comprehension 出題
LLM_MODEL_VALIDATE=gpt-5.6-terra # 審查組：Quiz validate（cascade 強把關端）
LLM_MODEL_CONTENT=gpt-5.6-terra  # 內容組：Unit content 批次
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_LLM_PER_DAY=60      # 每人每日 LLM 互動上限（防濫用；正常密集使用約 30-50 次）
LOG_LEVEL=INFO
```

## 測試策略

- **Unit**: pytest + pytest-asyncio → services（EDF pipeline、quiz generator）
- **Integration**: pytest + httpx.AsyncClient → API endpoints（含 DB）
- **Security**: pytest → sanitizer regex、output validator

### 改完後端程式碼必跑（全綠才算完成）
```bash
cd backend
.venv/bin/python -m pytest -q      # 全部測試
.venv/bin/ruff check .            # lint（已校準中文與 FastAPI 誤判，應為 All checks passed）
```
- ruff 設定見 `pyproject.toml`；**不要為了消警告而放寬 ignore**，先確認是不是真誤判
- 動到 migration：另跑 `.venv/bin/alembic upgrade head` 確認可套用
- 新增／刪除／改名 route 必須同步 `docs/api-spec.md`；ORM table 或 migration 契約變更同步 `docs/db-schema.md`，最後跑 `python3 scripts/doc_selfcheck.py`
