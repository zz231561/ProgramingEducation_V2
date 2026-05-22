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
7. **避免重複造輪子（OSS 優先）**：開發新功能前必先查 `docs/references.md` §1 決策矩陣。**禁止移植已有對應套件的演算法**（例：BKT 必用 pyBKT）。**禁止引入 AGPL/GPL 授權套件**（見 references.md §2 黑名單）。

## 技術棧（已鎖定）
- **前端**：Next.js 15 + TypeScript + Tailwind CSS（`web/`）
- **後端**：FastAPI + Python 3.12 + SQLAlchemy 2.0 async（`backend/`）
- **資料庫**：PostgreSQL + pgvector | **快取**：Redis
- **程式碼執行**：Judge0 | **LLM**：OpenAI GPT-4o | **RAG**：LlamaIndex + pgvector
- **Auth**：NextAuth.js (Google OAuth) + JWT | **編輯器**：CodeMirror 6
- **部署**：Zeabur（Tencent Tokyo VPS）

## 當前狀態
> 詳細 sub-task 進度見 `docs/roadmap.md`；已完成細節見 `docs/roadmap-archive.md` / `docs/changelog.md`。
> **每次 session 開頭先讀 `docs/dev-setup.md` §1**（Colima + docker-compose 啟動 SOP）。
> ⚠ **環境前置**：`web/.env.local` `AUTH_SECRET` 必須與 `backend/.env` `NEXTAUTH_SECRET` 同值。

- **Phase 1-4 ✅** 全數完成（學生端閉環 + 容器化 + Zeabur 配置）
- **🎯 Phase 6 進行中**（NotebookLM grounded 教學內容建構）
  - 6-1 影片資料整合 ✅（Whisper 62 部 transcript + 861 chunks 入 RAG；2026-05-22 1-3 加 PREREQUISITE 邊回主路徑）
  - 6-2a/b ✅（grounded prompt + Pydantic + 批次生成 infra + staging 表 + 18 mock+DB tests）
  - 6-2c ✅（YT IFrame player + grounded markdown + citation seek；2026-05-22 使用者 UI 驗證通過）
  - **下一步**：6-2d 範例 tab → 6-2e 摘要 tab → 6-3 練習題庫 → 6-4 抽查
  - 後端 476 tests 全綠；實機 LLM 全跑延至 6-4 合併執行
- **Phase 5 ⇄ Phase 6 平行**：教師端可隨時插入並行
- **Phase 7 上線實測**：須 Phase 6 至少 6-1 + 6-2 完成 + Zeabur + VPS 就緒

## 文件索引
> 本文件目標 ≤ 60 行。新增內容先判斷歸屬，禁止回填 roadmap/日誌/UI 參數/Schema。

**`.claude/rules/`**（編輯對應檔案時自動注入，無需手動查閱）
- `frontend.md` — Design Tokens、元件規格、響應式斷點（glob: `web/**`）
- `backend.md` — 錯誤處理、安全規範、環境變數（glob: `backend/**`）
- `edf-pipeline.md` — EDF 三層管線、ConceptTag、出題流程（glob: `backend/services/edf/**`）

**`docs/`**（按需查閱，預設不主動讀）
- [dev-setup.md](docs/dev-setup.md) — **本機環境啟動 SOP（每次 session 必讀 §1）**
- [roadmap.md](docs/roadmap.md) — 任務追蹤（精簡）/ [roadmap-archive.md](docs/roadmap-archive.md) — 完成細節（凍結）
- [changelog.md](docs/changelog.md) — 變更日誌（時間序）
- [architecture.md](docs/architecture.md) / [modules.md](docs/modules.md) / [db-schema.md](docs/db-schema.md)
- [ui-ux-spec.md](docs/ui-ux-spec.md) / [ui-wireframes.md](docs/ui-wireframes.md)（實作該頁時才讀）
- [api-spec.md](docs/api-spec.md) / [deployment.md](docs/deployment.md)
- [tech-debt.md](docs/tech-debt.md) / [references.md](docs/references.md)
