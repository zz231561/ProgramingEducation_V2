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
- Judge0：Zeabur 託管的 service 不能跑 self-host Judge0（見 §C 警告）。兩種選擇：
  - **正式方案（2026-07-12 定案）**：另租一台 VPS 自架 Judge0，backend 設 `JUDGE0_API_URL=http://<伺服器B IP>:2358` + `JUDGE0_API_KEY=<authn token>` — 拓撲見 `docs/server-plan.md`
  - 過渡方案：RapidAPI（免費 50 次/天，僅夠冒煙測試）

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

### web service 的 Node 執行參數（2026-08-05 上線實測）

**已寫入 `web/Dockerfile`（烘進映像）+ `zeabur.json`，重建服務會自動帶入，dashboard 無需手動設定**：

| 變數 | 值 | 為什麼 |
|------|-----|--------|
| `NODE_OPTIONS` | `--dns-result-order=ipv4first` | 容器內 Node 18+ 預設 IPv6 優先，Zeabur 容器的 IPv6 無法路由外網 → **每次 DNS 解析都要等逾時才 fallback** |
| `UV_THREADPOOL_SIZE` | `32` | Node 的 DNS 查詢走 libuv threadpool（**預設僅 4 執行緒**）。上述逾時會佔滿它，導致同 process 的所有請求排隊 |

> 驗證方式：`docker run <image> node -e "console.log(require('dns').getDefaultResultOrder())"` 應回 `ipv4first`。
> ⚠ Zeabur dashboard 的手動環境變數會**覆蓋** Dockerfile 的 `ENV`——若曾手動設過，請確認值一致或直接移除。

**實測症狀**：`/api/auth/session` 首次請求卡 **2.2 分鐘**，期間所有 `/api/*` 全數 5 秒逾時（前端 health check 的 AbortController 上限），頁面因此停在 loading——但後端本身每個端點只要 2–10ms，從外部 curl 測也一切正常，**只有瀏覽器情境才會觸發**。

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
- [ ] `requirements.lock` 與 `pyproject.toml` 同步（改過 dependencies 後必須 `uv pip compile pyproject.toml -o requirements.lock` 重產；Dockerfile 只讀 lock，漏套件＝容器啟動即崩）
- [ ] 部署完成後回 Google Console 補 redirect URI

## 疑難排解

| 問題 | 檢查 |
|------|------|
| **整站極慢（頁面 10 秒以上）但後端 API 實測 2–10ms** | 見上方「web service 必要的 Node 執行參數」；另檢查回應是否帶 `alt-svc: h3`（HTTP/3 問題，見下） |
| **靜態資源下載僅數 KB/s，curl 卻正常** | 瀏覽器走了 HTTP/3（UDP）。`next.config.ts` 已設 `Alt-Svc: clear` 強制留在 HTTP/2；驗證方式：Console 執行 `performance.getEntriesByType('resource').map(r=>r.nextHopProtocol)`，應全為 `h2` |
| Template deploy 失敗：unknown schema field | Zeabur 不接受 `source.type: IMAGE`；用 fallback（marketplace pgvector / GIT + Dockerfile）|
| 502 Bad Gateway | web 的 `BACKEND_URL` 是否正確（應為 `http://${BACKEND_HOST}:8000`，由 backend service expose）|
| backend 502 / 一直 restart | 看 logs：alembic 失敗或 DATABASE_URL 拼錯 |
| DB 連線失敗 | `DATABASE_URL` 格式是否為 `postgresql+asyncpg://...`（非 `postgresql://`）|
| OAuth 失敗 redirect_uri_mismatch | Google Console redirect URI 是否含 `https://<web-domain>/api/auth/callback/google` |
| Migration 失敗 `CREATE EXTENSION vector`：permission denied / type "vector" does not exist | PG 不是 pgvector image —— Step 1 fallback 切換 |
| 變數 `${BACKEND_HOST}` 解析失敗 | 確認 zeabur.json 的 backend service 含 `BACKEND_HOST` expose（4-2b 已加；舊版 zeabur.json 漏）|

---

## §D. NextAuth callback URL 與 CORS 機制（roadmap 4-2c）

### Callback URL 是怎麼產生的

NextAuth v5 的 OAuth callback URL 規則：
- 路徑固定：`/api/auth/callback/{provider}` →  Google 是 `/api/auth/callback/google`
- 主機名來自：**`AUTH_TRUST_HOST=true`** 時讀 `X-Forwarded-Host` header，否則讀容器 internal hostname

→ 所以 **生產環境（Zeabur / nginx 反代後）必須設 `AUTH_TRUST_HOST=true`**，不然 callback 會變
`https://<container-hostname>/api/auth/callback/google` 而非 `https://your-domain.com/...`，導致：
- Google Console redirect URI 無法對齊（即使你填了正式 domain）
- 出現 `redirect_uri_mismatch` 錯誤

### 三種環境的設定

| 環境 | `AUTH_TRUST_HOST` | Google Console redirect URI |
|------|-------------------|----------------------------|
| Dev (localhost) | 不需設（NextAuth 自動 trust localhost）| `http://localhost:3000/api/auth/callback/google` |
| Self-host prod | `.env.prod` 中設 `AUTH_TRUST_HOST=true` | `https://your-domain.com/api/auth/callback/google` |
| Zeabur prod | zeabur.json web env 已含（4-2c 加）| `https://<your-zeabur-domain>/api/auth/callback/google` |

### 後端 CORS 設計

backend `core/config.py` 的 `cors_origins` property：
```python
return [self.NEXTAUTH_URL.rstrip("/")]
```

- 只允許 `NEXTAUTH_URL` 一個 origin（無 wildcard）
- **rstrip 防呆**：`https://domain.com/` 與 `https://domain.com` 對 CORSMiddleware 是不同字串
- 多 staging origin 場景目前不支援（YAGNI；未來真的要再改 list）

### 為什麼前後端同 domain 仍要設 CORS

本專案架構：
```
Browser → web (Next.js, /api/* proxy 到 backend) → backend (FastAPI)
```

瀏覽器只看到 web origin，**不直接打 backend** → 不會跨域。但 CORS 仍保留作為**防禦深度**：
- 萬一未來某 endpoint 直接暴露給 browser（如 SSE 串流不走 proxy）
- 萬一 proxy 配置變動讓部分請求繞過

→ 多此一舉的安全網成本 < 0；保留。

### 疑難排解（NextAuth）

| 錯誤訊息 | 檢查 |
|---------|------|
| `redirect_uri_mismatch`（Google）| Google Console redirect URI 是否含 `/api/auth/callback/google` 完整路徑（含 https） |
| Login 後 redirect 到 `localhost` 或 internal hostname | `AUTH_TRUST_HOST=true` 是否設定（Zeabur web service env / .env.prod）|
| `NEXTAUTH_SECRET` mismatch | backend `NEXTAUTH_SECRET` 與 web `AUTH_SECRET` 必須**完全一致**（zeabur.json 已用 `${AUTH_SECRET}` 同 source）|
| CORS preflight 失敗（OPTIONS 401）| 確認 backend `NEXTAUTH_URL` 與 web 實際 origin 一致（含 scheme + 無尾斜線）|

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

---

## §E. Runner 自架（7-R 正式方案，2026-08-05 取代 §C）

> B 機 = 互動執行引擎專用機。規格與參數見 `docs/server-plan.md`；
> 程式碼在 `runner/`。**B 機不放任何 credential，壞了即重灌。**

### Step 0：本機把 runner 送上 B 機

```bash
# 在專案根目錄（不要 rsync .env / .git）
rsync -av --exclude '.env' --exclude '__pycache__' --exclude '.pytest_cache' \
  runner/ ubuntu@<B機IP>:~/runner/
```

### Step 1：一次性初始化（swap / docker / 防火牆 / SSH 收斂）

先確認 **A 機公網 IP**（Zeabur backend 的對外出口）。若不確定，用下面的
「來源 IP 探測」取得，不要先開放全網。

```bash
ssh ubuntu@<B機IP>
sudo bash ~/runner/bootstrap.sh <A機公網IP>
```

腳本冪等，內容：swap 2G + `vm.swappiness=10` / 安裝 docker / ufw 只放行 22 與
「A 機 → 8080」/ **補 `DOCKER-USER` 規則**（docker 會改 iptables 繞過 ufw，這是常見疏漏）
/ 關閉 SSH 密碼登入 / 清理重複公鑰。

> **來源 IP 探測**（不需開放全網）：先跑 bootstrap 帶一個暫用 IP，
> 再 `sudo ufw logging on`，從前端觸發一次執行，然後
> `sudo grep 'DPT=8080' /var/log/ufw.log | tail -3` 讀出真正的 `SRC=`，
> 以 `sudo ufw allow from <真IP> to any port 8080 proto tcp` 補上、刪掉暫用那條。

### Step 2：設定 token 並部署

```bash
cd ~/runner
cp .env.example .env
openssl rand -hex 32          # 產生 token，記下來（A 機要用同一組）
nano .env                     # 填入 RUNNER_TOKEN
bash deploy.sh
```

`deploy.sh` 會 build → up → 等 healthy → 本機冒煙測試，最後應印出
`"stdout":"runner ok"`。首次 build 需編譯 nsjail 與 PCH，約 5–10 分鐘。

### Step 3：A 機（Zeabur dashboard）設定

1. **backend service → Domains → Generate Domain**（例如 `api-codedge.zeabur.app`）
   — WS 必須直連 backend，Next.js Route Handler 無法 proxy WebSocket
2. **backend service → Variables**：
   | 變數 | 值 |
   |------|-----|
   | `RUNNER_BACKEND` | `self` |
   | `RUNNER_URL` | `http://<B機IP>:8080` |
   | `RUNNER_TOKEN` | 🔒 Secret，與 B 機 `.env` 同值 |

   ⚠ **設完必須重啟 backend service**，否則變數不會被讀入（實測卡點）。
3. **web service → Variables**：
   | 變數 | 值 |
   |------|-----|
   | `NEXT_PUBLIC_TERMINAL_WS_URL` | `wss://api-codedge.zeabur.app/terminal/ws` |

   ⚠ `NEXT_PUBLIC_*` 是**建置期**烘入，設定後必須 **redeploy web service** 才生效。
4. backend CORS 需允許 web 網域（既有 `NEXTAUTH_URL` 機制，見 §D）

### Step 4：驗收

| 檢查 | 方法 | 預期 |
|------|------|------|
| B 機健康 | `curl -s localhost:8080/healthz`（B 機上） | `{"status":"ok","sandbox":"nsjail",...}` |
| 防火牆生效 | 從自己電腦 `curl http://<B機IP>:8080/healthz` | **連不上**（逾時） |
| 批次路徑 | 前端跑一支無輸入的程式 | 正常輸出 |
| **互動路徑** | 跑含 `cin` 的程式 | 終端機出現提示字 → 打字 → 程式收到 |
| 降級保護 | B 機 `docker compose stop` → 前端再跑一次 | 自動退回批次，學生無感 |

### 回滾

Zeabur backend 設 `RUNNER_BACKEND=judge0`（或清空 `RUNNER_URL`）即刻退回
RapidAPI 批次，不需重新部署程式碼。

### ⚠ 已知限制：A↔B 走明文 HTTP

B 機無網域故無 TLS 憑證，`RUNNER_TOKEN` 與學生程式碼以明文往返公網。
現行防線＝雙層防火牆（ufw + 騰訊安全群組）鎖來源 IP + token。
**風險評估**：B 機不含任何機密、被攻陷即重灌；最壞情況是被當免費算力。
**改善選項**（記於 tech-debt）：① B 機掛自訂子網域 + Caddy 自動 TLS
② A↔B 建 WireGuard 隧道並改綁 127.0.0.1。

### 疑難排解

| 症狀 | 檢查 |
|------|------|
| 前端永遠走批次（不進終端機） | ① **backend 是否已重啟**——環境變數要重啟才讀入，這是 2026-08-06 實際卡住的原因 ② `NEXT_PUBLIC_TERMINAL_WS_URL` 是否設了且 **web 已 redeploy** ③ DevTools Network 看 `/terminal/ticket` 是否 503。**快速判別**：B 機 `sudo docker logs codedge-runner` 若連 `POST /run` 都沒有來自 A 機的紀錄，就是 backend 沒讀到 `RUNNER_URL`（因批次路徑也會打 runner） |
| ticket 200 但 WS 連不上 | backend 是否已綁公開網域；`wss://` 對應 https 前端（混合內容會被瀏覽器擋） |
| WS 開了但沒有輸出 | B 機 `docker logs codedge-runner`；防火牆是否放行 A 機**實際**出口 IP |
| 編譯報 nsjail 相關錯誤 | `docker exec codedge-runner nsjail --help`；確認 compose 的 `cap_add: SYS_ADMIN` 與 `apparmor:unconfined` 有生效 |
| 執行很慢 / 常排隊 | `curl localhost:8080/healthz` 看 `queue_depth`；必要時調 `RUNNER_GATE_SLOTS`（受 RAM 限制，見 server-plan） |
