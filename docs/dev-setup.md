# 本機開發環境 SOP

> **每次 session 開頭先檢查本文件 §1**，確認服務都跑起來再開始開發。
> 與 Zeabur 部署無關 — 本機 dev 工具不會影響部署流程（部署走 `zeabur.json`）。

---

## 1. 每次 session 啟動流程（已裝完工具的情況）

### 🟢 最小啟動（DB + Redis，2-1b 開發只需這段）

**一鍵指令（複製整段貼上）：**
```bash
colima start && \
cd /Users/hao/Desktop/Project/ProgramingEducation_V2 && \
docker-compose -f docker-compose.dev.yml up -d && \
docker exec codedge-postgres-dev pg_isready -U postgres -d programing_education && \
docker exec codedge-postgres-dev psql -U postgres -d programing_education -c "\dx vector" && \
cd backend && .venv/bin/alembic current
```

**預期最後一行輸出**：`b2c3d4e5f6a7 (head)` → 環境 OK。

**逐步版（出問題時方便定位失敗點）：**
```bash
# 1) 啟動 Docker daemon（Colima VM）
colima start

# 2) 切到專案根目錄並啟動 dev 容器（pgvector + redis）
cd /Users/hao/Desktop/Project/ProgramingEducation_V2
docker-compose -f docker-compose.dev.yml up -d

# 3) 確認 Postgres healthy + pgvector 啟用
docker exec codedge-postgres-dev pg_isready -U postgres -d programing_education
docker exec codedge-postgres-dev psql -U postgres -d programing_education -c "\dx vector"

# 4) 確認 Alembic migration 在最新版
cd /Users/hao/Desktop/Project/ProgramingEducation_V2/backend
.venv/bin/alembic current
# 預期顯示：b2c3d4e5f6a7 (head)
```

### 🟡 完整開發（再加後端 + 前端 server）

承接上面之後，分別開兩個 terminal：
```bash
# Terminal 1：後端 API server
cd /Users/hao/Desktop/Project/ProgramingEducation_V2/backend
.venv/bin/uvicorn main:app --reload --port 8000

# Terminal 2：前端 dev server
cd /Users/hao/Desktop/Project/ProgramingEducation_V2/web
npm run dev
```
開瀏覽器：http://localhost:3000

### 🔴 收工關閉

```bash
cd /Users/hao/Desktop/Project/ProgramingEducation_V2
docker-compose -f docker-compose.dev.yml down  # 容器停（資料保留）
colima stop                                     # 停 VM 釋放資源
```

> **資料持久化**：Postgres 資料存於 Docker volume `programingeducation_v2_postgres_data`。
> `down` 不會清資料；要清資料用 `docker-compose -f docker-compose.dev.yml down -v`。

### 📊 狀態檢查（除錯用）
```bash
docker ps                  # 看容器跑得如何
colima status              # 看 Colima VM 狀態
docker info | head -5      # 看 docker daemon 是否 ready
```

---

## 2. 已安裝工具清單

| 工具 | 版本 | 用途 | 安裝指令 |
|------|------|------|---------|
| **Colima** | 0.10.1 | Docker daemon (取代 Docker Desktop，避免 sudo 問題) | `brew install colima` |
| **docker CLI** | 29.4.1 | container 操作 | `brew install docker` |
| **docker-compose** | v2 (5.1.3) | compose 檔案執行 | `brew install docker-compose` |
| **uv** | 0.11.8 | Python 套件管理（繞過 brew Python 3.12 在 macOS Tahoe 的 expat bug） | `brew install uv` |
| **portable Python 3.12.13** | by uv | backend venv 用 | (uv 自動下載) |

---

## 3. 後端 venv 操作

```bash
cd backend

# 啟動 venv
source .venv/bin/activate

# 安裝套件（用 uv 而非 pip）
uv pip install <package>

# 跑 migration
.venv/bin/alembic upgrade head
.venv/bin/alembic revision -m "描述"  # 建新 migration

# 啟動後端 server
.venv/bin/uvicorn main:app --reload --port 8000
```

> **venv 用 uv 建，沒裝 `pip`**。一律用 `uv pip install` 取代 `pip install`。

---

## 4. 服務連線資訊（本機 dev）

| 服務 | URL/連線字串 |
|------|-------------|
| Postgres | `postgresql+asyncpg://postgres:postgres@localhost:5432/programing_education` |
| Redis | `redis://localhost:6379/0` |
| 後端 API | `http://localhost:8000`（`uvicorn` 啟動後）|
| 前端 | `http://localhost:3000`（`web/` 跑 `npm run dev`）|

帳密與 `backend/.env`、`docker-compose.dev.yml` 對齊。

---

## 5. 與 Zeabur 部署的關係

| 項目 | 本機 dev | Zeabur prod |
|------|---------|-------------|
| Postgres image | `pgvector/pgvector:pg16`（docker-compose.dev.yml）| 目前 marketplace `postgresql`，**Phase 4-1b 會替換為 pgvector spec** |
| migration | `.venv/bin/alembic upgrade head` | 容器啟動腳本 `backend/start.sh` 同指令 |
| `DATABASE_URL` | 寫死於 `backend/.env` | `zeabur.json` 注入 |
| Docker daemon | Colima | Zeabur 平台自管 |

**關鍵約束**：本機 docker-compose.dev.yml **不進部署路徑**。Zeabur 走 `zeabur.json`。

---

## 6. 首次安裝（如果換新機器）

```bash
# 1) 安裝 brew（如已有跳過）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2) 一次裝全部工具
brew install colima docker docker-compose uv

# 3) 啟動 Colima（首次會下載 VM image，約 1-2 分鐘）
colima start --cpu 2 --memory 4 --disk 30

# 4) 建立 backend venv + 裝依賴
cd backend
uv venv --python 3.12 .venv
uv pip install \
  "fastapi>=0.115,<1" "uvicorn[standard]>=0.34,<1" "pydantic>=2.10,<3" \
  "pydantic-settings>=2.7,<3" "sqlalchemy[asyncio]>=2.0,<3" "asyncpg>=0.30,<1" \
  "redis>=5.2,<6" "python-dotenv>=1.0,<2" "authlib>=1.3,<2" "cryptography>=42,<45" \
  "PyJWT>=2.8,<3" "openai>=1.50,<3" "httpx>=0.28,<1" "pgvector>=0.3,<1" \
  "alembic>=1.13,<2"

# 5) 複製 env 設定（OPENAI_API_KEY 自行填入）
cp .env.example .env
$EDITOR .env

# 6) 啟動容器 + 跑 migration
cd ..
docker-compose -f docker-compose.dev.yml up -d
cd backend && .venv/bin/alembic upgrade head
```

---

## 7. 疑難排解

| 症狀 | 解法 |
|------|------|
| `docker compose` 找不到指令 | 改用 `docker-compose`（hyphenated）。brew 的 docker 沒掛 plugin。 |
| `colima start` 失敗 | `colima delete` 後重來；或檢查 `colima status` 看詳細錯誤 |
| Postgres 無法連線 | `docker exec codedge-postgres-dev pg_isready -U postgres`；不行就 `docker-compose -f docker-compose.dev.yml restart postgres` |
| `pip install` 找不到 pip | venv 是 uv 建的、沒裝 pip。改用 `uv pip install` |
| Python `Symbol not found: _XML_SetAllocTrackerActivationThreshold` | brew Python 3.12 在 macOS Tahoe 的 expat bug。venv 必須用 uv 自帶的 portable Python，不要用 brew python3.12 |
