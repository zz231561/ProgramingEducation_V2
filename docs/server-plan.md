# 伺服器需求規劃（Phase 7 部署）

> 2026-07-12 定案兩台拓撲（B 機自架 Judge0）→ **2026-08-05 修訂：B 機改跑自建互動 runner**
> （nsjail 沙箱 + PTY + WebSocket），Judge0 降為 fallback（RapidAPI，`RUNNER_BACKEND` 切換）。
> 修訂理由：① 批次判題無法提供互動 `cin`（使用者定案需求：本地編譯器體驗）② 自架 Judge0
> 需 GRUB 切 cgroup v1 + privileged——把 B 機釘死在淘汰中機制 ③ RapidAPI 50 次/天不敷課堂。
> 舊自架 Judge0 SOP 保留於 `docs/deployment.md` §C 供追溯，不再是正式方案。

## 拓撲總覽

```
┌─ 伺服器 A（主機，Zeabur 託管）────────────┐   ┌─ 伺服器 B（Runner 專用）───────────┐
│ ProgramingEducation：                     │   │ codedge-runner（docker compose）   │
│  web (Next.js) / backend (FastAPI)        │──▶│  FastAPI + g++ + nsjail 沙箱       │
│  PostgreSQL(pgvector) / Redis             │   │  POST /run（批次）+ WS /terminal   │
│  backend 另綁公開子網域（WS 入口）        │   │ 防火牆：runner port 僅放行 A 機 IP │
└───────────────────────────────────────────┘   └────────────────────────────────────┘
     Browser ─wss→ A 機 backend ─中繼→ B 機（A→B 帶 X-Runner-Token 共享密鑰）
```

- 前端 WS **不經 Next.js proxy**（Route Handler 不支援 WebSocket）→ backend 需綁 Zeabur 公開子網域，JWT 於 WS 首訊息驗證
- **PokerNote_V2 留在原機不動**（2026-08-05 決策：搬遷有資料庫 dump/restore 風險，且原機取 VPS 密碼會失去 Zeabur 託管支援；B 機另租，總月費 $6+$3+$3=$12）

## 伺服器 A — 主機（不變）

| 項目 | 內容 |
|------|------|
| 用途 | 本專案 4 個 service（web / backend / postgres / redis） |
| 規格 | 2C8G ZeaburOS（實用約 2.5 GB，餘裕充足；編譯負載全在 B 機） |
| 託管 | Zeabur dashboard 部署，維持完整託管支援（**禁止取 VPS 密碼轉自管**） |

## 伺服器 B — Runner 專用機（2026-08-05 已租用並實測）

| 項目 | 內容 |
|------|------|
| 用途 | 僅跑自建 runner（執行任意學生 C++，與主資料物理隔離；**壞了即重灌**，不放任何 credential / 資料） |
| 實機 | `43.133.7.93` — 2 vCPU / 2 GB RAM（實測可用 ~1.5 GB）/ 40 GB disk（餘 33 GB），Tokyo |
| OS | 實測 Ubuntu 24.04（kernel 6.8 / OpenSSH 9.6p1 / apt 標 24.04.2；Zeabur 面板顯示 22.04，以實測為準） |
| cgroup | **v2 unified**（cpu / memory / pids / cpuset / io 齊全）→ **不需動 GRUB** |
| 登入 | `ubuntu@` SSH 金鑰（id_ed25519）+ 免密碼 sudo；密碼登入 R5 收斂禁用；authorized_keys 有重複金鑰一筆，R5 一併清 |
| 乾淨度 | 實測無 k3s / containerd / Zeabur agent（僅騰訊 tat_agent）＝純裸 VM，資源全歸 runner |
| 注意 | `apparmor_restrict_unprivileged_userns=1`：runner 容器以 root + `CAP_SYS_ADMIN` 跑 nsjail（不走非特權 userns）；若仍受阻 `sysctl -w kernel.apparmor_restrict_unprivileged_userns=0` |
| 支援 | 已取 VPS 密碼＝Zeabur 僅提供重灌服務——符合「自管、壞了即重灌」定位 |

### Runner 資源參數（2026-08-05 定案）

| 參數 | 值 | 依據 |
|------|-----|------|
| 並行編譯閘 | **2** | 可用 RAM 1.5 GB 的安全值；超出排隊並向前端回報「排隊中 n/m」 |
| swap | 2 GB | 吸收編譯尖峰（R5 建立） |
| 編譯上限 | CPU 10s / RAM 512MB | |
| 執行上限 | RAM 256MB / pids 64 / 輸出 8MB 截斷 | |
| 互動 session | idle 60s / 硬上限 300s / 同時上限 40 | 等待輸入時 CPU≈0、RAM 5–15MB/session |
| 加速 | 標準庫 PCH（本機實測 0.25s→0.09s）+ 編譯結果雜湊快取 | 教學程式 include 高度同質 |

### 安全硬性要求

- [ ] 防火牆（騰訊安全群組）：runner port 僅放行伺服器 A IP，禁止公網存取
- [ ] A→B 請求一律帶 `X-Runner-Token` 共享密鑰（防火牆之外第二道縱深）
- [ ] SSH 金鑰登入、禁密碼（R5 執行；金鑰已裝妥）
- [ ] B 機不放任何 credential / 資料（JWT 驗證在 A 機 backend 完成後才中繼）
- [ ] nsjail：`--network none`、唯讀 rootfs、cap-drop ALL、非特權 uid 執行學生程式

## 容量假設與依據

- 課堂尖峰：30–60 名學生；最壞情境＝全班同步按 Run
- 2 併發編譯 × ~0.3s/支（PCH 後，雲端 x86 估值）→ 30 人序列化最後一人約 6 秒（前端顯示排隊位置）
- RAM 峰值：30 互動 session ≈ 0.45 GB + 2 併發編譯 ≈ 0.6 GB → 合計 ~1.2 GB < 1.5 GB 可用（swap 兜底）
- 規模擴大：升 4C4G 並調高編譯閘即可，A 機不受影響

## 環境變數（backend，詳見 `.claude/rules/backend.md`）

| 變數 | 值 |
|------|-----|
| `RUNNER_BACKEND` | `self`（預設）/ `judge0`（B 機故障時降級 RapidAPI 批次） |
| `RUNNER_URL` | `http://43.133.7.93:<port>` |
| `RUNNER_TOKEN` | 共享密鑰（Zeabur Secret） |

## 待辦

- [x] B 機租用 + SSH 金鑰 + 硬體實測全綠（2026-08-05）
- [ ] R5：swap + docker + runner 部署 + 防火牆 + 禁密碼 + 健康檢查（見 roadmap 7-R）
- [ ] backend 綁 Zeabur 公開子網域（WS 直達；使用者已確認可綁）
- [ ] 課堂規模壓測：30 並行提交（R6）
