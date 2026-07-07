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
  - 6-2e ✅程式碼完成（2026-07-06 決策：摘要 tab 將移除 U2b，deferred 驗收作廢）
  - 6-3a-1 ✅`generate_question(video_order=...)` grounded mode（含 grounding prompt 規則 + 4 mock tests；學生現生題 backward compat 保留）
  - 6-3a-2 ✅批次 service `services/quiz/batch_generator.py` + CLI `scripts/generate_unit_questions.py`（per-concept N 題 × generate+validate + skip_existing；8 mock+DB tests）
  - 6-3b ✅ExercisesTab 題庫優先（GET /quiz/from-bank → 404 QUESTION_BANK_EMPTY fallback /quiz/generate；6 bank + 5 route tests；前端 Loading 文案分兩階段）
  - 6-R ✅健壯性強化（2026-07-04 架構審查）：500 traceback logging + token exp 驗證 + per-user rate limit（Redis fail-open）+ Judge0 網路例外 503 + LLM schema 驗證 502 + chat fail-safe 持久化 + user service 節流/race 防護 + 前端 401 重導/proxy timeout
  - 6-M ✅ LLM 模型選型 v2（2026-07-06 定案 + 6-M1 落地）：任務導向路由——生成 `gpt-5-mini` / 審查 `gpt-5.4` / content `gpt-5.4` / 對話與分析 `gpt-5.4-mini`；6-M1 分組環境變數（GENERATE/VALIDATE/CONTENT fallback LLM_MODEL）+ 11 呼叫點切換 + .env 套用完成；批次費用 ≈ $6.6、儲值 $10（key 已在 .env）
  - 6-2b/6-3a-3 實機批次 ✅（2026-07-06）：content 62/62 生成 + **全量 promote 上線**（v05/v62 needs_more_source）+ 題庫 138 題 validated（57/62 concept 滿額；v17/v41 掛零記 tech-debt）；途中修 gpt-5 參數相容層 `core/llm_params.py` + quiz batch MissingGreenlet
  - 6-4a 正式抽查已移除（使用者決策）：品質問題改由實際操作回饋 → 6-4b 局部重跑；6-2c citation 跳轉併入實際操作驗證
  - 後端 611 tests 全綠；剩 K4d 調參（使用者實測回饋）
- **🎯 Phase 6-K K-Graph 自適應學習引擎**（2026-07-04 功能規格書新增；原 6-5/6-6 整併入 K4 / K1+K5）
  - K1 ✅跨章多對多依賴 DAG（migration `i5d6e7f8a9b0` 90 條 curated 邊 + `get_prerequisite_closure` BFS 回溯 + 實機驗證；K1d UI 抽查待使用者）
  - K2 ✅動態知識狀態（`edf_parent_tag` mapping + 三層 fan-out 讓對話重新驅動 BKT；`/concepts/mastery` 加 last_practiced_at；K2c 決策：暫不引入真 AST）
  - K3 ✅全數完成（後端連續失敗觸發 + closure 回溯 + `GET /concepts/{tag}/diagnosis`；K3e 前端：答錯自動查診斷 → 嫌疑鏈 + 微測驗 `GET /quiz/questions/{id}` + 補救開放 + 圖譜跳轉）
  - K4a/b/c ✅（K-Graph 鷹架注入 prompt + Coddy persona 改寫 + RAG 相關性觸發 + 補救路徑 remediate API）；K4d 真人驗收待 API key 實測
  - K5a/b/c ✅（2026-07-05，六輪迭代）：Cytoscape.js + mastery band 填色 + 路徑 ring（藍=目前/綠=已完成/紅=補救 `?remedial=`）+ **語意縮放全覽**（overview=同批概念節點放大字體/尺寸並重排每章緊湊網格 `overview-layout.ts`；detail=蛇形星系佈局；zoom 門檻 0.45 動畫切換 `graph-mode.ts`）+ 點擊容器/節點皆 zoom in 該章 + GalaxyNav 含全覽鈕 + zoom cap 1.0 + 跨章邊淡出；`knowledge-graph.tsx` 已拆分（212 行 + `use-graph-nav.ts`，第 3 批）
  - K6 ✅熟練度演算法 v2（2026-07-06 第 3 批）：K6a 訊號分級 BKT 參數（quiz 強/chat 弱證據）+ K6b 遺忘曲線惰性衰減（`services/mastery/decay.py`，floor 0.25 + 半衰期隨練習成長）+ K6c 事件級透明化（effective/raw confidence + due_for_review 提示）；**論文關鍵文獻標注 references.md §5.1**
  - **下一步（K 系列）**：**K5d 真人驗收**（學生能否從圖讀懂進度與弱項；含 K1d UI 抽查）→ K4d 真人驗收（可與 6-4a 實機批次合併）
- **🎯 Phase 6-U 學生端修正**（2026-07-06 session 定案）：U1a/b/c ✅（第 1 批）/ U2b/c ✅（第 2 批）/ U2a/d ✅（第 4 批，含重複曝光消除）/ U2e Workspace 程式碼存檔（第 8 批）/ U2f 範例程式（第 6 批）
- **執行順序 10 批已定案**（2026-07-06；晚間修訂 U2f→U2g）：①~⑥ ✅（U2g 含全量 promote 完成）→ ⑥' 6-3c 知識點驅動題庫（觀念題=選擇題，不做簡答；程式題固定 1 題、intro 0 題；138 題保留補缺）→ ⑦ 教師端 → ⑧ U2e+監控 → ⑨ Phase 7 → ⑩ 5-3/5-4；**下一步：6-3c**（LEARN/citation 品質問題由使用者操作回饋 → 6-4b）
- **DEV 開發者模式 ✅ 全數完成**（2026-07-05；拆解見 roadmap DEV 節）：後端 gating（`DEV_MODE_ENABLED`+`DEV_MODE_EMAILS`、`require_dev_user`）+ rate limit 豁免 + Settings 六卡（身分切換 / 幽靈解鎖 / 熟練度編輯 / K3 診斷模擬 / 題庫檢視 `/quiz?question=` 深連結 / 分類重置）+ EDF Debug 面板（chat `debug_sink`，dev 才附）；+33 tests；**UI 驗收待使用者**；DEV-E 假學生 seeder 留 Phase 5
- **🎯 Phase 5 教師端 進行中**（批次 ⑦）：5-1b 全後端完成 ✅（班級 CRUD + profile + 加入班級 + 名冊）；5-1c-1 教師班級管理頁 `/teacher` ✅ **UI 驗收通過**（建班/邀請碼/名冊/停用 + avatar 教師入口；含修 `/users/me` 路由碰撞 + 身分切換即時更新選單 + 精簡選單）；5-1c ✅ 全數 UI 驗收通過；5-1d 身分自選 onboarding（決策：自選師生 + 單一身分 + 設定頁切換＝全清）：5-1d ✅ 全數驗收通過（身分自選 onboarding + 設定切換＝全清）→ **5-1 班級管理全部完成**；🎯 **5-2 行為資料收集進行中**：5-2a ✅ coding_events 表 + 5-2b ✅ event logging service（掛 /code/execute + chat hint）+ 5-2c ✅ chat_messages 加 dialogue_act（StudyChat 6 值；11 tests）+ 5-2d ✅ 行為指標聚合 service（`aggregate_user_behavior`：執行次數/成功率/修復時間/hint+dialogue_act 分布；compute-on-read 不建預聚合表；7 tests）→ **5-2 行為資料收集 5-2a~d 全數完成**；**下一步**（批次 ⑦）：DEV-E 假學生 seeder → 5-5 作業指派
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
