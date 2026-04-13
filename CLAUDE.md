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
- **資料庫**：PostgreSQL + pgvector（RAG 向量搜尋）
- **快取**：Redis（session cache、rate limiting）
- **程式碼執行**：Judge0（開發期 RapidAPI hosted → 上線後自架）
- **LLM**：OpenAI GPT-4o（Socratic 教學 + 智慧出題）
- **RAG**：LlamaIndex + pgvector
- **Auth**：NextAuth.js（Google OAuth）+ JWT
- **編輯器**：CodeMirror 6
- **部署**：Zeabur（Tencent Tokyo VPS 節點）

## 當前狀態
**Phase 0：規劃完成 ✅** — 尚未開始實作
- 完整規劃文件已就緒（技術棧、模組設計、UI 設計、API 規格、工程規範、開發階段）
- 下一步：Phase 1-1 專案初始化（Next.js + FastAPI + PostgreSQL + Redis）
→ 詳見 `docs/06-phases.md`

## 文件索引
> **維護規範**：本文件目標 ≤ 60 行。新增內容先判斷歸屬哪個文件，
> 禁止將 roadmap、測試流程、日誌、UI 參數、Schema 等回填至此。

**`docs/`**（按需查閱）
- [00-overview.md](docs/00-overview.md) — 專案總覽 + 已確認決策摘要
- [01-tech-stack.md](docs/01-tech-stack.md) — 技術棧、系統架構圖、目錄結構
- [02-modules.md](docs/02-modules.md) — 8 個模組規劃 + DB Schema
- [03-ui-design.md](docs/03-ui-design.md) — UI/UX 設計、Design Tokens、Wireframe、元件規格
- [04-api-spec.md](docs/04-api-spec.md) — 完整 API 端點規格
- [05-engineering.md](docs/05-engineering.md) — 環境變數、錯誤處理、安全規範、測試策略
- [06-phases.md](docs/06-phases.md) — 4 個實作階段 + 已確認決策
- [changelog.md](docs/changelog.md) — 變更日誌
