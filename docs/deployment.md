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

- Zeabur 帳號（無需先建 Project — template deploy 會自動建）
- Google OAuth credentials
  - 在 Google Cloud Console 先建 OAuth Client
  - **Authorized redirect URI** 暫填佔位（部署完拿到 web domain 後再回頭補；見 §A Step 5）
- OpenAI API Key（已啟用 GPT-4o + text-embedding-3-small）
- Judge0：選 RapidAPI（Zeabur 不能跑 self-host Judge0；見 §C 警告）

## Service 串接架構

`zeabur.json` 定義 4 個 service 與其變數引用鏈：

```
postgres (pgvector image, expose POSTGRES_HOST/PORT/DATABASE/USERNAME/PASSWORD)
  ↓ 引用變數
backend (Dockerfile build, expose BACKEND_HOST)
  ↓ 引用變數
web (Dockerfile build, domain key WEB_DOMAIN)

redis (image redis:7-alpine, expose REDIS_HOST/REDIS_PORT)
  ↓ 引用變數
backend
```

**Zeabur 變數插值規則**：
- `${POSTGRES_HOST}` 等 expose 變數會自動跨 service 解析
- `${CONTAINER_HOSTNAME}` 由 Zeabur 注入（每個 service 自己的內部 DNS 名稱）
- `${PASSWORD}` 由 Zeabur 自動產生強隨機密碼（用於 POSTGRES_PASSWORD）
- `${WEB_DOMAIN}` 由 web service 的 domainKey 產生（綁定 domain 後可用）

## Step 1：使用 zeabur.json 部署

最簡途徑：在 Zeabur dashboard 用 "Deploy from template" 上傳 `zeabur.json`，
或安裝 [Zeabur CLI](https://zeabur.com/docs/zh-TW/devops/zeabur-cli) 後：

```bash
# 在 repo 根目錄
zeabur template deploy --file zeabur.json
```

四個 service 會一次建好：postgres / redis / backend / web。

> **若 Zeabur 拒絕 `template: PREBUILT` + `source.type: IMAGE` schema**（兩處 — postgres / redis）：
> 1. 移除 `source.type` + `source.image`，改回 `source: "MARKETPLACE"` + `id: "pgvector"`（如有）
> 2. 或建一個 GIT service 指向含一行 `FROM pgvector/pgvector:pg16` 的 Dockerfile
>
> Redis 同理可改 marketplace `redis`。**標準 marketplace `postgresql`（無 pgvector）不可使用**。

## Step 2：在 Zeabur dashboard 設定 Project Variables

zeabur.json 內的 `${VAR}` 會從 Project 層級的變數解析。在 Project Settings → Variables 設：

| 變數 | 值 | Secret? |
|------|------|---------|
| `AUTH_SECRET` | `npx auth secret` 產生的 32+ 字元 random | 🔒 |
| `AUTH_GOOGLE_ID` | Google OAuth Client ID | 公開 |
| `AUTH_GOOGLE_SECRET` | Google OAuth Client Secret | 🔒 |
| `OPENAI_API_KEY` | `sk-proj-...` | 🔒 |
| `JUDGE0_API_URL` | `https://judge0-ce.p.rapidapi.com` | 公開 |
| `JUDGE0_API_KEY` | RapidAPI Key | 🔒 |

> **`POSTGRES_PASSWORD` 不需手動設**：zeabur.json 用 `${PASSWORD}`，Zeabur 自動產生。
> **Secret 標記方式**：見上方「環境變數分層」章節。

## Step 3：綁定 web domain

1. Zeabur dashboard → web service → Domains → 綁定自訂域名（或用免費 `.zeabur.app`）
2. 等 SSL 自動下發
3. domain 對應的變數 `${WEB_DOMAIN}` 自動填入 backend `NEXTAUTH_URL=https://${WEB_DOMAIN}`

## Step 4：等部署完成 + 驗證

部署順序（Zeabur 會依依賴鏈處理）：postgres → redis → backend → web。
backend 啟動時會自動跑 `alembic upgrade head`，含 `CREATE EXTENSION vector`。

Health check：
```bash
curl https://<your-web-domain>/api/health
# → {"status": "ok"}
```

## Step 5：補上 Google OAuth redirect URI

回 Google Cloud Console → Credentials → 編輯 OAuth Client → **Authorized redirect URIs** 加：
- `https://<your-web-domain>/api/auth/callback/google`

接著測 Golden path：
1. 開啟前端 Domain → 應看到登入頁
2. Google OAuth 登入 → 成功進入 Workspace
3. 撰寫 C++ 程式 → 點擊 Run → Output Panel 顯示結果
4. 開啟 Chat Panel → 發送訊息 → AI 回覆正常

## 部署 checklist（實際操作前 dry-run）

- [ ] Google Cloud OAuth Client 已建（先填佔位 redirect URI）
- [ ] OpenAI API Key 已備好
- [ ] RapidAPI Judge0 帳號 + key 已備好
- [ ] `npx auth secret` 已產生 AUTH_SECRET
- [ ] Zeabur 帳號 + 信用卡已 ready（生產實例需付費 plan）
- [ ] `zeabur.json` 已 commit 到 repo（最新版含 4-2b 改動）
- [ ] `requirements.lock` 已是 4-1a 後的 272 行版（`grep -c '==' backend/requirements.lock` 應 ≥ 100）
- [ ] 部署完成後回 Google Console 補 redirect URI

## 疑難排解

| 問題 | 檢查 |
|------|------|
| Template deploy 失敗：unknown schema field | Zeabur 不接受 `source.type: IMAGE`；用 fallback（marketplace pgvector / GIT + Dockerfile）|
| 502 Bad Gateway | web 的 `BACKEND_URL` 是否正確（應為 `http://${BACKEND_HOST}:8000`，由 backend service expose）|
| backend 502 / 一直 restart | 看 logs：alembic 失敗或 DATABASE_URL 拼錯 |
| DB 連線失敗 | `DATABASE_URL` 格式是否為 `postgresql+asyncpg://...`（非 `postgresql://`）|
| OAuth 失敗 redirect_uri_mismatch | Google Console redirect URI 是否含 `https://<web-domain>/api/auth/callback/google` |
| Migration 失敗 `CREATE EXTENSION vector`：permission denied / type "vector" does not exist | PG 不是 pgvector image —— Step 1 fallback 切換 |
| 變數 `${BACKEND_HOST}` 解析失敗 | 確認 zeabur.json 的 backend service 含 `BACKEND_HOST` expose（4-2b 已加；舊版 zeabur.json 漏）|

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
