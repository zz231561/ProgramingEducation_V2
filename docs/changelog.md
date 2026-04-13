# 變更日誌

## [2026-04-13] — Phase 1-1c PostgreSQL + Redis 連線
### Added
- `core/database.py` — SQLAlchemy async engine + sessionmaker + `Base` 宣告式基底 + `get_db` 依賴注入
- `core/redis.py` — Redis async client 初始化/關閉 + `get_redis` 依賴注入
- `main.py` 新增 `lifespan` context manager 管理 DB engine dispose + Redis 連線生命週期
- `api/routes/health.py` 升級為完整健康檢查：回傳 DB + Redis 連線狀態（`connected` / `disconnected`）
- `api/deps.py` 匯出 `get_db`、`get_redis` 供路由依賴注入使用

## [2026-04-13] — Phase 1-1b FastAPI 專案建立
### Added
- `backend/` 目錄結構：`api/routes/`、`api/middleware/`、`models/`、`services/`、`core/`
- `pyproject.toml` + `requirements.lock` 依賴管理（FastAPI 0.135 + Pydantic 2.13 + SQLAlchemy 2.0 + asyncpg）
- `core/config.py` — Pydantic Settings 管理環境變數（DB、Redis、Auth、OpenAI、Judge0）
- `core/errors.py` — 標準錯誤回應模型 `ErrorResponse` + 全域例外處理（`AppError` → JSON）
- `main.py` — FastAPI 進入點 + CORS middleware（僅允許 NEXTAUTH_URL）+ health route
- `api/routes/health.py` — `GET /health` 端點
- `.env.example` — 環境變數範本

## [2026-04-13] — Activity Bar 放大並加入文字標籤
### Changed
- Activity Bar 從 48px icon-only 改為 180px icon + 文字標籤（英文名稱 + 中文說明）
- Chat Panel 預設寬度改為 350px（pixel-based），修正原本過窄的問題

## [2026-04-13] — Phase 1-1g 前端 UI 基礎建設
### Added
- 安裝 shadcn/ui（base-nova style, dark preset）+ lucide-react + react-resizable-panels v4
- Activity Bar 元件（48px 左側導覽，9 項 icon 導覽 + Avatar + Tooltip）
- AI Chat Panel 空殼（Header + 訊息佔位 + 輸入區，支援收合/展開）
- Status Bar 元件（24px 底部，連線狀態 + 語言 + 編碼 + 游標位置 + 精熟度）
- AppShell 全域骨架整合 react-resizable-panels 拖曳調整 Content / Chat 寬度
- 響應式佈局：Desktop 三欄 / Laptop Chat overlay / Tablet 漢堡選單頂部 bar / Mobile 底部 tab bar
- 8 個路由佔位頁面（workspace / learn / quiz / knowledge / overview / notifications / dashboard / settings）
- `useBreakpoint` hook（4 斷點偵測）
- Ctrl+B 快捷鍵收合/展開 Chat Panel

## [2026-04-13] — 新增 UI/UX 介面規格書
### Added
- `docs/ui-ux-spec.md` — 完整 UI/UX 介面規格書（13 章節）
- VSCode 風格 IDE 佈局：Activity Bar + Content Area + AI Chat Panel
- 7 個頁面規格：Workspace、Learn、Quiz、Knowledge、Overview、Dashboard、Settings
- Workspace 檔案樹（多檔案管理）、學生 Overview 獨立頁面、通知系統鈴鐺
- 響應式設計（Desktop / Laptop / Tablet / Mobile 四斷點）
- 動效、快捷鍵、狀態列、Pre-Coding Reflection / Post-Solution 互動流程

## [2026-04-13] — Phase 1-1a Next.js 專案初始化
### Added
- `web/` 目錄：Next.js 16 + App Router + TypeScript + Tailwind CSS v4
- Design Tokens（GitHub Dark）套用為 CSS 變數，Tailwind `@theme` 映射為 utility class
- 字型載入：Inter（UI）+ Noto Sans TC（中文）+ JetBrains Mono（程式碼）
- Dark mode 預設啟用（`<html class="dark">`）
- `lang="zh-TW"` 設定

## [2026-04-13] — Roadmap 新增前端 UI 基礎建設任務
### Changed
- `roadmap.md` Phase 1-1 新增 1-1g：shadcn/ui 安裝 + 全域 Layout + Header Navigation + 響應式骨架，確保後續功能開發時已有成熟 UI 框架

## [2026-04-13] — 文檔交叉引用修正
### Fixed
- `architecture.md` routes 註解補齊 `dashboard, analytics, reflection` 端點
- `changelog.md` Module 9 參考專案計數修正（7→6）
- `db-schema.md` Module 6 `student_answers` 加入 comprehension 擴充欄位交叉引用
- `roadmap.md` Phase 2 header 補齊影響頁面（Workspace Pre-Coding Reflection 側邊欄）
- `roadmap.md` Phase 4-2c `dialogue_act` enum 補漏 `acknowledgment`

## [2026-04-13] — 新增 Pre-Coding Reflection 反認知外包機制
### Added
- 跨模組機制：Pre-Coding Reflection（解題前反思閘門，方案 B 一次追問機會）
- 跨模組機制：Post-Solution Comprehension Check（EPL / 預測輸出 / 變體挑戰）
- DB Schema：`reflections` 表 + `student_answers` 擴充 comprehension 欄位
- API：Reflection 端點（create + update + get）+ Quiz comprehension 端點
- Roadmap：Phase 2 新增 2-5（反思閘門）+ 2-6（理解驗證）、Phase 3-1 新增 3-1e
- 學術參考：7 篇新增至 references.md（CodeAid、PRIMM、EPL、Self-explanation 等）

### Changed
- modules.md Module 6/7 加入反思觸發點、Module 9 加入反認知外包指標
- edf-pipeline.md Evidence 層加入反思內容注入、Feedback 層加入反思引用
- references.md 新增 Pre-Coding Reflection 參考區塊

## [2026-04-13] — 新增 Module 9 學習行為分析模組
### Added
- Module 9：學習行為分析（教師專屬，Phase 4）— 中粒度追蹤 coding 行為與 AI 互動
- DB Schema：`coding_events` 事件紀錄表 + `behavior_aggregates` 預聚合表
- `chat_messages` 擴充 `dialogue_act` 欄位（Phase 4-2c）
- API：Behavior Analytics 端點（班級總覽/散佈圖/熱力圖/個人時序/摘要）
- Roadmap Phase 4 拆分為 5 子階段（4-1 班級管理 → 4-2 資料收集 → 4-3 分析演算法 → 4-4 視覺化 → 4-5 作業指派）
- 參考專案：ProgSnap2、KOALA、StudyChat、pyBKT、PM4Py、OpenLAP 等 6 個新增至 references.md
- 目錄結構新增 `backend/services/analytics/`

### Changed
- modules.md 擴充為 9 模組
- CLAUDE.md 更新模組數量

## [2026-04-13] — 新增開源參考專案文檔
### Added
- `docs/references.md` — 8 個開源參考專案對照表（DeepTutor、OATutor、Mr. Ranedeer、EduAdapt-AI 等）
- 各功能最佳參考來源對照（EDF、RAG、Knowledge Tracing、智慧出題、學習路徑）
- 學術資源連結（論文、awesome list）

### Changed
- `docs/modules.md` — Module 3/4/6/7 加入對應開源參考來源
- `docs/roadmap.md` — Phase 1-4、2-1、2-3、2-4、3-1 加入參考專案指引
- `.claude/rules/edf-pipeline.md` — 加入開源參考區塊
- `CLAUDE.md` — 文件索引新增 references.md

## [2026-04-13] — 文檔一致性修正
### Fixed
- 將 `CHANGELOG.md` 搬移至 `docs/changelog.md`，與 CLAUDE.md 文件索引一致
- 修正 changelog 格式：每次變更使用獨立日期標頭，移除非標準的 `Previous` 區塊
- 統一導覽 Tab 命名：wireframe Header 的 `Graph` → `Knowledge`，並補上 `Dashboard` tab
- api-spec.md 新增 Dashboard API 端點（`/api/dashboard/summary` + `/api/dashboard/activity`）

## [2026-04-13] — Phase 0 規劃文檔完善
### Changed
- Roadmap 拆分為原子級子任務（每個 checkbox = 一次對話可完成）
- DB Schema 補齊 index/constraint 標記（unique、GIN、HNSW、複合索引）
- EDF pipeline 補完 Bloom 6 級定義 + Hint Ladder 6 級策略表
- architecture.md 新增前後端通訊模式（Next.js API proxy）+ 標準錯誤 JSON 格式
- API spec 更新 Chat 端點（SSE streaming + session CRUD）
- rules/frontend.md 補入測試策略 + API 呼叫規範

### Added
- `.env.example` — 環境變數範本
- `db-schema.md` Module 3 Chat Session 表（chat_sessions + chat_messages）

## [2026-04-12] — 文檔架構重構
### Changed
- 重構全部文檔架構，最佳化 Claude Code 上下文效率
- 新增 `.claude/rules/` 自動注入規則（frontend、backend、edf-pipeline）
- 拆分大檔案：modules + db-schema、ui-wireframes + rules/frontend
- 合併冗餘文件：06-phases → roadmap、00-overview → CLAUDE.md
- 刪除 7 個舊文件，重組為 8 個 docs + 3 個 rules

### Added
- `.claude/rules/frontend.md` — 前端 Design Tokens、元件規格、響應式（自動注入 web/**）
- `.claude/rules/backend.md` — 錯誤處理、安全規範、環境變數（自動注入 backend/**）
- `.claude/rules/edf-pipeline.md` — EDF 管線規範（自動注入 backend/services/edf/**）
- `docs/architecture.md` — 系統架構圖 + 目錄結構
- `docs/modules.md` — 8 模組功能摘要
- `docs/db-schema.md` — 全部 DB Schema
- `docs/ui-wireframes.md` — 5 頁 wireframe

### Removed
- `docs/00-overview.md` — 內容已涵蓋在 CLAUDE.md
- `docs/01-tech-stack.md` — 拆分至 architecture.md + CLAUDE.md
- `docs/02-modules.md` — 拆分至 modules.md + db-schema.md + edf-pipeline.md
- `docs/03-ui-design.md` — 拆分至 ui-wireframes.md + rules/frontend.md
- `docs/04-api-spec.md` — 重命名為 api-spec.md
- `docs/05-engineering.md` — 拆分至 rules/backend.md
- `docs/06-phases.md` — 合併至 roadmap.md

## [2026-04-11] — 專案初始化
### Added
- 新增 `CLAUDE.md` 專案級開發指揮中心
- 專案初始化，建立 Git repository
- 新增 .gitignore
