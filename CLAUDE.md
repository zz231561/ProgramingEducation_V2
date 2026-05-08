# ProgramingEducation V2 — 開發指揮中心

## 執行守則 (STRICT RULES)
1. **小步快跑**：每次對話僅限執行 Roadmap 中的「單一最小 Checkbox 任務」。
2. **強制中斷**：完成代碼修改後立即停止，提示使用者手動測試。
3. **禁止擅自推進**：等待使用者回覆「測試通過」才可勾選 Checkbox 並開始下一任務。
4. **狀態同步**：任務確認後優先更新對應文件的 Checkbox `[x]`。
5. **專業匯報**：簡述修改對架構的影響，確認是否符合工程規範。
6. **強制文檔同步**：每次指令完成後，**必須**更新所有相關記錄文檔：
   - `docs/changelog.md` — 新增本次變更記錄行
   - `docs/roadmap.md` — 勾選已完成的 Checkbox / 新增任務項
   - `CLAUDE.md` 當前狀態區塊 — 反映最新進度
   - `docs/tech-debt.md` — 若產生或消除技術債
7. **避免重複造輪子（OSS 優先）**：開發新功能前**必先查閱 `docs/references.md` §1 決策矩陣**，確認是否有 Tier 1 可直接 `pip/npm install` 的成熟套件、或 Tier 2 可採用的 schema。**禁止移植已有對應套件的演算法**（例：BKT 必用 pyBKT，禁止 port OATutor JS 版）。**禁止引入 AGPL/GPL 授權套件**（見 references.md §2 黑名單）。新增 dependency 前必須在 PR 描述列出 license 並確認屬於白名單。

## 技術棧（已鎖定）
- **前端**：Next.js 15 + TypeScript + Tailwind CSS（`web/`）
- **後端**：FastAPI + Python 3.12 + SQLAlchemy 2.0 async（`backend/`）
- **資料庫**：PostgreSQL + pgvector | **快取**：Redis
- **程式碼執行**：Judge0 | **LLM**：OpenAI GPT-4o | **RAG**：LlamaIndex + pgvector
- **Auth**：NextAuth.js (Google OAuth) + JWT | **編輯器**：CodeMirror 6
- **部署**：Zeabur（Tencent Tokyo VPS）

## 當前狀態

**Phase 1：基礎建設（MVP）✅**（1-1 ~ 1-6 全數完成；明細見 `docs/roadmap.md`）
- 骨架 / Auth / 編輯與執行 / EDF 教學管線 / AI 對話介面 / 介面精修

**Phase 2 完成 ✅**（2-1 ~ 2-6 全數完成；明細見 `docs/roadmap.md`）
- RAG / 知識圖譜 / BKT 精熟度 / 智慧出題 / Pre-Coding Reflection / Post-Solution Comprehension（EPL+Predict+Variation+動態觸發+BKT 串接）

**Phase 3 完成 ✅**（學習體驗，3-1 / 3-2 / 3-3 全數完成）
> **每次 session 開頭先讀 `docs/dev-setup.md` §1**（Colima + docker-compose 啟動 SOP）；首次接手讀 §2~6。
> ⚠ **環境前置**：`web/.env.local` `AUTH_SECRET` 必須與 `backend/.env` `NEXTAUTH_SECRET` 同值
- 3-1 結構化學習路徑（7 sub-tasks）/ 3-2 Quiz 完整版（3 sub-tasks）/ 3-3 Dashboard（3 sub-tasks）
- 學生端完整閉環：登入 → Learn → Quiz → Dashboard；後端 439 tests 全綠

**Phase 4 完成 ✅**（容器化 + 配置層，本機可完成範圍）
- ✅ 4-1 容器化（Dockerfile build / pgvector / Judge0 自架）
- ✅ 4-2 配置層（環境變數分層 / Zeabur 串接 / NextAuth + CORS）
- ⚠ 原 4-3 上線驗證已重整至 **Phase 7 上線實測**（需實際部署才能驗證）

**🎯 進行中：Phase 6 教學內容建構（NotebookLM grounded 模式）**
- ✅ 6-1a 教授交付 playlist URL（2026-05-07：62 部影片完整對齊 video_order 1-62）
- ✅ 6-1b 開發 fetcher script + 產出 59 列 CSV（2026-05-07）
- ✅ 6-1b+ fetcher 擴充為 EXPECTED 1-62 + 重產 62 列 CSV（2026-05-07）
- ✅ 6-1c 加 video 1-3 concept seed migration（2026-05-07，DB 59→62，filter 在 generator.py，445 tests 全綠）
- ✅ 6-1d PATCH script + 執行寫入 DB（2026-05-07：62/62 metadata 寫入，dev DB 已就緒）
- ✅ 6-1e（NotebookLM 核心）改 B1 Whisper API（A 方案 YT 字幕失敗）→ 62 transcripts → 12 global corrections → 861 chunks 入 RAG（2026-05-08，spot retrieve 4/4 命中）
- ✅ 6-1f tech-debt 同步
- ✅ 6-2a Grounded prompt template + Pydantic 模型 + 13 mock-LLM 測試（2026-05-08：458 tests 全綠）
- ✅ 6-2b 批次生成 infra：retrieve metadata filter + staging 表 + retry + promote helper + 18 個 mock+DB 測試（2026-05-08：476 tests 全綠；實機 LLM 全跑延至 6-4 抽查時合併執行）
- ⬜ 6-2c ~ 6-4：YT player 嵌入 / 範例 tab / 摘要 tab / 練習題庫 / 教授抽查

**Phase 5 ⇄ Phase 6 平行**：Phase 5 教師端可隨時插入並行（5-1 班級管理 / 5-2 行為資料 / 5-3 分析演算法 / 5-4 視覺化 / 5-5 作業指派）

**Phase 7 上線實測**：須 Phase 6 至少 6-1 + 6-2b 完成（避免部署後 Learn 頁仍空殼）+ Zeabur + VPS 就緒

**OSS 守則**：見守則 #7 + `references.md` §1。

## 文件索引
> 本文件目標 ≤ 60 行。新增內容先判斷歸屬，禁止回填 roadmap/日誌/UI 參數/Schema。

**`.claude/rules/`**（編輯對應檔案時自動注入，無需手動查閱）
- `frontend.md` — Design Tokens、元件規格、響應式斷點（glob: `web/**`）
- `backend.md` — 錯誤處理、安全規範、環境變數（glob: `backend/**`）
- `edf-pipeline.md` — EDF 三層管線、ConceptTag、出題流程（glob: `backend/services/edf/**`）

**`docs/`**（按需查閱）
- [dev-setup.md](docs/dev-setup.md) — **本機環境啟動 SOP（每次 session 必讀 §1）**
- [architecture.md](docs/architecture.md) — 系統架構圖 + 目錄結構
- [modules.md](docs/modules.md) — 9 模組功能摘要 + 設計決策
- [db-schema.md](docs/db-schema.md) — 全部 DB Schema（按模組分區）
- [ui-ux-spec.md](docs/ui-ux-spec.md) — 完整 UI/UX 介面規格書（VSCode 風格 IDE 佈局）
- [ui-wireframes.md](docs/ui-wireframes.md) — 5 頁 ASCII wireframe（實作該頁時才讀）
- [api-spec.md](docs/api-spec.md) — API 端點規格
- [deployment.md](docs/deployment.md) — Zeabur 部署指南
- [roadmap.md](docs/roadmap.md) — Phase 1~4 任務追蹤 + 已確認決策
- [changelog.md](docs/changelog.md) — 變更日誌
- [tech-debt.md](docs/tech-debt.md) — 技術債追蹤
- [references.md](docs/references.md) — 開源參考專案（實作各 Phase 時 clone 研究）
