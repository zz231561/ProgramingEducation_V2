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
  - 6-2c ✅程式碼完成 + fallback 已驗（grounded markdown / citation seek 主路徑待 6-4a-deferred-ui 補驗）
  - 6-2d ✅程式碼完成 + fallback 已驗（grounded card + Workspace handoff 主路徑待 6-4a-deferred-ui 補驗）
  - 6-2e ✅程式碼完成 + fallback 已驗（grounded `summary.key_points` bullet + citation 標籤渲染主路徑待 6-4a-deferred-ui 補驗）
  - 6-3a-1 ✅`generate_question(video_order=...)` grounded mode（含 grounding prompt 規則 + 4 mock tests；學生現生題 backward compat 保留）
  - 6-3a-2 ✅批次 service `services/quiz/batch_generator.py` + CLI `scripts/generate_unit_questions.py`（per-concept N 題 × generate+validate + skip_existing；8 mock+DB tests）
  - 6-3b ✅ExercisesTab 題庫優先（GET /quiz/from-bank → 404 QUESTION_BANK_EMPTY fallback /quiz/generate；6 bank + 5 route tests；前端 Loading 文案分兩階段）
  - 6-R ✅健壯性強化（2026-07-04 架構審查）：500 traceback logging + token exp 驗證 + per-user rate limit（Redis fail-open）+ Judge0 網路例外 503 + LLM schema 驗證 502 + chat fail-safe 持久化 + user service 節流/race 防護 + 前端 401 重導/proxy timeout
  - **下一步**：**6-4a 自行品管抽查 + 6-3a-3 實機跑 + 6-4a-deferred-ui 必跑**（須備好 OpenAI API key + 預估 $5-15 USD；2026-07-04 已移除教授抽查）；或先平行 Phase 5 教師端
  - 後端 550 tests 全綠（2026-07-05 K3e +4）；實機 LLM 全跑延至 6-4 合併執行
- **🎯 Phase 6-K K-Graph 自適應學習引擎**（2026-07-04 功能規格書新增；原 6-5/6-6 整併入 K4 / K1+K5）
  - K1 ✅跨章多對多依賴 DAG（migration `i5d6e7f8a9b0` 90 條 curated 邊 + `get_prerequisite_closure` BFS 回溯 + 實機驗證；K1d UI 抽查待使用者）
  - K2 ✅動態知識狀態（`edf_parent_tag` mapping + 三層 fan-out 讓對話重新驅動 BKT；`/concepts/mastery` 加 last_practiced_at；K2c 決策：暫不引入真 AST）
  - K3 ✅全數完成（後端連續失敗觸發 + closure 回溯 + `GET /concepts/{tag}/diagnosis`；K3e 前端：答錯自動查診斷 → 嫌疑鏈 + 微測驗 `GET /quiz/questions/{id}` + 補救開放 + 圖譜跳轉）
  - K4a/b/c ✅（K-Graph 鷹架注入 prompt + Coddy persona 改寫 + RAG 相關性觸發 + 補救路徑 remediate API）；K4d 真人驗收待 API key 實測
  - K5a/b/c ✅（2026-07-05）：維持 Cytoscape.js 決策記錄（references.md §1）+ 節點填色改 mastery band + 路徑 ring（藍=目前/綠=已完成/紅=補救 `?remedial=`）；初驗回饋後改**確定性 preset 佈局**（S 曲線章節 + phyllotaxis）+ 章節低透明度星系 SVG 背景（parent 可拖）
  - **下一步（K 系列）**：**K5d 真人驗收**（學生能否從圖讀懂進度與弱項；含 K1d UI 抽查）→ K4d 真人驗收（可與 6-4a 實機批次合併）
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
