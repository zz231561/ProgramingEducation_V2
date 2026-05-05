# 部署指南

兩種部署選項：
- **A. Zeabur**（推薦 MVP 上線）— 走 `zeabur.json`，details 見 §A
- **B. Self-host VPS**（如 Tencent Tokyo）— 走 `docker-compose.prod.yml`，details 見 §B

## 架構概覽

```
Browser → web (Next.js, port 3000) → backend (FastAPI, port 8000)
                                          ├── PostgreSQL (pgvector)
                                          └── Redis
```

## ⚠ pgvector 必要性

backend 啟動時會跑 `alembic upgrade head`，其中 migration `b2c3d4e5f6a7` 會執行
`CREATE EXTENSION IF NOT EXISTS vector` — **PG image 必須預裝 pgvector**，否則部署
會 fail。本專案統一用 `pgvector/pgvector:pg16`（dev / prod 一致）。

---

## 環境變數分層（roadmap 4-2a）

三套環境配置，**禁止混用**：

| 環境 | 範本 | 來源 | 敏感資訊處理 |
|------|------|------|----------------|
| **本機 dev**（backend）| `backend/.env.example` → `backend/.env` | 開發者本機檔案 | 視個人安全習慣 |
| **本機 dev**（web）| `web/.env.example` → `web/.env.local` | 開發者本機檔案 | 同上 |
| **Self-host prod** | `.env.prod.example` → `.env.prod` | 部署 VPS 上的 dotenv 檔 | 強隨機密碼 + .gitignore 防誤 commit |
| **Zeabur prod** | （無檔案）| Zeabur dashboard 的 Project env | 必須在 dashboard 標記為 **Secret**（隱藏顯示）|

### 變數分類一覽

| 變數 | 是否敏感 | dev | self-host prod | Zeabur prod |
|------|---------|-----|----------------|-------------|
| `OPENAI_API_KEY` | 🔒 敏感 | backend/.env | .env.prod | Zeabur **Secret** |
| `GOOGLE_CLIENT_SECRET` | 🔒 敏感 | backend/.env | .env.prod | Zeabur **Secret** |
| `AUTH_SECRET` / `NEXTAUTH_SECRET` | 🔒 敏感 | 各自 .env | .env.prod | Zeabur **Secret** |
| `POSTGRES_PASSWORD` | 🔒 敏感 | docker-compose.dev.yml hardcode | .env.prod | Zeabur 自動產生（`${PASSWORD}`） |
| `JUDGE0_API_KEY` | 🔒 敏感（RapidAPI）| backend/.env | .env.prod | Zeabur **Secret** |
| `JUDGE0_POSTGRES_PASSWORD` / `JUDGE0_REDIS_PASSWORD` | 🔒 敏感 | — | .env.prod + judge0.conf | Zeabur 不適用 |
| `GOOGLE_CLIENT_ID` | 公開 | 各自 .env | .env.prod | Zeabur 一般 env |
| `DATABASE_URL` / `REDIS_URL` | 公開 | dev hardcode | .env.prod 拼裝 | Zeabur 用 `${POSTGRES_HOST}` 等引用 |
| `WEB_URL` / `NEXTAUTH_URL` | 公開 | localhost | .env.prod | Zeabur `${WEB_DOMAIN}` |
| `LLM_MODEL` / `EMBEDDING_MODEL` / `LOG_LEVEL` | 公開 | 預設值 | 預設值 | 預設值（如需覆寫才設）|

> **Zeabur Secret 標記方式**：Project Settings → Environment Variables → 點 variable 詳情 →
> 將「Hidden」/「Secret」開關打開。標記後 dashboard 不再顯示原值，也不會出現在 log 中。

---

## §A. Zeabur 部署

## 前置條件

- Zeabur 帳號 + Project 建立完成
- Google OAuth credentials（已設定 redirect URI 為正式 domain）
- OpenAI API Key
- Judge0 API URL + Key

## Step 1：透過 zeabur.json 部署

`zeabur.json` 已配置 4 個服務：
1. **postgres** — `template: PREBUILT` + `source.image: pgvector/pgvector:pg16`（自架 pgvector）
2. **redis** — marketplace
3. **backend** — Git source + Dockerfile（`backend/`）
4. **web** — Git source + Dockerfile（`web/`）

> **若 Zeabur 拒絕 `template: PREBUILT` + `source.type: IMAGE` schema**：
> 改用 marketplace pgvector 服務（在 Zeabur dashboard 搜尋 "pgvector"），或建一個
> Git service 指向 `pgvector/` 目錄（內含一行 `FROM pgvector/pgvector:pg16` 的 Dockerfile）。
> 普通 marketplace `postgresql` 不含 pgvector，**不可使用**。

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
| Migration 失敗 `CREATE EXTENSION vector`：permission denied / type "vector" does not exist | PG 不是 pgvector image —— 換用 `pgvector/pgvector:pg16` |
| Migration 失敗（其他） | 查看 backend logs，確認 PostgreSQL 已啟動 |

---

## §B. Self-host VPS 部署（docker-compose.prod.yml）

適用：有自己 VPS（如 Tencent Tokyo）+ 想完全控制資料的場景。

### Step 1：準備 .env.prod

在專案根目錄建立 `.env.prod`（**勿 commit**）：

```bash
# DB
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<強隨機密碼>
POSTGRES_DB=programing_education

# Auth
AUTH_SECRET=<npx auth secret 產生>
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
WEB_URL=https://your-domain.com

# AI
OPENAI_API_KEY=sk-proj-...

# Judge0（自架）
JUDGE0_API_URL=http://judge0:2358
JUDGE0_API_KEY=
```

### Step 2：啟動

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

首次啟動 backend 會自動跑 `alembic upgrade head`（含 CREATE EXTENSION vector）。

### Step 3：反向代理

`docker-compose.prod.yml` 只暴露 web 的 3000 port。建議前置 nginx / caddy 提供 HTTPS：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    ssl_certificate ...;
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Step 4：健康檢查

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
# 確認 postgres / redis / backend / web 都是 healthy / running

curl http://localhost:3000/api/health
# {"status": "ok"}
```

### Self-host 疑難排解

| 問題 | 檢查 |
|------|------|
| backend 容器一直 restart | `docker compose ... logs backend` 查 alembic / DB 連線錯誤 |
| `vector` extension 找不到 | 確認 image 是 `pgvector/pgvector:pg16` 不是 `postgres:16` |
| Judge0 部分功能失效 | 見 §C 自架 Judge0 / 或在 .env.prod 改 JUDGE0_API_URL 為 RapidAPI |

---

## §C. Judge0 自架（取代 RapidAPI 50 次/天限制）

適用：self-host VPS（§B）情境；想擺脫 RapidAPI 配額或在內網執行學生程式碼。

### ⚠ Zeabur 不支援

Judge0 worker 需要 **`privileged: true`**（用 Linux cgroups 對使用者程式做時間 / 記憶體 /
process 隔離）。Zeabur 等多數雲平台禁用 privileged container → **Zeabur 部署仍應走
RapidAPI Judge0**（在 Zeabur dashboard 為 backend 設 `JUDGE0_API_URL=https://judge0-ce.p.rapidapi.com`
+ `JUDGE0_API_KEY=<RapidAPI key>`）。

### Step 1：準備 judge0.conf

複製範本並填密碼：
```bash
cp judge0.conf.example judge0.conf
# 編輯 judge0.conf 把 REDIS_PASSWORD / POSTGRES_PASSWORD 填入強隨機值
```

### Step 2：補 .env.prod

把 §B 的 `.env.prod` 補上 Judge0 自架密碼（與 judge0.conf 內**完全一致**）：
```bash
# Judge0 自架專用（與 judge0.conf 內密碼一致）
JUDGE0_POSTGRES_PASSWORD=<與 judge0.conf POSTGRES_PASSWORD 相同>
JUDGE0_REDIS_PASSWORD=<與 judge0.conf REDIS_PASSWORD 相同>

# backend 連 Judge0 改自架 endpoint
JUDGE0_API_URL=http://judge0-server:2358
JUDGE0_API_KEY=  # 自架不需 RapidAPI key
```

### Step 3：啟動 Judge0 stack

```bash
docker compose --env-file .env.prod -f docker-compose.judge0.yml up -d
# 等 ~30 秒 worker 啟動 + 註冊 languages

# 驗證
curl http://localhost:2358/about
# 應回 Judge0 metadata JSON（version / homepage 等）
```

### Step 4：合併 backend 與 Judge0 網路

`docker-compose.prod.yml` 與 `docker-compose.judge0.yml` 預設不同 docker network。
要讓 backend 用 service name 連線 Judge0，三種方式擇一：

1. **同 network（推薦）**：在兩個 compose 加共同 `networks:` 區塊（命名一致），backend 用 `JUDGE0_API_URL=http://judge0-server:2358`
2. **走 host.docker.internal**：backend 用 `JUDGE0_API_URL=http://host.docker.internal:2358`（Linux 需加 `extra_hosts`）
3. **同一個 compose**：把 docker-compose.judge0.yml 的服務 inline 進 docker-compose.prod.yml

### Step 5：驗證 backend 接通

進入 Workspace → 撰寫 C++ 程式 → 點「執行」→ Output panel 應顯示 stdout/stderr。

### Judge0 疑難排解

| 問題 | 檢查 |
|------|------|
| `/about` 502 / 連不上 | Judge0 worker 容器是否 healthy；`docker compose -f docker-compose.judge0.yml ps` |
| Worker 啟動 fail：privileged 被拒 | 主機 Docker daemon 是否啟用 privileged；雲平台需自己 VPS / 不能用 Zeabur |
| backend 端 Judge0 timeout | 確認 `JUDGE0_API_URL` 指對；workers 啟動較慢首次需等 30-60s |
| Submission 結果一直 status=1（in queue） | workers 容器沒起 / cgroups 不可用；查 worker logs |
