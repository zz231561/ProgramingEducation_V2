# 伺服器需求規劃（Phase 7 部署）

> 2026-07-12 定案：**兩台伺服器拓撲**。背景：Judge0 RapidAPI 託管成本高（免費 50 次/天不敷課堂使用、
> 付費 $10+/月訂閱制），改為自架 Judge0；但 Judge0 worker 需要 `privileged: true` + cgroup v1，
> 不能與主服務混跑於 Zeabur 託管流程，故獨立一台。程式碼零改動（`services/judge0.py` 已支援無 key 自架模式）。

## 拓撲總覽

```
┌─ 伺服器 A（主機，Zeabur 託管）────────────┐   ┌─ 伺服器 B（Judge0 專用）──────────┐
│ PokerNote_V2（既有專案）                  │   │ Judge0 CE 1.13.1（docker-compose）│
│ ProgramingEducation：                     │   │  ├─ server + workers ×2          │
│  web (Next.js) / backend (FastAPI)        │──▶│  └─ 自帶 postgres + redis        │
│  PostgreSQL(pgvector) / Redis             │   │ 防火牆：2358 僅允許伺服器 A IP    │
└───────────────────────────────────────────┘   └───────────────────────────────────┘
         backend 以 JUDGE0_API_URL + authn token 呼叫 B
```

## 伺服器 A — 主機

| 項目 | 內容 |
|------|------|
| 用途 | PokerNote_V2 + 本專案 4 個 service（web / backend / postgres / redis） |
| 建議規格 | **4 vCPU / 8 GB RAM**（最低 2C4G，前提：PokerNote_V2 負載持續輕量） |
| 區域 | Tokyo（維持與使用者低延遲） |
| 託管 | **Zeabur dedicated server**，全部 service 走 Zeabur dashboard 部署（`zeabur.json` 現成） |
| 部署 SOP | `docs/deployment.md` §A |

### RAM 預算（穩態）

| 元件 | 估算 |
|------|------|
| Zeabur agent（k3s）開銷 | 0.7–1 GB |
| PokerNote_V2 | 0.5–1 GB |
| web + backend + PostgreSQL + Redis | 1.3–1.5 GB |
| 餘裕（LLM 請求尖峰 / OS cache） | 其餘 |

## 伺服器 B — Judge0 專用機

| 項目 | 內容 |
|------|------|
| 用途 | 僅跑自架 Judge0 CE（執行任意學生 C++ 程式碼，**與主資料物理隔離**） |
| 建議規格 | **2 vCPU / 2 GB RAM**，Ubuntu 22.04（cgroup v1 開機參數相容性最佳） |
| 區域 | Tokyo（與 A 同區降低 polling 延遲） |
| 租用 | 可透過 Zeabur 租用計費；**部署不走 Zeabur dashboard**（見下） |
| 部署 SOP | `docs/deployment.md` §C（`judge0.conf.example` 現成） |

### ⚠ 為什麼 B 不能走 Zeabur dashboard 部署

1. Judge0 worker 需要 `privileged: true`，Zeabur 的 k8s 託管流程不允許 privileged pod。
2. Judge0 1.13.1 需要主機 GRUB 加 `systemd.unified_cgroup_hierarchy=0`（切回 cgroup v1）並重開機——全機設定，不能只影響單一容器。

→ 操作方式：SSH 上主機 → 改 GRUB 重開機 → `docker compose up -d`（Zeabur 文件允許
dedicated server「停用 Zeabur 服務自由使用」）。**租用前必須確認該方案提供 SSH root 權限。**

### 安全硬性要求（跑任意學生程式碼）

- [ ] `judge0.conf` 啟用 **authn token**，backend 請求帶 token
- [ ] 防火牆（騰訊安全群組）：2358 port 僅放行伺服器 A 的 IP，禁止公網存取
- [ ] SSH 改用金鑰登入、禁密碼
- [ ] 這台機器上**不放任何其他服務與資料**（定位：壞了即重灌）

## 容量假設與依據

- 課堂尖峰：30–60 名學生同時上課，突發 5–10 個並行執行請求。
- Judge0 2 workers + 佇列可消化（單次編譯+執行約 1–3 秒；backend polling 上限 12 秒）。
- 每個並行 g++ 編譯瞬時吃 0.2–0.5 GB RAM → B 機 2 GB 對 2 workers 足夠。
- 若日後規模擴大（多班並行）：B 機升 4C4G 並調高 worker 數即可，A 機不受影響。

## 環境變數變更（相對 RapidAPI 方案）

| 變數 | RapidAPI（舊） | 自架（新） |
|------|---------------|-----------|
| `JUDGE0_API_URL` | `https://judge0-ce.p.rapidapi.com` | `http://<伺服器B IP>:2358` |
| `JUDGE0_API_KEY` | RapidAPI key | Judge0 authn token（header 邏輯需小改，見下） |

> ⚠ 技術債：`services/judge0.py` `_build_headers()` 目前只支援 RapidAPI header
> （`X-RapidAPI-Key`）；自架 authn 用的是 `X-Auth-Token`。切換時需加一個 header 分支
> （約 5 行），已記入 `docs/tech-debt.md`。

## 待辦（租用後）

- [ ] 確認 Zeabur 租用方案含 SSH root 權限（B 機前提）
- [ ] A 機：Zeabur 部署 PokerNote_V2 + 本專案（deployment.md §A）
- [ ] B 機：GRUB cgroup v1 + docker-compose Judge0 + authn + 防火牆（deployment.md §C）
- [ ] backend `_build_headers()` 加自架 authn header 分支 + 測試
- [ ] 課堂規模壓測：模擬 30 並行提交，確認 polling 不逾時
