# 變更日誌

## [2026-04-13] — 新增 Module 9 學習行為分析模組
### Added
- Module 9：學習行為分析（教師專屬，Phase 4）— 中粒度追蹤 coding 行為與 AI 互動
- DB Schema：`coding_events` 事件紀錄表 + `behavior_aggregates` 預聚合表
- `chat_messages` 擴充 `dialogue_act` 欄位（Phase 4-2c）
- API：Behavior Analytics 端點（班級總覽/散佈圖/熱力圖/個人時序/摘要）
- Roadmap Phase 4 拆分為 5 子階段（4-1 班級管理 → 4-2 資料收集 → 4-3 分析演算法 → 4-4 視覺化 → 4-5 作業指派）
- 參考專案：ProgSnap2、KOALA、StudyChat、pyBKT、PM4Py、OpenLAP 等 7 個新增至 references.md
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
