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

## 技術棧（已鎖定）
- **前端**：Next.js 15 + TypeScript + Tailwind CSS（`web/`）
- **後端**：FastAPI + Python 3.12 + SQLAlchemy 2.0 async（`backend/`）
- **資料庫**：PostgreSQL + pgvector | **快取**：Redis
- **程式碼執行**：Judge0 | **LLM**：OpenAI GPT-4o | **RAG**：LlamaIndex + pgvector
- **Auth**：NextAuth.js (Google OAuth) + JWT | **編輯器**：CodeMirror 6
- **部署**：Zeabur（Tencent Tokyo VPS）

## 當前狀態
**Phase 1-3：程式碼編輯與執行 🔧**
- ✅ 1-3a CodeMirror 6 整合（C++ 語法高亮 + One Dark 主題）
- ✅ 1-3b Workspace 頁面基礎佈局（Toolbar + Editor + Output Panel）
- ✅ 1-3c Judge0 API client（submit + polling 取結果）
- ✅ 1-3d 前端 Run 按鈕串接 + Output Panel 顯示結果
- ✅ 1-3f react-resizable-panels 拖曳調整

**Phase 1-4：EDF 教學管線 ✅**
- ✅ 1-4a Evidence 層：LLM 結構化輸出（錯誤分類 + ConceptTag + Bloom）
- ✅ 1-4b Decision 層：Bloom × Hint Ladder 策略矩陣
- ✅ 1-4c Feedback 層：分層 prompt 組裝 + 輸出驗證
- ✅ 1-4d Chat API 端點（interact + history）
- ✅ 1-4e 安全防護：輸入三層防護 + 輸出完整程式碼阻擋

**Phase 1-5：AI 對話介面 ✅**
- ✅ 1-5a Chat Panel 元件（訊息氣泡 + 輸入框 + Context 共享）
- ✅ 1-5b 對話歷史持久化（session 管理 + 歷史載入）
- ✅ 1-5c Run 結果自動注入 Chat context
- ✅ 1-5d Chat Panel 收合/展開 toggle

**Phase 1-6：介面精修 ✅**（統一視覺協議；6 份借鑑來源僅貢獻結構模式）
- ✅ 1-6a Surface / Shadow / Border / Radius token 增補
- ✅ 1-6b Inter OpenType `cv01, ss03` 全站套用
- ✅ 1-6c Output Panel Run Block 化（Warp 結構）
- ✅ 1-6d Chat 訊息氣泡 ring + Bloom badge（Claude 結構）
- ✅ 1-6e Toolbar Linear 風格化
- ✅ 1-6f EDF Pipeline mini timeline（Cursor 結構）

**Phase 1-7：部署 ⏸**（上次卡關於 API 串接）
- ⬜ 1-7a Dockerfile — 配置已存在，需重新驗證 build
- ⬜ 1-7b Zeabur 部署配置 — `zeabur.json` 已存在，需驗證 service 串接
- ⬜ 1-7c 首次上線驗證 — 上次卡在 API 串接，待逐項排查

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
