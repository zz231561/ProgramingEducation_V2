# ProgramingEducation V2 — 開發指揮中心

## 執行守則 (STRICT RULES)
1. **小步快跑**：每次對話僅限執行 Roadmap 中的「單一最小 Checkbox 任務」。
2. **強制中斷**：完成代碼修改後立即停止，提示使用者手動測試。
3. **禁止擅自推進**：等待使用者回覆「測試通過」才可勾選 Checkbox 並開始下一任務。
4. **狀態同步**：任務確認後優先更新對應文件的 Checkbox `[x]`。
5. **專業匯報**：簡述修改對架構的影響，確認是否符合工程規範。
6. **強制文檔同步**：每次指令完成後**必須**更新：
   - `docs/changelog.md` — 新增變更記錄行
   - `docs/roadmap.md` — 勾選 Checkbox（**僅一行摘要**，細節歸 changelog）
   - `CLAUDE.md` 當前狀態 — 反映最新進度
   - `docs/tech-debt.md` — 若產生或消除技術債
7. **改檔案一律用 Edit/Write 工具**：**禁止**用 `python3 - <<EOF` / `sed -i` / `cat >` 等 shell 手法改動專案檔案——那是任意程式碼執行、diff 不可見、且會繞過權限確認。批次改動就多呼叫幾次 Edit。
8. **避免重複造輪子（OSS 優先）**：開發新功能前必先查 `docs/references.md` §1 決策矩陣。**禁止移植已有對應套件的演算法**（例：BKT 必用 pyBKT）。**禁止引入 AGPL/GPL 授權套件**（見 references.md §2 黑名單）。
9. **當場修小問題**：發現的問題若**範圍小、根因明確、不需設計裁決**（過時文案、失效路徑、錯誤敘述、明顯 bug），**當輪直接修**，不要只記錄或延後、也不必先問。需要討論的只有三種：改動會擴散到其他模組、涉及架構或教學設計取捨、根因尚未確定。修完照守則 6 同步文檔。

## 技術棧（已鎖定）
- **前端**：Next.js 15 + TypeScript + Tailwind CSS（`web/`）
- **後端**：FastAPI + Python 3.12 + SQLAlchemy 2.0 async（`backend/`）
- **資料庫**：PostgreSQL + pgvector | **快取**：Redis
- **程式碼執行**：自建 runner（nsjail + PTY 互動終端，B 機）| fallback：Judge0
- **LLM**：OpenAI gpt-5.6（`luna` 對話/分析/生成、`terra` 審查/內容）| **RAG**：LlamaIndex + pgvector
- **Auth**：NextAuth.js (Google OAuth) + JWT | **編輯器**：CodeMirror 6
- **部署**：Zeabur（Tencent Tokyo VPS）

## 當前狀態
> 詳細 sub-task 進度見 `docs/roadmap.md`；已完成細節見 `docs/roadmap-archive.md` / `docs/changelog.md`。
> **每次 session 開頭先讀 `docs/dev-setup.md` §1**（Colima + docker-compose 啟動 SOP）。
> ⚠ **環境前置**：`web/.env.local` `AUTH_SECRET` 必須與 `backend/.env` `NEXTAUTH_SECRET` 同值。

**已完成（細節一律查 roadmap-archive / changelog，禁止回填此處）**
Phase 1-4 全數 ✅｜Phase 5 教師端 ✅（5-3/5-4 除外，等真實資料）｜Phase 6 教學內容建構 ✅｜
Phase 6-K K-Graph 自適應引擎 ✅｜Phase 6-U 學生端修正 ✅｜DEV 開發者模式 ✅｜
Phase 7-R 自建互動執行引擎 ✅（生產終端已上線）｜Phase 7-U 上線後體驗優化 ✅ 六項

**🎯 進行中 — 7-C Coddy 教學品質**（2026-08-06 使用者回報對話品質 → 全面審計 → 兩輪模擬驗收）
- 7-C1 ✅ 接通提示階梯（`hint_level` 原寫死 0，矩陣只用得到第 0 欄）+ Evidence 補 exit_code/status
- 7-C1' ✅ 七型學生模擬 harness（`backend/scripts/eval_coddy/`）+ 診斷輪修復 9 項；
  最重大＝**gpt-5.6 reasoning 預算間歇吃光輸出**（8-05「拒收 reasoning_effort」結論錯誤，值域改為 none/low/…），
  反思評分因此在生產一直靜默 fail-open；已全面改送 `reasoning_effort="none"`
- 7-C2a ✅ Decision 層重構（累積式揭露階梯 + 動態選層，方案 B）：36 格矩陣 → 6 級累積指令 + 6 Bloom 修飾；
  `reveal_level = min(5, base(error_type) + need)`；選層輸入搬後端（`services/chat_signals.py`）
  並刪掉前端／harness 兩個鏡像檔；RULE-1/2 定為階梯之上的不變量 + 新增 RULE-6
- 7-C2a' ✅ **選層輸入 persistence → need**（「堅持不等於值得」）：need 是需求量估計不是追問次數，
  理解 −1／沒理解 +1／失敗的實質嘗試 +1／顯式求助 +2／**追問與索答施壓 0**（單輪漲幅上限 2）；
  訊號由 Evidence 既有呼叫順帶輸出（零額外請求）
- 7-C2a'' ✅ 收尾：B8 消除（同證據沿用 error_type）＋「我卡住了」按鈕（`explicit_help` 欄位）＋
  Evidence 容錯解析（欄位越界退保守預設，不再整輪 502）＋ harness 可重跑；
  **七型全跑通過**（877 tests／前端 build 過／migration 可逆）
- 7-C2b ✅ 其餘 P1：NZEC 機械文案分三層（C++ 標準／OS 慣例／本平台判定，第一人稱）+ RULE-7/8
  （禁「通常」含糊帶過、認錯第一句就講）+ 逾時文案改互動終端 + 429 配額與故障分辨
- 7-C3 ✅ Comprehension 前端 UI（2-6 後端一直沒人用）：`components/comprehension/` 7 檔 +
  Quiz/Learn 兩處接入；變體挑戰以 AppShell 層 AI 鎖真的停用 Coddy；六端點端對端煙霧測試過
- **順序（roadmap 開頭有完整表）**：7-C4 再驗 →
  **7-D 技術債清償** → **7-E 使用者驗收** → Phase 8 / 7-2 監控 / 7-3 效能 / 5-3·5-4

**排在驗收之後**：Phase 8 專案健檢（8-0 討論已完成）／6-4b 教材局部重跑（依操作回饋）／K1d·K4d·K5d 使用者自測

**工具**：`python3 scripts/doc_selfcheck.py` — 文件自檢（超門檻檔案／失效路徑／測試數）；session 結束前跑一次
**驗收機制**：`backend/scripts/eval_coddy/` — 七型學生模擬（真實 LLM + debug_sink/DB 白盒探針），改完 Coddy 重跑對照

**部署與營運**：見 `docs/deployment.md`。要點＝**push 即自動部署**、migration 自動跑；
**唯獨改環境變數必須手動重啟 service**；OAuth 測試模式 100 人上限（Step 6 與已知限制節）。

## 文件索引
> 本文件目標 ≤ 60 行。新增內容先判斷歸屬，禁止回填 roadmap/日誌/UI 參數/Schema。

**`.claude/rules/`**（編輯對應檔案時自動注入，無需手動查閱）
- `frontend.md` — Design Tokens、元件規格、響應式斷點（glob: `web/**`）
- `backend.md` — 錯誤處理、安全規範、環境變數（glob: `backend/**`）
- `edf-pipeline.md` — EDF 三層管線、ConceptTag、出題流程（glob: `backend/services/edf/**`）

**`docs/`**（按需查閱，預設不主動讀）
- [dev-setup.md](docs/dev-setup.md) — **本機環境啟動 SOP（每次 session 必讀 §1）**
- [acceptance-checklist.md](docs/acceptance-checklist.md) — **真人驗收清單（依操作動線分 0~9 段；2026-08-06 全面重寫）**
- [roadmap.md](docs/roadmap.md) — 任務追蹤（精簡）/ [roadmap-archive.md](docs/roadmap-archive.md) — 完成細節（凍結）
- [changelog.md](docs/changelog.md) — 變更日誌（時間序）
- [architecture.md](docs/architecture.md) / [modules.md](docs/modules.md) / [db-schema.md](docs/db-schema.md)
- [ui-ux-spec.md](docs/ui-ux-spec.md) / [ui-wireframes.md](docs/ui-wireframes.md)（實作該頁時才讀）
- [api-spec.md](docs/api-spec.md) / [deployment.md](docs/deployment.md)（§E = Runner 部署 SOP）/ [server-plan.md](docs/server-plan.md) — A 機 + B 機 Runner 專用機（2026-08-05 改版）
- [design-plan.md](docs/design-plan.md) — 統一視覺協議（實作 UI 前才讀）
- [tech-debt.md](docs/tech-debt.md) / [references.md](docs/references.md)
