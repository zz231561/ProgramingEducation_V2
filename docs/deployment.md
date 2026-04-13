# 部署指南 — Zeabur

## 架構概覽

```
Browser → web (Next.js, port 3000) → backend (FastAPI, port 8000)
                                          ├── PostgreSQL
                                          └── Redis
```

## 前置條件

- Zeabur 帳號 + Project 建立完成
- Google OAuth credentials（已設定 redirect URI 為正式 domain）
- OpenAI API Key
- Judge0 API URL + Key

## Step 1：建立 Marketplace 服務

在 Zeabur Project 中新增以下 Marketplace 服務：

1. **PostgreSQL** — 記下自動產生的連線資訊
2. **Redis** — 記下自動產生的連線資訊

## Step 2：部署 backend

1. 新增 Git Service → 選擇本 repo
2. **Root Directory** 設為 `backend`
3. 設定環境變數：

| 變數 | 值 |
|------|-----|
| `DATABASE_URL` | `postgresql+asyncpg://${POSTGRES_USERNAME}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DATABASE}` |
| `REDIS_URL` | `redis://${REDIS_HOST}:${REDIS_PORT}/0` |
| `NEXTAUTH_SECRET` | 與前端 `AUTH_SECRET` 相同 |
| `NEXTAUTH_URL` | `https://<your-web-domain>` |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret |
| `OPENAI_API_KEY` | OpenAI API Key |
| `JUDGE0_API_URL` | Judge0 API 端點 |
| `JUDGE0_API_KEY` | Judge0 API Key |

> Zeabur 支援 `${POSTGRES_HOST}` 等變數引用，會自動解析同 Project 內的服務。

## Step 3：部署 web

1. 新增 Git Service → 選擇本 repo
2. **Root Directory** 設為 `web`
3. 綁定自訂 Domain
4. 設定環境變數：

| 變數 | 值 |
|------|-----|
| `AUTH_SECRET` | `npx auth secret` 產生的值 |
| `AUTH_GOOGLE_ID` | Google OAuth Client ID |
| `AUTH_GOOGLE_SECRET` | Google OAuth Client Secret |
| `BACKEND_URL` | `http://<backend-service-name>.zeabur.internal:8000` |
| `AUTH_TRUST_HOST` | `true` |

> `BACKEND_URL` 使用 Zeabur 內部 DNS（`<service-name>.zeabur.internal`）。

## Step 4：驗證

Golden path 測試：
1. 開啟前端 Domain → 應看到登入頁
2. Google OAuth 登入 → 成功進入 Workspace
3. 撰寫 C++ 程式 → 點擊 Run → Output Panel 顯示結果
4. 開啟 Chat Panel → 發送訊息 → AI 回覆正常

Health check：
- `https://<web-domain>/api/health` → `{"status": "ok"}`

## 疑難排解

| 問題 | 檢查 |
|------|------|
| 502 Bad Gateway | `BACKEND_URL` 是否正確指向 backend 內部地址 |
| DB 連線失敗 | `DATABASE_URL` 格式是否為 `postgresql+asyncpg://...` |
| OAuth 失敗 | Google Console redirect URI 是否包含正式 domain |
| Migration 失敗 | 查看 backend logs，確認 PostgreSQL 已啟動 |
