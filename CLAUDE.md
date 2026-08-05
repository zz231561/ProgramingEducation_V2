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

**🎯 進行中**
- **7-C Coddy 教學品質修復**（2026-08-06 使用者對話回報 → 審計出四個「機制寫好但環節斷線」缺陷）：
  7-C1 ✅ P0（Hint Ladder 接通 + Evidence 補 exit_code/status；827 tests）→ 7-C2 P1（NZEC 文案・429 顯示・prompt 規則）→ 7-C3 **2-6 Comprehension 前端**（後端完整但 UI 從未存在，裁決＝建 UI）
- **使用者驗收**：裁決改為**功能全部完善後一律驗收**（7-C 完成後）；驗收清單 0~9 段，目前僅 1-1 通過
- **Phase 8 專案健檢**：8-0 討論完成（體積已釐清、自檢 script 已定案）；動手清理排在驗收後

**待辦（未排期）**
7-R R6 收尾（使用者要求暫緩）／7-2 監控程式碼／7-3 效能 baseline／
5-3·5-4 行為分析（等真實資料）／6-4b 教材局部重跑（依實際操作回饋）／K1d·K4d·K5d 使用者自測

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
