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

**🎯 進行中：Phase 2 智慧功能（功能優先策略）**
> 部署已從 Phase 1-7 移至 **Phase 4**（見 roadmap）。先把學生端體驗做完，再一次性處理部署 + 教師端，避免反覆卡關於 API 串接。
> **本機 dev**：Colima + `docker compose -f docker-compose.dev.yml up -d`（啟 pgvector + redis）；後端用 `uv` + `backend/.venv`。
- 🟡 2-1 RAG 知識檢索（**用 LlamaIndex `PGVectorStore`**）— 2-1a ✅ pgvector + documents 表
- ⬜ 2-2 知識圖譜（**用 Cytoscape.js + fcose**）
- ⬜ 2-3 精熟度追蹤（**用 pyBKT，禁止 port OATutor JS 版**）
- ⬜ 2-4 智慧出題
- ⬜ 2-5 Pre-Coding Reflection（解題前反思）
- ⬜ 2-6 Post-Solution Comprehension Check（解題後驗證）

**Phase 3 學習體驗 → Phase 4 部署 → Phase 5 教師端**（詳見 roadmap）

**📦 OSS 重用策略**：開發前必查 `docs/references.md` §1 決策矩陣（CLAUDE.md 守則 #7）

## 文件索引
> 本文件目標 ≤ 60 行。新增內容先判斷歸屬，禁止回填 roadmap/日誌/UI 參數/Schema。

**`.claude/rules/`**（編輯對應檔案時自動注入，無需手動查閱）
- `frontend.md` — Design Tokens、元件規格、響應式斷點（glob: `web/**`）
- `backend.md` — 錯誤處理、安全規範、環境變數（glob: `backend/**`）
- `edf-pipeline.md` — EDF 三層管線、ConceptTag、出題流程（glob: `backend/services/edf/**`）

**`docs/`**（按需查閱）
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
