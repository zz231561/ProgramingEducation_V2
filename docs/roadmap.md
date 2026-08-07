# Roadmap

> **狀態：活躍** — 這裡是「現在要做什麼」的**唯一真相來源**（CLAUDE.md 不再重複進度）。
>
> **寫法**：每個 sub-task **只寫一行摘要** + 完成日期，理由與數據寫 `decisions.md`、
> 變更明細查 `git log`。完成就地打勾 `[x]`，不搬走（phase 結構本身就是索引）。
> **禁止手抄機械事實**（行數／測試數）——以 `doc_selfcheck.py` 產出為準。

## 🎯 現在的執行順序（2026-08-07 更新）

> Phase 1–6 全數完成、Phase 7 已上線、**7-C Coddy 教學品質已全數完成**。
> 現在的主線是 **7-D 技術債清償**；其餘（Phase 8 健檢、7-2 監控、7-3 效能、
> 5-3/5-4 行為分析）都排在使用者驗收之後。

| 順序 | 項目 | 性質 | 狀態 |
|------|------|------|------|
| ① | ~~**7-C2a** Decision 層重構（累積式揭露階梯 + 動態選層，方案 B）~~ | 架構優化 | ✅ 2026-08-06 |
| ①' | ~~**7-C2b** 其餘 P1（NZEC 教學語意 / 逾時文案 / 分層說明+認錯規則 / 429 配額顯示）~~ | 功能優化 | ✅ 2026-08-06 |
| ② | ~~**7-C3** 2-6 Comprehension 前端 UI（後端完整但學生碰不到）~~ | 新建功能 | ✅ 2026-08-06 |
| ③ | ~~**7-C4** Coddy 品質再驗（`eval_coddy` 七型重跑前後對照）~~ | 驗證 | ✅ 2026-08-06 |
| ④ | **7-D** 技術債清償（前端測試 → code health → lint → **文檔工作流** → R6 收尾 → toast） | 技術債 | 🎯 **進行中** |
| ⑤ | **7-E** 使用者驗收（acceptance-checklist 0~9 段） | 驗收 | 待辦 |
| ⑥ | Phase 8 專案健檢整理 → 7-2 監控 → 7-3 效能 baseline → 5-3/5-4 行為分析 | 後續 | 待辦 |

> **定序原則（使用者定案）**：新功能／功能優化 → **技術債清償** → 驗收。
> 驗收放最後是因為使用者裁決「功能全部完善後一律驗收」，避免同一動線反覆驗。

---

> **原始執行策略（歷史脈絡）**：功能優先（Phase 2 → 3）→ 部署準備程式碼（Phase 4）→ **Phase 5 教師端 / Phase 6 教學內容建構（兩者可平行或先後，依教授資料準備進度而定）** → 上線實測（Phase 7）。
> **核心原則**：需要實際 Zeabur / VPS 部署才能驗證的工作（Golden path / 監控 / 效能 baseline）集中在 Phase 7。本機可完成的程式碼準備全部排在 Phase 7 之前。
> **OSS 重用**：開發前必查 `docs/references.md` §1 決策矩陣（CLAUDE.md 守則 #7）。
> **完成細節**：變更明細查 `git log`；決策理由與實測數據查 `docs/decisions.md`；
> 按 phase 結構的完成快照查 `docs/roadmap-archive.md`（⚫ 凍結）。

## Phase 1：基礎建設（MVP）✅
> 學生可登入、寫 C++、執行、與 AI 對話學習｜對應 Workspace (Page 1)
- [x] 1-1 專案骨架（Next.js 15 / FastAPI / PG / Redis / Alembic / Health check）
- [x] 1-2 Auth 模組（NextAuth + Google OAuth + JWT + RBAC middleware）
- [x] 1-3 程式碼編輯與執行（CodeMirror 6 + Judge0 + Output Panel + 拖曳）
- [x] 1-4 EDF 教學管線（Evidence + Decision + Feedback + Chat API + 三層安全防護）
- [x] 1-5 AI 對話介面（Chat Panel + 持久化 + Run 注入 + 收合）
- [x] 1-6 介面精修（Surface/Shadow token / Inter cv01 / Run Block / 訊息 ring / Toolbar / EDF timeline）

## Phase 2：智慧功能 ✅
> RAG 可用、知識圖譜可視覺化、弱項自動出題｜對應 Knowledge / Quiz / Workspace 擴充
- [x] 2-1 RAG 知識檢索（pgvector + LlamaIndex IngestionPipeline + 檢索 service + 注入 EDF）
- [x] 2-2 知識圖譜（concepts/edges schema + 查詢 service + Cytoscape.js 渲染 + Detail Panel + Obsidian 風格精修）
- [x] 2-3 精熟度追蹤（student_mastery + BKT 公式更新 + 圖譜節點著色）
- [x] 2-4 智慧出題（Select 弱項 + Generate LLM+RAG + Validate 自審 + Quiz API）
- [x] 2-5 Pre-Coding Reflection（reflections 表 + 評估 service + 觸發 UI + 側邊欄 + 注入 EDF）
- [x] 2-6 Post-Solution Comprehension（EPL + Predict + Variation + 動態觸發 + BKT 串接）

## Phase 3：學習體驗 ✅
> 學生可從頭到尾跟隨學習路徑、完成測驗、查看進度｜對應 Learn / Quiz / Dashboard
- [x] 3-1 結構化學習路徑（learning_paths/units schema + 拓撲生成 + Learn 頁 + onboarding seed + 單元內容頁 + ExercisesTab）
- [x] 3-2 Quiz 完整版（MC/Coding UI + 計時器 + Hint 5 級 + 結果頁 + EDF 回饋）
- [x] 3-3 Dashboard（4 統計卡 + 今日建議 + 活動時間線 + 精熟度總覽圖表）

## Phase 4：部署準備（容器化 + 配置層）✅
> 一次性處理 Docker / Zeabur / Judge0 自架 / NextAuth callback / CORS / API proxy；上線驗證已搬至 Phase 7
- [x] 4-1 容器化（Dockerfile build / pgvector image / Judge0 自架 docker-compose）
- [x] 4-2 Zeabur 部署準備（環境變數分層 / service 串接 zeabur.json / NextAuth callback + CORS）

> ⚠ 原 4-3 上線驗證（Golden path / 監控 / 效能 baseline）已搬移至 **Phase 7**

---

## Phase 5：教師端（不需實際部署即可開發）
> 教師可管理班級、查看學生行為分析圖表、指派作業｜對應 Teacher Dashboard
> **前置條件**：Phase 4 完成。
> **資料策略（2026-07-06 修訂）**：5-1 / 5-2 / 5-5 無真實學生資料依賴，**前移至 Phase 7 部署前開發**（5-2 收集機制必須先上線才有資料累積；5-5b 用 DEV-E 假學生 seeder 開發）；**5-3 / 5-4 延後至全案最後**——等 Phase 7 上線累積真實行為資料後才做（原「合成資料先寫」註記作廢）。

### 5-1 班級管理
- [x] 5-1a classes + class_members 表 migration（`l8a9b0c1d2e3` + `models/classroom.py`；up/down 實跑可逆驗證）
- 5-1b 班級 + 學生身分 API（2026-07-07 需求擴充：學生補填校名/系所/學號/姓名 → 教師名冊 + 學生右上角顯示）
  - [x] 5-1b-1 student_profiles 表 migration（`m9b0c1d2e3f4` + `models/student_profile.py`；1:1 user_id PK / 學號不 unique / up-down 可逆驗證）
  - [x] 5-1b-2 班級 CRUD API（`POST/GET/PATCH /classes`；6 位數字碼 secrets 產生+碰撞重試；require_roles(TEACHER)；他人班級 404；含成員數；7 route tests）
  - [x] 5-1b-3 加入班級 + profile API：`GET/POST /profile`（upsert，email 來自 users）+ `POST /classes/join`（驗碼入班 idempotent + 未填 profile 回 409 PROFILE_REQUIRED + 停用/無效碼 404）+ `GET /classes/{id}/members` 教師名冊（僅擁有者）；13 route tests
- 5-1c 教師 Dashboard + 學生 profile UI（前端）
  - [x] 5-1c-1 教師班級管理頁（`/teacher`：建班/邀請碼複製/名冊展開/停用；role gate + avatar 選單教師入口）— **UI 驗收通過**（含修 `/users/me` 路由碰撞 + 身分切換即時更新選單 + 精簡選單移除空殼學習總覽/通知）
  - [x] 5-1c-2 學生 profile 表單 + 首次登入 gate（`ProfileGate` 包 AppShell：student 未填 → 全屏填寫頁；教師放行；fail-open）— **UI 驗收通過**
  - [x] 5-1c-3 右上角導覽顯示學生身分（avatar 選單真名 + 校系 + 學號；隨 role 切換即時更新）— **UI 驗收通過**（5-1c 全數完成）
  - [x] 5-1c-4 學生加入班級 UI（2026-07-12 補規劃缺口：後端 join API 一直存在但前端無入口）：共用 `JoinClassForm`（6 位碼驗證）掛作業頁空狀態 + Settings「我的班級」卡（僅學生，列已加入班級）；後端補 `GET /classes/mine`（學生視角不含邀請碼；+2 tests，730 passed）— **UI 驗收通過**（2026-07-12）
> 決策（2026-07-07）：profile 存 student_profiles 獨立表；首次登入強制引導（僅 role=student）；學號不做唯一約束；邀請碼 6 位數字
- 5-1d 身分自選 onboarding + 身分重置（2026-07-07 決策：production 自選教師/學生；單一身分；設定頁可切換身分＝全資料重置 + 警告）
  - [x] 5-1d-1 users 加 `role_selected` 布林 migration（`n0c1d2e3f4a5`，server_default false）+ `/users/me`·`/auth/me` 回傳（可逆驗證）
  - [x] 5-1d-2 後端 `POST /users/role` 自選/切換身分（`services/identity.py`）：首選只設定、已選過再改＝全清（reset_user_data + profile + class_members + 教師 classes）；admin 不可自選 422；5 route tests
  - [x] 5-1d-3 前端 onboarding 身分選擇頁（`RolePicker` + `OnboardingGate` 三段：選身分→學生填 profile→放行）— **UI 驗收通過**
  - [x] 5-1d-4 Settings 身分重置卡（`identity-card.tsx`，二段確認 + 全清警告 + 成功後導回 onboarding）— **UI 驗收通過**（5-1d 全數完成，5-1 班級管理收尾）
> ⚠ 提權風險已知悉：自選教師＝任何人可看全班 PII；使用者評估後接受（單一教授小課程情境）

### 5-2 行為資料收集（Module 9）
> **OSS**：✅ Tier 2 採用 ProgSnap2 EventType schema + StudyChat dialogue act 分類 schema
- [x] 5-2a coding_events 表 migration（`o1d2e3f4a5b6` + `models/coding_event.py`；ProgSnap2 EventType 6 值 String+CHECK；id=EventID/user_id=SubjectID；concept_tags/execution_result/event_metadata 用 JSON；(user_id,created_at) 索引；up/down 可逆驗證）
- [x] 5-2b event logging service（`services/analytics/events.py`）：`log_execution` 從 Judge0 分類 success/compile_error/runtime_error + `log_coding_event` best-effort（失敗吞例外+warning）；掛 `/code/execute`（執行結果）+ chat interact（hint_level>0 記 hint_request）；6 tests
- [x] 5-2c chat_messages 擴充 dialogue_act 欄位（migration `p2e3f4a5b6c7`；String+CHECK 6 值 StudyChat schema；啟發式 `classify_dialogue_act` 純函式掛 interact，訊號不足留 NULL；11 tests）
- [x] 5-2d 行為指標聚合 service（`services/analytics/aggregate.py` `aggregate_user_behavior`：執行次數/成功率/修復時間配對/hint 分布/dialogue_act 分布 + 時間窗；compute-on-read 不建預聚合表；7 tests）

### 5-3 行為分析演算法（Module 9）
> **OSS**：✅ Tier 1 pyBKT + `prefixspan`（sequential pattern mining，**取代 AGPL 的 PM4Py**）
- [ ] 5-3a 行為-成效相關性分析（行為指標 vs 精熟度提升）
- [ ] 5-3b 學生行為模式群聚（主動型/被動型/掙扎型分群，scikit-learn KMeans）
- [ ] 5-3c 行為流程分析（**用 prefixspan**，禁止用 PM4Py）
- [ ] 5-3d 行為分析 API 端點（班級/個人行為統計 + 圖表資料）

### 5-4 行為分析視覺化（Module 9）
> 參考：OpenLAP 三層架構（Data Collection → Indicator Engine → Analytics Framework）
- [ ] 5-4a 行為-成效散佈圖 + 錯誤類型熱力圖
- [ ] 5-4b 學習行為時序圖 + Hint 階梯使用分布
- [ ] 5-4c 班級行為群聚分析圖 + 精熟度趨勢線

### 5-5 作業指派（2026-07-07 定案：TronClass 式文件繳交，非題庫 quiz）
> **決策**：教師建立作業（標題 + 內容 + 附件）→ 指派**整班** → 學生繳交（文字 + 附件）→ 教師人工檢視 + **評分/評語**。檔案存 **Postgres bytea**（Zeabur 容器 fs ephemeral；單檔 ≤ 10MB + 型別白名單）；學生**雙入口**（頂部「作業」tab + Dashboard 待辦卡片）。
> ⚠ 原 5-5b「精熟度熱力圖 + 常見錯誤統計」與文件繳交無關 → 回歸 **5-4 行為分析視覺化**（本就在那）；5-5b 重定義為「學生繳交 + 教師交件檢視」。
- 5-5a 作業建立 + 附件（教師端）
  - [x] 5-5a-1 3 表 migration `q3f4a5b6c7d8` + models（assignments / assignment_submissions / attachments 多型 bytea；單檔 CHECK ≤ 10MB；submission UNIQUE(assignment,student)；up/down 可逆驗證）
  - [x] 5-5a-2 教師作業 CRUD + 附件上傳/下載 API（`services/assignment/` + `api/routes/assignments.py`：CRUD 擁有權 404 + PATCH 可編輯/清除 due_at；附件 bytea 上傳白名單+10MB+下載授權+Content-Disposition attachment；python-multipart；15 tests）
  - [x] 5-5a-3 教師作業 UI（建立表單含截止時間 + 拖曳上傳 + 作業卡編輯/停用/刪除 + 附件懶載入下載/續傳；`GET /assignments/{id}` 補 attachments）— **UI 驗收通過**（導航位置另見 5-6）
- 5-6 教師端導航與教材檢視（2026-07-08 使用者回饋：班級/作業移入導航、師生導航分流、Learn 全開、題庫檢視）
  - [x] 5-6a 角色化導航（教師＝班級|作業|Workspace|Learn，移除 Quiz/Knowledge；班級/作業移出 avatar 選單進頂部導航；`useRole` hook；教師登入預設落地班級管理；`/teacher` 拆 layout gate + 班級/作業兩 route）— **UI 驗收通過**（2026-07-12）
  - [x] 5-6b Learn 教師權限全開（`ghostUnlock = useGhostUnlock() || role==="teacher"`，複用 DEV-4 幽靈解鎖鏈路讓教師點閱全部 locked 單元）— **UI 驗收通過**（2026-07-12）
  - [x] 5-6c Learn 單元頁題庫檢視（`GET /quiz/bank?tag=` teacher-gated 回完整 content+解析；`TeacherQuestionBank` 元件 + unit-content 教師專屬「題庫」tab；解答預設隱藏 + 顯示/隱藏切換 + 正解綠框；6 route tests）— **UI 驗收通過**（2026-07-12）
- 5-5b 學生繳交 + 教師交件檢視
  - [x] 5-5b-1/2 後端（`services/assignment/submissions.py` + `api/routes/assignment_submissions.py`）：學生 `GET /assignments/mine`（+`/mine/{id}` 詳情含教師/繳交附件）+ `PUT /assignments/{id}/submission`（upsert 重繳覆蓋）+ `POST /submissions/{sid}/attachments`；教師 `GET /assignments/{id}/submissions`（名冊×狀態）+ `PATCH /submissions/{sid}/grade`（評分+評語）；attachment delete 通用化（作業限教師/繳交限本人）；8 tests
  - [x] 5-5b-3 學生作業 UI（學生導航加「作業」tab → `/assignments` 列表/詳情 + 繳交表單（文字+拖曳上傳+刪除繳交附件）+ 下載教師附件 + 顯示分數/評語 + 逾期軟提示；Dashboard「待辦作業」卡片）— **UI 驗收通過**（2026-07-12，含繳交狀態徽章修訂）
  - [x] 5-5b-4 教師交件檢視 UI（作業卡「交件」展開：名冊×狀態+繳交率 → 檢視文字/下載繳交附件 + 評分+評語即時回寫；後端 submissions 列表加繳交附件 meta；728 tests）— **UI 驗收通過**（2026-07-12，含可點卡片動線修訂）

---

## Phase 6：教學內容建構（NotebookLM grounded 模式 — 內容必須來自實際影片）🎯 進行中
> 62 個學習單元的 4 個 tab 全部有實質內容、且 LLM 生成內容**完全 grounded 在教授實際影片字幕上**；`learning_units.content` 不再是空骨架。
> **核心架構（NotebookLM 模式）**：YT 字幕 → LlamaIndex IngestionPipeline 入庫 → 生成時 retrieve 該 video 字幕 chunks 注入 prompt → LLM 生成必須引用 timestamp citation、不引入字幕未出現的概念 → 品管抽查時可比對「LLM 生成 vs 影片實際 timestamp 處內容」。
> **資料流**：YT playlist URL → fetcher 抓 metadata + 字幕 → PATCH 寫入 concepts metadata + RAG ingest 字幕 → LLM grounded 生成 unit content → 自行抽查品管 → 修正 prompt 重跑（如需）。
> **OSS**：RAG 沿用 Phase 2-1 LlamaIndex；LLM 生成沿用 Phase 2-4c `services/quiz/generate.py` 與 OpenAI `json_object` mode；字幕抓取沿用 yt-dlp。**禁止為此 Phase 引入新框架**。
> **Concept 範圍**（2026-05-22 修訂）：62 個影片 concept（video_order 1-62）全部進學習路徑；PREREQUISITE 鏈 1→2→3→…→62 完整串連。1-3 仍保留 `category="課程介紹"` 供未來知識圖譜 styling 區分使用。

### 6-1 影片資料整合（metadata + 字幕 RAG ingest）✅
- [x] 6-1a 教授交付 playlist URL（62 部影片完整對齊 video_order 1-62）
- [x] 6-1b/b+ fetcher script + 62 列 CSV
- [x] 6-1c video 1-3 concept seed migration（2026-05-22 修訂：加 PREREQUISITE 邊 1→2→3→4 並進路徑；保留 category="課程介紹" 標記供未來圖譜 styling 區分）
- [x] 6-1d PATCH script 寫入 62 筆 metadata 至 DB
- [x] 6-1e（NotebookLM 核心）Whisper 全 62 部 transcript + 12 global corrections + 861 chunks 入 RAG（spot retrieve 4/4 命中）
- [x] 6-1f tech-debt 同步

### 6-2 Unit content 批次生成（grounded on YT 字幕）
- [x] 6-2a Grounded prompt template + Pydantic 模型 + 13 mock-LLM 測試
- [x] 6-2b 批次生成 infra：retrieve metadata filter + staging 表 + retry + promote helper + 18 個 mock+DB 測試
- [x] 6-2c 概念說明 tab：YT player IFrame embed（依賴 6-1d metadata；timestamp citation 點擊跳到對應影片時間點）
- [x] 6-2d 範例 tab：渲染 LLM 生成的程式碼範例 + 「在 Workspace 開啟」按鈕（復用 Phase 2-5d sessionStorage）+ citation 標示
- [x] 6-2e 摘要 tab：渲染 grounded `summary.key_points` bullet + citation 標籤 + needs_more_source notice + legacy string fallback（fallback 已驗，grounded 主路徑延至 6-4a-deferred-ui）

### 6-3 練習題庫補充（grounded）
- [ ] 6-3a 用 Phase 2-4 智慧出題管線批次模式為每 unit（4-62 共 59 個）生成至少 2 題；**generate prompt 加 grounding 規則**：題目情境必須與該 video 字幕中出現的範例 / 變數命名一致；validated=True 才入庫
  - [x] 6-3a-1 `generate_question(video_order=...)` grounded mode：grounded RAG 走 `get_chunks_by_video_order` + system prompt 加 grounding 規則 + 4 mock tests（480 全綠）；`video_order=None` 走原 semantic path（backward compat）
  - [x] 6-3a-2 批次 script + service：`services/quiz/batch_generator.py`（per-concept 跑 N 題 × generate+validate × MAX_VALIDATE_RETRIES=2）+ CLI `scripts/generate_unit_questions.py`（--only / --force / --dry-run）+ 8 mock+DB tests（488 全綠）；預設題型 mix multiple_choice + coding；validate fail 自動 retry，generate fail 直接 abort 與 orchestrator 一致
  - [x] 6-3a-3 實機 LLM 全跑（2026-07-06 ✅）：62 concept 題庫批次 + 補跑 → 138 題 validated（詳見 decisions.md；v17/v41 掛零 + 3 concept 缺 1 題記 tech-debt 待 6-4b）
- [x] 6-3b ExercisesTab 改造：從「按需現生」→「優先讀題庫，題庫不足才現生」(GET /quiz/from-bank + ApiRequestError 404 QUESTION_BANK_EMPTY fallback；6 bank service tests + 5 route integration tests；前端 Loading 文案分「查找題庫題目 (< 1 秒)」/「AI 正在生成 (5-15 秒)」兩階段)
- [x] 6-3c 知識點驅動題量（2026-07-06 晚間程式碼完成）：知識點萃取 service + 每點 1 MC + coding 固定 1 題（intro 0）+ `QuestionSource.BATCH` 分流（migration `k7f8a9b0c1d2`）+ `GET /quiz/unit-set` LEARN 整組作答 + validate 加 `point_meaningful` 面向 + generate「考點有意義」規則 + LEARN 前端整組逐題（`concept-quiz-tab.tsx`，不呼叫 LLM）+ `rereview_questions.py`；627 tests；實機批次已跑 ✅（同日隨 6-3d：436 MC 覆蓋 61/62 片 + 57 coding + 舊題複審刪 15，見 changelog）
- [x] 6-3d QUIZ 弱項綜合測驗組（2026-07-06 完成，程式碼 + 實機題庫；文獻標注 references.md §5.1）：multi-concept generate + blueprint/plan（掌握度自適應）+ 題庫優先≤30%並行組裝 + `POST /quiz/weakness-set?count=10|25` + 前端 10/25 選擇逐題作答；程式題強模型 + 審查加考點有意義 + 舊 MC 複審刪 15 + LEARN 資料驅動 tab 隱藏。原始需求規格 ↓
  - **需求**：QUIZ 弱項模式從「單節點、一題一題現生」→「一次生成整組 10 或 25 題」，含單節點題 + 綜合相連節點（多跳）題
  - **決策（使用者三問定案）**：
    1. 題型比例 = **依掌握度自適應**（整體掌握度低 → 偏單節點精準補強；掌握度回升 → 自動提高綜合題比例）
    2. 生成策略 = **題庫優先只補缺口 + 並行生成（asyncio.gather）+ 進度條**；**重用舊題比例 ≤ 30%**（其餘 ≥70% 為當下新鮮生成，優先未答過題）
    3. 程式題 = 每組 **1-2 題**，每題 **1 個弱項目標 + 2 個已掌握相連節點當鷹架情境**（ZPD + interleaving，避免全弱項過難）
  - **文獻依據**：Interleaving/Desirable Difficulties（Bjork）、ZPD/Scaffolding（Vygotsky）、CAT content balancing、概念圖感知題目序列化（GNN+RL）、多跳 KGQA
  - **技術要點**：generate 需支援「多 concept_tag 綜合出題」prompt 模式；多節點選法用現有 `get_prerequisite_closure`；程式題鷹架節點取「已掌握（effective confidence 高）的相連節點」；新端點 `POST /quiz/weakness-set?count=10|25`（需 rate limit 放寬）；前端 QUIZ 頁改題數選擇 + 進度條 + 整組作答

### 6-4 內容品管（2026-07-06 晚間再修訂：正式抽查移除，改由使用者實際操作回饋）
- ~~6-4a 自行抽查~~ → **移除（2026-07-06 晚間使用者決策）**：staging 62 部已全量 approve + promote（`scripts/promote_unit_content.py`，promote 時剝除 summary/code_examples 殘留 key）；品質問題由使用者實際操作時回饋
- ~~6-4a-deferred-ui~~ → 6-2d/6-2e 已作廢；**6-2c citation 跳轉**（grounded markdown + `player.seekTo`）併入使用者實際操作驗證
- [ ] 6-4b 依使用者操作回饋調整 6-2a prompt template 並針對問題 unit 局部重跑；對品質太差的 unit 評估升級到 Whisper 重 transcribe（B 方案）作為 source；**含題庫缺題補生**（v17/v41 掛零等，見 tech-debt）

> ⚠ 原 6-5（Coddy 對話品質）與 6-6（知識圖譜優化）已於 2026-07-04 依功能規格書**整併至 Phase 6-K**（6-5 → K4；6-6 → K1 + K5），原 sub-task 內容完整保留於對應 K 項。

### 6-M LLM 模型選型 v2 — 任務導向路由（2026-07-06 session 定案）
> **背景**：原論文規格指定 GPT-4o（2024 舊世代）；2026-07-06 定案改為「依任務特性路由模型」（cascade 設計：弱模型生成 + 強模型審查）。**📌 論文關鍵技術**：FrugalGPT（Chen et al. 2023）、RouteLLM（Ong et al. 2024），引用見 `references.md` §5.1；論文實驗章節記錄實驗當下確切模型版本。
> **選型表**：對話組（EDF Feedback）+ 分析組（Evidence / Reflection / Comprehension 評分）= `gpt-5.4-mini`（K4d 實測不足再升 5.4）｜生成組（Quiz generate / Hint / Comprehension 出題）= `gpt-5-mini`｜審查組（Quiz validate）= `gpt-5.4`｜Unit content 6-2b 批次 = `gpt-5.4`（教科書本體，品質優先）｜Embedding 維持 `text-embedding-3-small`（861 chunks 已入庫不重嵌）。
> **費用**：一次性批次 ≈ $6.6（content $4 + 題庫生成 $1 + 審查 $1.6）；儲值 $10；上線後即時互動估 $35-40/月（100 學生）。不採 OpenAI Batch API（省 <$1.5 不值得改寫非同步流程）。
- [x] 6-M1 分組模型環境變數（2026-07-06 ✅）：config 三組變數 + fallback property + 11 個呼叫點切換 + .env 套用選型表；608 tests 全綠
- [x] 6-M2 模型全面升級 gpt-5.6 世代（2026-08-05 實測定案，取代上表選型）：對話+分析+生成＝`gpt-5.6-luna`（$0.20/$1.20）、審查+內容＝`gpt-5.6-terra`（$2.00/$12）；**每項都更便宜且更新世代**，單次互動 $0.00316 → $0.00081（省 74%），100 人×80 則/月 $25.3 → $6.5。修 `core/llm_params.py`——gpt-5.6 拒收 `temperature` 也拒收 `reasoning_effort`（原只認 `gpt-5-` 前綴 → 502）
- [x] 6-M3 成本控制三層（2026-08-05）：① 主題限制寫進 Evidence prompt ② **離題分流**（`services/edf/off_topic.py`——判斷搭既有 Evidence 呼叫零額外成本、Feedback input 1699→135 省 92%、`dialogue_act=off_topic` 回填供評估期統計）③ **每日配額** `RATE_LIMIT_LLM_PER_DAY=60`（僅 scope=llm、UTC 分 key、超額明示明日重置）；+10 tests（773）。**決策：不做上課日分級配額**——省的錢遠小於複雜度且傷週末複習體驗；業界基準 CS50.ai 為 $1.90/學生/月

### 6-R 健壯性強化（2026-07-04 架構審查新增，同日完成）✅
> 背景：上線前架構審查發現三個系統性缺口：可觀測性為零（500 不留痕）、安全規範未落地（rate limit / token exp 只在文件）、外部依賴網路例外未馴服。全部本機完成 + 測試驗證（後端 513 tests 全綠，+14 新測試）。
- [x] 6-R1 (H) `unhandled_error_handler` 補 traceback logging（6-4a 實機跑前置）
- [x] 6-R2 (H) NextAuth token `exp` 驗證（401 TOKEN_EXPIRED）+ 前端 401 統一重導 /login
- [x] 6-R3 (H) per-user rate limit（`core/rate_limit.py` Redis INCR+EXPIRE，fail-open；掛 12 個 LLM 端點 + /code/execute；429 帶 retry_after_seconds）
- [x] 6-R4 (M) Judge0 httpx 網路例外 → 503 JUDGE0_UNAVAILABLE（submit）/ 該輪重試（polling）
- [x] 6-R5 (M) Evidence 層 LLM 回傳 ValidationError → 502 LLM_PARSE_ERROR（quiz 系列原已防護）
- [x] 6-R6 (M) chat interact fail-safe：user message 於 LLM 呼叫前先 commit，LLM 失敗不丟學生輸入
- [x] 6-R7 (M) `get_or_create_user`：首登並發 IntegrityError 重查 + last_login_at 1 小時節流
- [x] 6-R8 (L) `func.count()` 取代全表載入（chat/quiz）/ 容錯 except 補 `logger.warning` / Next proxy 30s timeout（504 BACKEND_TIMEOUT）/ 422 統一 VALIDATION_ERROR 格式

---

## Phase 6-K：K-Graph 自適應學習引擎（2026-07-04 功能規格書新增）🎯
> 目標：把知識圖譜從「靜態視覺化」升級為驅動自適應學習的核心引擎——學生依各自難度與弱點學習。
> **整併說明**：原 6-5 全部併入 K4；原 6-6a/c/d 併入 K5、6-6b 併入 K1。tech-debt「跨章節 PREREQUISITE 邊未標」由 K1 消除、「EDF Mastery 連動暫時退場」由 K2 消除、「Learn 頁 graph 版升級」併入 K5 評估。
> **執行順序依據（依技術相依性）**：K1 資料基礎（多對多邊 + 圖走訪）→ K2 狀態數據源 → K3 依賴 K1 走訪 + K2 狀態 → K4 消費 K2/K3 輸出 → K5 視覺化需要 K1 邊 + K2 動態狀態才有內容可畫。
> **可行性註記**：schema 原生支援多對多（`concept_edges` unique triple）、拓撲排序已處理 DAG、mastery 已有 BKT——K1/K2 主要是資料與整合工作，非架構重寫。

### K1 跨章依賴多對多圖（功能一；吸收原 6-6b）
- [x] K1a curated 依賴 DAG migration（`i5d6e7f8a9b0`）：以 curated map（每 concept 1-3 個真實直接前置，依 C++ 教學相依性 + RAG 字幕輔助判斷）取代線性鏈 61 條 → **90 條多對多 PREREQUISITE 邊**；全部 source.video_order < target.video_order 保證無環；除 video 1 外每節點至少 1 條入邊保證連通
- [x] K1b `get_prerequisite_closure` 圖走訪（`services/graph/traversal.py`：單查詢載邊 + 記憶體 BFS + max_depth 限制 + 菱形去重；5 tests）— K3 根源回溯的基礎
- [x] K1c 實機驗證：alembic upgrade 實跑 + DB 驗證（90 邊 / 遞迴←25+37+38 / 0 孤兒節點 / 0 反向邊）
- [ ] K1d UI 抽查：`/knowledge` 頁面確認多對多邊渲染正常、Learn 路徑生成不受影響（2026-07-06 改使用者 session 後自測，有問題再回報，不排入開發批次）

### K2 動態知識狀態追蹤（功能二；2026-07-04 缺口分析後細化）
> 缺口分析：`GET /concepts/mastery` 已提供 per-concept 狀態（K2b 原規劃的 80%），缺 `last_practiced_at`；真正缺的是 EDF 20 粗 tag → 62 影片 concept 的橋接。
- [x] K2a EDF ConceptTag → 影片 concept 對映（migration `j6e7f8a9b0c1` + `services/mastery/resolve.py`）：20 tag 中 10 個有課綱覆蓋（59 concepts 對映、課程介紹 3 個 NULL），其餘照舊跳過；**三層 fan-out**：① tag 直接命中照舊 → ② parent group 只更新已曝光組員 → ③ 全未曝光只更新組內入門 concept；5 fan-out tests + 實機驗證 mapping 分布
- [x] K2b 擴充既有 `GET /concepts/mastery` 加 `last_practiced_at`（不新建 k-state 端點）；1 test
- [x] K2c 程式碼分析信號決策（2026-07-04 記錄）：**現階段沿用 LLM Evidence，不引入真 AST**——LLM 已輸出 concept_tags + error_type + bloom（等效於 AST→概念對映的產物）；tree-sitter/libclang 需自建「AST 特徵 → concept」規則工程，成本高且與 LLM 重複；待 Phase 5 行為資料可檢驗 LLM tagging 可靠度後重評（記 tech-debt）

### K3 根源弱點定位器（功能三；2026-07-04 細化，後端同日完成）
- [x] K3a 觸發器：stateless 連續失敗判定（最近作答由新往舊數、遇答對截斷；streak >= 3 觸發；無新表）
- [x] K3b 回溯演算法（`services/diagnosis/root_cause.py`）：closure max_depth=3 回溯；嫌疑排序 = 已曝光低 confidence（depth 淺、conf 低優先）→ 未曝光盲區（depth、video_order）；已曝光高 confidence 前置排除；上限 3 個
- [x] K3c 診斷驗證：每個嫌疑節點附題庫 validated 診斷題 question_id（題庫無題為 null）；作答走既有 /quiz/submit 自然寫回 mastery，不重造判分
- [x] K3d-API `GET /concepts/{tag}/diagnosis`（未觸發回 triggered=false 供前端隱藏入口）；9 tests
- [x] K3e 前端入口：答錯自動查診斷（未觸發自動隱藏）→ 嫌疑鏈 + 微測驗（`GET /quiz/questions/{id}` 直取診斷題）+ 補救開放 + 知識圖譜 `?remedial=` 跳轉；4 route tests

### K4 Coddy 自適應提示 + 補救路徑（功能四；吸收原 6-5 全部）
- [x] K4a K-Graph State 注入 EDF Feedback prompt（`services/edf/kgraph_context.py`）：解析 evidence tags（直接命中 + parent group 已曝光成員）→ 依最弱概念 confidence 分級鷹架（<0.4 填空/拆解、0.4-0.7 引導提問、>0.7 只點 edge case）；persona 改寫為 Coddy 自然語氣 + RULE-5 允許行動建議收尾（原 6-5b）；7 tests
- [x] K4b RAG 觸發改內容相關性：`TeachingStrategy` 移除 `use_rag`，Feedback 層每次檢索、`RAG_MIN_SCORE=0.40` 分數過濾（原 6-5a）；門檻初始值待 K4d 依實際命中率調整；tests 更新 +2
- [x] K4c 補救路徑（`services/learning/remedial.py` + `POST /concepts/{tag}/diagnosis/remediate`）：診斷觸發後把嫌疑概念在 default path 的既有 units **重新開放**（completed/locked → available、清 completed_at；系統級動作繞過手動轉移限制）；不新建 row 不動 order 唯一約束；order_index 升冪 = 建議補救順序；未觸發回 409；5 tests
- [ ] K4d 真人測試驗收（原 6-5c）：比對改動前後語氣 / RAG 命中率（含 RAG_MIN_SCORE 調參）/ 鷹架適切度 / 補救路徑 Learn 頁呈現（2026-07-06：RAG_MIN_SCORE 調參與對話組模型是否升 `gpt-5.4` 併入第 5 批實機批次執行；語氣部分使用者自測）
- [x] K4f 編譯失敗主動說明（2026-08-05 使用者定案）：`services/run_help.py` + `POST /chat/run-help`——平台限制（引用平台沒有的函式庫）機械判定 + 固定文案**不呼叫 LLM**；學生自己的編譯錯誤走 LLM 引導（禁給修好的程式碼）；前端僅編譯失敗觸發 + 錯誤簽章去重（同一錯誤只說明一次，省配額）；+10 tests（793）
- [x] K4e Coddy 防幻覺三層（2026-08-05 使用者驗收發現時間戳為幻覺後新增）：`services/edf/citations.py`——① `strip_ungrounded_citations` 機械攔截不在檢索結果內的影片連結（容差 ±90s、非 YouTube 連結保留、攔截寫 log 可統計幻覺率）② `NO_SOURCE_RULE` 檢索無命中時明確禁止提及章節時間並誠實告知 ③ `extract_citations` + migration `t6c7d8e9f0a1`（`chat_messages.citations`）+ 前端 citation-list 元件（已刪除）摺疊顯示 transcript 原文供學生核對；+13 tests（763）。**限制**：出處已鎖死，內容曲解仍需第二次 LLM 比對，成本翻倍故不常態開啟。**2026-08-06 註**：③ 的 UI 已隨 7-U3 移除（元件檔已刪，citations 仍存 DB），防幻覺實際剩 ①② 兩層

### K5 知識圖譜視覺改版（功能五；吸收原 6-6a/c/d）
- [x] K5a 套件調研決策記錄：維持 Cytoscape.js + fcose（決策記錄見 `docs/references.md` §1；dagre 不支援 compound、React Flow 定位 workflow editor 無決定性優勢）
- [x] K5b 多對多邊 + 熟練度視覺：節點填色改 mastery band + 分章 compound cluster + prerequisite 箭頭強化；`toElements` 拆至 `knowledge-graph-elements.ts`；**2026-07-05 迭代（使用者三輪回饋）**：fcose → 確定性 preset 佈局 → **太陽系主題定案**（星雲雙層視圖（overview 章節級星系 ⇄ detail 概念級，zoom 門檻 crossfade）、蛇形軌道 + 軌道線/星空 underlay、點擊即聚焦、全覽鈕、zoom cap、跨章邊淡出；星系 SVG 隱形根因 = 缺 width/height；當時留作備援的 galaxy-backgrounds 模組已隨七驗移除星雲圖層一併刪除）；**2026-07-05 六驗**：overview 改語意縮放——保留全部概念節點與名稱、依 zoom 門檻放大節點/字體並重排每章緊湊網格（移除章節星系節點層，`overview-layout.ts`）；**七驗**：移除星雲背景圖層（純黑星空）+ 修 detail panel setState-in-effect lint
- [x] K5c 個人化路徑高亮：underlay ring = 路徑狀態（藍=目前 / 綠=已完成 / 紅=補救嫌疑，`?remedial=` query 觸發 + 鏡頭聚焦）；R1-R8 檢核通過（灰階 cluster 容器、無外來 hex、無 emoji）
- [ ] K5d 真人測試驗收（原 6-6d）：學生能從圖讀懂自己的進度與弱項，不只是好看（2026-07-06 改使用者 session 後自測，不排入開發批次）

### K6 熟練度演算法 v2 — 訊號分級 + 遺忘衰減 + 透明化（2026-07-06 session 定案）
> **動機**：現行 `services/mastery/updater.py` 對 quiz 作答與 chat 對話用同一組 BKT 參數全額更新（quiz 權重過高），且標準 BKT 無遺忘機制（confidence 只增不減）。
> **📌 論文關鍵技術**（完整引用清單見 `docs/references.md` §5.1）：BKT（Corbett & Anderson 1995）、BKT+Forgetting（Khajah et al. 2016）、Ebbinghaus 遺忘曲線指數衰減、FSRS 記憶穩定度、Duolingo HLR、Open Learner Model（Bull & Kay）。
- [x] K6a 訊號分級 BKT 參數：`BKT_CHAT_PARAMS(learn=0.05, slip=0.3, guess=0.4)`——chat 傳弱證據參數、quiz/comprehension 沿用強證據預設；雙向更新幅度皆顯著小於 quiz（測試驗證）；Phase 5 真實資料後用 pyBKT `fit()` 替換
- [x] K6b 遺忘曲線惰性衰減：`services/mastery/decay.py`（floor=0.25、基準半衰期 14 天、半衰期隨 success_count +50%/次、上限 180 天）；套用點＝mastery summary（K4 鷹架連動）+ quiz Select（衰減回弱項會重新被選中）+ K3 診斷嫌疑判定；讀取端惰性計算、DB 原值不動
- [x] K6c 事件級透明化：API 加 `raw_confidence`/`days_since_practiced`/`due_for_review` 衍生欄位；detail panel 顯示「已 N 天未練習，掌握度自 X% 回落至 Y%——建議複習」（framing 複習提示非扣分）；圖譜節點 band 色以 effective confidence 驅動自動變暗；無逐筆帳本

### DEV 開發者模式（2026-07-05 與使用者共同定案：Settings 入口 / 分類重置 / 真改 DB role / A+B+C+D 全納首版）
> **安全前提（不可妥協）**：後端 `DEV_MODE_ENABLED` 總開關（生產預設關）+ `DEV_MODE_EMAILS` email 白名單，兩者皆環境變數（白名單不寫死、不進 git）；所有 dev 變更端點掛 `require_dev_user` 逐一驗證（403），前端 UI 只是入口不是防線；操作寫 log 留痕。
- [x] DEV-1 後端 gating 基礎：config 雙環境變數 + `core/dev_mode.py` `is_dev_email` + `require_dev_user` dependency + `GET /dev/status` + rate limit 豁免（追加功能 B）；11 tests
- [x] DEV-2 Settings「開發者工具」區塊殼 + `useDevMode`（打 `/dev/status`，非 dev 完全不渲染）
- [x] DEV-3 分類重置：熟練度 / 課程進度 / 測驗紀錄 / 對話紀錄四鍵 + 一鍵全部（`POST /dev/reset`，二段確認）
- [x] DEV-4 幽靈解鎖：純前端開關（localStorage + 僅 dev 生效）locked unit 可點瀏覽；unit 內容後端本就回傳給本人，狀態轉移限制不變
- [x] DEV-5 熟練度編輯器：章節/單一概念 + confidence 滑桿（`PUT /dev/mastery` upsert）
- [x] DEV-6 身分切換：student ⇄ teacher 真改 `users.role`（`PUT /dev/role`；教師端 UI 待 Phase 5）
- [x] DEV-7 EDF Debug 面板（追加 A）：interact `debug_sink` 收集 evidence/strategy/RAG 分數/kgraph（dev 才附、僅當輪不持久化）+ AI 訊息下摺疊面板
- [x] DEV-8 K3 診斷模擬器（追加 C）：`POST /dev/simulate-failures` 注入連錯 N 次（stub 題可重用）→ 回診斷摘要 + 圖譜補救連結
- [x] DEV-9 題庫檢視器（追加 D）：`GET /dev/questions?tag=` 列題（validate 狀態）+ `/quiz?question=<id>` 深連結直接作答
- [x] DEV-E 假學生資料 seeder（`services/dev_seed/` + CLI `scripts/seed_fake_students.py`：三行為原型塑形 profile+成員+events+chat dialogue_act+mastery；`@seed.dev` 可辨識、一律 purge 可重現；demo 教師/班級 get-or-create；4 tests + CLI 實機驗證）

---

## Phase 6-U：學生端 UI/UX 修正與機制調整（2026-07-06 session 規劃）🎯
> 來源：2026-07-06 session 討論（現狀確認 + 設計裁決 + 待辦清單）。與 Phase 6-K 剩餘驗收、Phase 5 教師端可平行。
> 教師端功能＝既有 Phase 5，不另立項。

### 6-U1 Bug 修正
- [x] U1a 根路由 `/` 的 Phase 1 placeholder 改為 redirect `/workspace`（OAuth callback 落在 `/` 即命中）
- [x] U1b 反思側欄比例錯誤：react-resizable-panels v4 裸數字＝px 非 %（`maxSize={40}`＝40 像素），全改百分比字串
- [x] U1c 反思 handoff gating：`active_reflection_handoff` 標記 + `getHandedOffReflectionId()`，非正確管道進入自動清除殘留

### 6-U2 UI/UX 與機制調整
- [x] U2a QUIZ 介面美化：入口改題型選擇卡（icon + 說明 + aria-pressed）+ 視覺階層重整 + 題庫優先提示；修 exercises-tab / unit-action-bar 兩處 R8.2 ✓ 符號字違規（改 lucide icon）
- [x] U2b 移除 LEARN 摘要：前端 tab + summary-tab.tsx 刪除；生成管線 Summary model / prompt / LLM call 移除（批次省 1/3 calls）；lazy-seed 骨架同步去 summary 欄位
- [x] U2c 拔除課程介紹範例：後端 `concept_category` 直通 UnitOut；前端課程介紹單元隱藏範例 tab；批次生成對 intro concept 跳過 examples LLM call（不標 needs_more_source）
- [x] U2d QUIZ tab 題庫優先：`GET /quiz/from-bank` 支援省略 concept_tag（弱項模式，複用 pick_target_concept）+ question_type 過濾；QuizRunner 兩階段 loading + 404 fallback 現生；**練習題重複曝光 tech-debt 一併消除**（bank 一律排除該生已答過的題，Learn/Quiz 兩入口同時生效；全答過 → fallback 現生新題入庫，題庫自然成長）
- [x] U2e Workspace 程式碼存檔（2026-07-16，決策：DB「我的程式碼」多檔管理）：`code_files` 表（草稿 name NULL 每人一份 + 命名檔案同名覆蓋、上限 50）+ `/code/draft`·`/code/files` API + 前端自動存檔（停輸入 2 秒 + beforeunload/卸載 keepalive 搶救）+ 進頁還原草稿 + Toolbar「我的程式碼」選單（另存/載入/刪除）+ CodeEditor 受控 value（順修 output 收合 remount 掉碼潛在 bug）；+8 tests（738）；2026-07-16 回饋修訂：我的程式碼改左側欄（與反思互斥切換）+ 近實時存檔（0.4s/連續每 2s）+ 修游標跳行（editor 重建依賴）+ Enter 縮排 4 空格；同日再補 Ctrl/Cmd+S（已命名覆寫/未命名另存對話框檔名反白）+ 開新檔案（未存確認）+ 檔名關聯（`opened_name` 存草稿列，重整/再登入停留最後開啟檔案）+ page.tsx 拆分（use-run-code / use-draft-restore）+ 實作題 handoff（自動命名「章節 程式實作題」開檔 + 反思按鈕限定實作題檔案 + 圖示順序調整）；**2026-08-05 生產驗收回饋修訂**：檔名鎖定 `.cpp` 尾綴（後端 `normalize_file_name` + 前端固定尾綴輸入框；副檔名對執行無作用，避免 `main.md` 誤導）+ 點 Toolbar 檔名就地重新命名（`PATCH /code/files`，同列改名不複製、草稿 opened_name 跟隨）+ 修首次草稿併發 INSERT 回 500 + 側欄列表錯誤附原因與重試；+10 tests（783）；**同日再修**：Output 執行歷史移出元件樹（`use-run-history.ts` module store + `useSyncExternalStore` + sessionStorage 最近 20 次）並把版面單一化（`workspace-layout.tsx`）——側欄開合原本會換根節點導致輸出整批消失；`page.tsx` 254→189 行（另拆 `use-reflection-handoff.ts`）— **UI 驗收通過（2026-08-05，含 .cpp 鎖定 / 就地改名 / 輸出歷史與歷史選單 / 滾動條 / 選單溢出全數複驗）**
- [x] U2i Coddy 反思開場（2026-07-16）：`POST /chat/reflection-kickoff` + handoff 自動展開 chat + 開場訊息（肯定亮點/接手跳過的追問/邀請提問；每反思一次；fail-open）— 待 UI 驗收
- [x] U2h 反思評分寬容化（2026-07-16 使用者回饋）：追問可跳過+一輪放行、rubric 初學者校準、門檻 0.45+Bloom 自適應、學生端隱藏分數（詳見 decisions.md）— 待 UI 驗收
- ~~U2f 範例程式製作~~ → **作廢（2026-07-06 晚間決策：範例程式全面移除，見 U2g）**
- [x] U2g LEARN tab 重構 + 移除範例程式（2026-07-06 晚間完成）：tab 改「概念說明 / 程式實作題 / 觀念題」+ intro 隱藏程式題 + examples 管線/前端全移除 + 全量 promote + 移除題庫提示字樣（詳見 decisions.md）

---

## Phase 7：上線實測（須實際部署到 Zeabur / VPS）
> Golden path 跑通、監控告警接通、效能 baseline 記錄；可對外開放給真實學生使用。
> **前置條件**：Phase 4 配置層完成；Phase 6 至少 6-1 + 6-2b 完成（含字幕 RAG ingest + grounded LLM 生成 unit content）；6-R 健壯性 H 級完成 ✅（2026-07-04）；Zeabur 帳號 + VPS（Judge0 self-host）就緒。
> ⚠ 上次卡關於 API 串接（前後端 proxy / NextAuth callback URL / CORS / Judge0 endpoint），重啟前先排查 `web/app/api/*` proxy 設定、`backend/core/config.py` 環境變數、Zeabur dashboard service 連線狀態。

### 7-1 Golden path 整合驗證
- [ ] 7-1a 部署到 Zeabur（web + backend + pgvector + redis）+ ~~Judge0 self-host VPS~~（2026-08-05 改 7-R 自建 runner，B 機部署列 R5）
  - [x] 7-1a-1 部署前置修復（2026-08-04）：`requirements.lock` 補 python-multipart（生產映像缺此套件會啟動即崩，docker build 實測 81 routes）+ `zeabur.json` 補 6-M 模型變數（原本會 fallback gpt-4o）
  - [x] 7-1a-2 Judge0 RapidAPI 鏈路實測（2026-08-04）：正常執行 / 編譯錯誤 / 503 三路徑通過；`_build_headers()` RapidAPI 分支驗證可用
  - [x] 7-1a-3 **生產資料播種 script**（2026-08-04 規劃缺口補齊）：`scripts/seed_production_content.py`——**關鍵發現＝`concepts` seed 用 `uuid4()` 隨機產生 id，生產庫 UUID 與本機不同**，`unit_content_staging.concept_id` 必須以 tag 為橋樑重映射；`data_codedge_rag` 由 LlamaIndex 執行期建表（不在 migration），需 pg_dump 連 schema 搬。本機建 `prod_test` 庫完整演練通過（62 教材 / 628 題 / 861 chunks / 64 documents，0 孤兒、tag 對應一致）
  - [x] 7-1a-4 實機執行播種 ✅（2026-08-05）：pg_dump 搬 RAG 表 → script 灌入生產庫，實機結果 documents 64 / questions 628 / unit_content_staging 62；**同日複驗**：concepts 影片 ID 62/62（含 duration 逐筆比對本機一致）、RAG 861、alembic `t6c7d8e9f0a1`、`learning_units` 62 筆 content 全非空（lazy-seed 已由首次進 Learn 頁觸發並帶入 staging 內容）→ **播種與 metadata 同步全數完成，無待補項**
  - [x] 7-1a-5 script 環境隔離防護（2026-08-05 使用者要求）：`scripts/_db_guard.py`——對生產庫操作時 export 的 `DATABASE_URL` 會殘留在同一個 shell，後續任何 script 都會誤寫生產庫。5 支開發工具掛 `require_local_db`（假學生 seeder / content·題庫批次生成 / RAG ingest / 題庫複審，非本機一律中止無覆寫選項），2 支生產維護工具掛 `confirm_remote_db`（promote / metadata patch，需輸入 yes 或 `ALLOW_PRODUCTION_WRITE=1`）；訊息遮蔽密碼
  - [x] 7-1a-6 生產環境效能根因排除 ✅（2026-08-05）：兩個**僅生產環境會出現**的問題疊加造成「頁面 10 秒」——① Node DNS IPv6 逾時耗盡 libuv threadpool（`NODE_OPTIONS=--dns-result-order=ipv4first` + `UV_THREADPOOL_SIZE=32`，環境變數不在版控，已記入 deployment.md）② Zeabur 邊緣宣告 HTTP/3 使瀏覽器走 UDP（`next.config.ts` 加 `Alt-Svc: clear`，拒絕要求使用者關 QUIC 的方案）；實測 137KB 檔案 18.50 秒 → 166ms、43 筆請求全 `h2`。後端全程無辜（13 端點 2–10ms、前端 trace 699,950 事件僅 1 個 ≥100ms）
- [~] 7-1b Golden path：登入 → 寫碼 → **互動終端執行**（2026-08-06 已通）→ AI 對話 → RAG → 出題作答；**其餘待驗收清單第 1–6 段**
- [ ] 7-1c 教師端帳號 / 班級 / 行為資料端到端驗證（驗收清單第 7 段；**生產環境從未跑過**）

### 7-2 監控與告警
> Sentry / 結構化日誌 / 健康檢查端點的**程式碼**可在本機預先寫好，但接通告警鏈路、Log aggregation、Sentry 收 issue 都需實際部署。
> ⚠ 2026-08-06 起 B 機 runner 也需納入監控（`GET /healthz` 已具備 queue/cache/session 觀測欄位）。
- [ ] 7-2a Sentry SDK 整合（前後端 init + DSN 環境變數 + 異常捕捉）— 程式碼可本機完成
- [ ] 7-2b 結構化日誌（structlog / loguru + request_id middleware）— 程式碼可本機完成
- [ ] 7-2c 健康檢查端點分離（/health/live + /health/ready）— 程式碼可本機完成
- [ ] 7-2d 部署後告警鏈路驗證（Sentry 收 issue / 日誌聚合可查 / 健康檢查告警觸發）— **須實際部署**

### 7-3 效能 baseline
- [ ] 7-3a 首次互動時間（TTFB / LCP）量測
- [ ] 7-3b LLM p95 延遲量測（EDF interact / Quiz generate / Comprehension grade）
- [ ] 7-3c Runner 成功率與佇列等待時間量測（原 Judge0，2026-08-05 隨 7-R 改自建）
- [ ] 7-3d 將上述指標記入 `docs/performance-baseline.md` 作為後續優化基準

### 7-R 自建互動執行引擎（2026-08-05 定案，取代 Judge0 主路徑）
> 完整決策記錄見「已確認決策」末條；B 機規格與參數見 `docs/server-plan.md`；拓撲見 `docs/architecture.md` 執行引擎節。
- [x] R0 決策落地（2026-08-05）：推翻 Batch Terminal 決策 + server-plan / architecture / frontend / backend 規則同步 + tech-debt 記錄
- [x] R1 runner service ✅（2026-08-05）：`runner/` 9 模組 + Dockerfile（nsjail 自 source 建 + PCH 預編）+ `POST /run` + 15 tests 全綠（Dockerfile 建置與 nsjail 路徑待 R5 B 機實測）
- [x] R2 backend 抽換 ✅（2026-08-05）：`services/runner.py` dispatcher（RUNNER_URL 未設自動退 Judge0）+ 2 呼叫點換 import + 7 tests；後端 811 全綠
- [x] R3 互動層 ✅（2026-08-05）：runner `WS /terminal`（PTY + 看門狗 + session 上限）+ backend `POST /terminal/ticket`（Redis 單次 60s，沿用 execute rate limit）+ `WS /terminal/ws` 中繼 + 行為事件側錄；runner 22 / backend 818 tests 全綠
- [x] R4 前端 ✅（2026-08-05）：Output 面板終端模式（`@xterm/xterm` 動態載入避 SSR + ANSI 主題 + 排隊提示）+ 結束收合回 RunBlock + stdin 降級「進階：預先餵入」+ runner 不可用自動退批次；tsc/eslint/build 全過（A12 兩缺陷隨之消滅）
- [~] R5 B 機上線：**部署產物 + 本機 Docker 實測完成 ✅（2026-08-05）**，實機執行待使用者
  - [x] R5a 部署產物：`docker-compose.yml`（SYS_ADMIN + apparmor/seccomp unconfined + mem/pids/cpu 天花板 + tmpfs /tmp）/ `bootstrap.sh`（swap+docker+ufw+**DOCKER-USER 補洞**+禁密碼登入）/ `deploy.sh`（build→up→healthy→冒煙）/ `.env.example` / deployment.md **§E 完整 SOP**（含來源 IP 探測法、回滾、疑難排解）
  - [x] R5b 本機 Docker 實測（nsjail 真實沙箱）：修 3 個只在容器內才會爆的缺陷——① PCH 目錄未綁入 jail ② nsjail 用 execve 故編譯器需絕對路徑（`--really_quiet` 把錯誤吃掉）③ **nsjail 以 128+signal 回報，逾時被誤判 NZEC**（會讓 Coddy 給錯的主動說明）；驗過 hello/stdin/argv/編譯錯誤/逾時/SIGSEGV/`/usr` 唯讀/**PTY 互動提示字先到達**；runner 27 tests
  - [x] R5c-1 **B 機實機部署 ✅**（2026-08-06）：bootstrap 8/8 驗證通過（swap/docker/ufw/DOCKER-USER/systemd unit/SSH 禁密碼）+ 映像建置 + 容器 healthy；實機驗過 hello/stdin/argv/編譯錯誤/逾時/SIGSEGV/快取命中/401/**PTY 互動**；外部直連 8080 已阻斷（Mac 測 000）
    - 修 3 個實機才暴露的缺陷：① `iptables-persistent` 與 ufw 互斥導致 **apt 直接移除 ufw**（改 systemd unit 持久化 DOCKER-USER，purge 該套件）② 驗證函式 `cmd | grep -q` 在 `pipefail` 下收 SIGPIPE 回 141 被誤判 FAIL ③ 🔴 **`/lib64` 未掛入 jail**——amd64 動態載入器在此，execve 報 "No such file or directory"；arm64 loader 在 `/lib` 底下故本機 Apple Silicon 完全測不出來
  - [x] R5c-2 **Zeabur 設定 ✅ 生產互動終端上線**（2026-08-06 使用者驗收通過）：backend 綁公開子網域 + 三變數 + **重啟 backend**（環境變數需重啟才讀入，這是唯一卡點）；web `NEXT_PUBLIC_TERMINAL_WS_URL` + redeploy；**A 機出口 IP 實測即 `43.153.167.105`**（與推測值一致，防火牆無需調整）
  - [x] R5d UI 收斂（使用者回饋「進階：預先餵入很醜」）：stdin-panel 元件刪除 → `args-panel.tsx`（僅 argv 單行，`codeUsesArgs` 為真才渲染）+ 靜態偵測函式移至 `lib/code-detect.ts`（`usesLocalTime` 供 Coddy UTC 說明）；context 移除 orphan `getStdin/setStdin`，批次降級路徑不再送 stdin
- [ ] R6 收尾：教材健檢解除 20 支/天上限 + 額度文案清理（acceptance-checklist / CLAUDE.md）+ 30 並行壓測 + 文件同步

> **7-R6 收尾已改列 7-D4**（2026-08-06 重排：技術債統一排在功能之後、驗收之前）。

### 7-U 上線後體驗優化（2026-08-06 使用者回饋定案）
- [x] 7-U1 上下單元只在概念說明顯示（作答中跳單元非合理動線）
- [x] 7-U2 **課程全解鎖**：generator 全 available + migration `u7d8e9f0a1b2` 轉既有 locked + 前端移除 ghostUnlock 整條線路（含 DEV 設定卡）；順序改由編號/狀態圖示呈現為建議路徑
- [x] 7-U3 教材出處：LEARN 與 Coddy 皆從 UI 移除（citations 仍存 DB 與注入 prompt）+ 內文時間戳改**句尾註腳式播放標記**（`lib/transcript-timestamps.ts`；段落內去重、程式碼圍籬不動、區間取起點）
- [x] 7-U4 終端機與執行歷史 per-file（每檔 20 次、5 檔 LRU；切檔即清終端並中止進行中 session）
- [x] 7-U5 靜態補全：92 個候選（關鍵字 + 教材用得到的 STL 含繁中說明 + 骨架片段）+ 當前檔識別字掃描；Tab/Enter 接受、Esc 關閉；彈窗樣式對齊 GitHub Dark（**不接 clangd LSP**——B 機 2GB 撐不住 30 個實例）
- [x] 7-U6 Coddy 分階段狀態文字：`/chat/interact` 改 SSE（stage → done/error）+ 前端三段進度條；`chat.py` 263 行超硬上限 → 抽 `chat_sse.py`（使用者核准）

### 7-C Coddy 教學品質修復（2026-08-06 使用者對話回報 → 全面審計 → 分批修復）
> 起因：使用者實測 return 1 對話——Coddy 連續反問不升級、學生 push back 兩次才拿到正確答案。
> 審計方法：後端每個 API 欄位 ↔ 前端實際送出值、每個 service ↔ 呼叫端、規範文件 ↔ 實作，逐一比對。
> 完整缺陷清單見 tech-debt；**驗收策略（使用者裁決）：功能全部修補/新建完成後一律驗收**。
- [x] 7-C1 **P0 批次**（2026-08-06 ✅ 待實測）：
  - 接通 Hint Ladder：hint-escalation.ts 純函式（**已於 7-C2a 刪除**；同脈絡追問 +1 / 卡住訊號「不懂・沒辦法回答」跳 2 級至少 2 / 致謝歸零 / 新 session・重新執行歸零）+ `use-chat.ts` ref 追蹤送出真實 hint_level（原寫死 0）；下游自動復活＝chat hint_request 行為事件 + 策略矩陣 1-5 欄
  - Evidence 補執行狀態：`analyze_evidence` 增 `exit_code`/`status_description`，NZEC 時 prompt 改注入「執行平台狀態」（修復前會對 LLM 說「程式執行成功」而學生螢幕是 Runtime Error）
  - `_has_execution_error` 同步看 exit_code/status → NZEC 提問正確分類 DEBUGGING
  - dialogue_act 語意修正：chat 的自動升級階梯≠學生明確要提示，`classify_dialogue_act` 改傳 0 防 asking_hint 過度標記
  - 後端 827 tests 全綠（+5）；前端 tsc/eslint/build 過 + hint-escalation 11 斷言含真實對話重演
- [x] 7-C1' **七型學生模擬驗收 harness + 診斷輪修復 9 項**（2026-08-06 ✅ 兩輪模擬驗證，詳見 decisions.md）：
  `scripts/eval_coddy/`（七型學生 × 真實 LLM × debug_sink+DB 白盒探針）；診斷輪抓到並修復——
  **gpt-5.6 reasoning 預算間歇吃光輸出**（llm_params 8-05 結論錯誤；反思評分因此生產靜默失效）/
  同一執行結果重複計 BKT 負證據 / 無碼提問建立精熟度 / kgraph 鷹架被當輪雜訊污染（改先讀後寫）/
  散文洩答（strategy 層防線，殘留記 tech-debt）/ off_topic 覆寫誤標 / RAG 查詢加問句+導覽型只用問句 /
  Coddy 反要學生提供連結 / 索答詞跳級與失敗重跑歸零；後端 834 tests；⚠ `chat.py` 299 行超硬上限待拆
- [x] 7-C2a **Decision 層重構：累積式揭露階梯 + 動態選層**（方案 B）：36 格矩陣 → 6 級累積指令 + 6 條 Bloom 修飾；
      `reveal_level = min(5, base(error_type) + need)`；選層輸入搬後端 `services/chat_signals.py`
      並刪除前端／harness 兩個鏡像檔；RULE-1/2 明文定為階梯之上的不變量 + 新增 RULE-6；
      `edf/feedback.py` 越硬上限 → 拆出 `prompt_blocks.py`；實測抓到並修掉 hint_request 事件灌水
- [x] 7-C2a' **選層輸入改寫：persistence（追問次數）→ need（需求量估計）**——「堅持不等於值得」：
      理解 −1／沒理解 +1／失敗的實質嘗試 +1／顯式求助 +2／**追問與索答施壓 0**，
      歸零＝跑成功｜換卡點｜閒置 30 分；訊號由 Evidence 既有呼叫順帶輸出（零額外請求）。
      後端 869 tests ＋ P1/P3/P2 真實 LLM 實測（P3 四輪施壓 need 恆 0）；消除 tech-debt B7
- [x] 7-C2b **其餘 P1 修正**（消除 tech-debt B1／B2，B4 消化 chat 路徑）：NZEC 機械文案分三層
      （C++ 標準 / OS 慣例 / 本平台判定，第一人稱）+ PREAMBLE RULE-7/8（禁含糊帶過、認錯先講）
      + 逾時文案改互動終端 + `chat-error.ts` 分辨配額與故障；880 tests，P1 重跑實測措辭已改正
- [x] 7-C3 **2-6 Comprehension 前端 UI｜新建功能**（對應 tech-debt A1）：`lib/comprehension.ts` +
      `components/comprehension/` 7 檔（狀態機 / Modal / 三種 step / AI 鎖）；接入 Quiz result-view
      與 Learn 觀念題 tab；變體挑戰**真的鎖住 Coddy**（Provider 掛 AppShell，ChatPanel 讀鎖）；
      六端點端對端煙霧測試通過。⚠ 觸發頻率待 7-C4 用數據裁決是否加節流
- [x] 7-C2a'' **收尾**：B8 消除（`stabilize_error_type` 同證據沿用 error_type）＋
      「我卡住了」按鈕（migration `v8e9f0a1b2c3` + need +2 + 單輪漲幅上限 2）＋
      Evidence 容錯解析（欄位越界不再 502）＋ harness 可重跑（P2 反思 upsert）；
      **七型全跑通過**（P1 2→3→4→5｜P3 恆 1｜P6 三段注入全擋｜P7 診斷流完整）
- [x] 7-C4 **Coddy 品質再驗**：七型全跑通過（P1 2→3→4→5｜P3 施壓無效｜P6 注入全擋｜
      全型無含糊措辭）；**B3 裁決＝不加二次檢查、改修防線措辭**（禁的是目標概念的推理，
      不是背景知識）；**量測發現並修掉 comprehension 觸發的吸收態**（1 筆通過就永久關閉整個機制）
  - ⏳ **待使用者裁決**：修好後弱學生連答 10 題會被驗 10 次（每次 2 次 LLM 呼叫），要不要加間隔

### 7-D 技術債清償（**排在功能完成之後、使用者驗收之前**；2026-08-06 使用者定序）
> 清單正本在 `docs/tech-debt.md`，此處只排執行順序。機械事實一律跑 `python3 scripts/doc_selfcheck.py`。
- [x] 7-D1 **前端測試基礎設施** ✅ 2026-08-07：Vitest(jsdom) + `npm test` + 三支純函式測試共 **31 it**；
      順修 `cpp-completion-source.ts` 永遠不成立的 Ctrl+Space 分支（寫測試才浮現）
- [x] 7-D2 **Code Health 規則改版 + 檔案逐案處置** ✅ 2026-08-07（原「拆 7 個超硬上限檔」）：
      門檻 150/250 → 250/400、判準改「AI 檔名可預測性 + 一次讀得完」、新增舉證豁免與反向約束、
      新增 jscpd 重複偵測；工作流寫成 `.claude/skills/code-health/SKILL.md`。
      7 檔逐案判斷結果＝**1 拆分**（`generate.py` → `generate_prompts.py`）＋ **6 舉證豁免**；
      🚫 與 ⚠ 雙雙歸零。下一個機械命中項＝tech-debt C3（`_get_client` 跨 14 檔）
- [x] 7-D2b **後端 lint 首次落地** ✅ 2026-08-07：ruff 早已宣告與設定卻從未安裝（lint 零執行）；
      擴充 rule set 並校準 6900+ 筆中文全形／FastAPI `Depends` 誤判，437 findings → **0**；
      意外揭露 5-2b chat 事件記錄失效（→ tech-debt C6）
- [~] 7-D3 **文檔工作流重整**（2026-08-07 使用者擴大範圍：原「changelog 拆檔」→ 全文檔清查優化）
  - [x] 階段一 規則與標題（2026-08-07）：`changelog.md` → **`decisions.md`**（重新定位為決策記錄，
        變更明細改以 git log 為主）、`design-plan.md` → **`visual-protocol.md`**（名實對齊）、
        CLAUDE.md 去進度化（進度唯一真相＝roadmap）、文檔同步守則改為依變更類型決定、
        文件狀態標記 🔵活躍/⚪穩定/⚫凍結、高頻檔的寫法規範寫進各自檔頭
  - [x] 階段二 A **UI 文件退場**（2026-08-07）：`ui-ux-spec` / `ui-wireframes` / `visual-protocol`
        / `design-references` 共 **2891 行**刪除，有效內容（動效表／快捷鍵表／`.kbd`）收斂進
        `frontend.md`；docs 15 → 12 份。順帶抓到實作缺口 tech-debt E4/E5
  - [ ] 階段二 B **`decisions.md` 內容清理**：243 條依新規範逐條處理
        （刪 git log 已有的 Added/Changed/Tests 快照，留決策理由/否決方案/實測數據；
        估 5114 → 約 1200-1400 行）。**按月份分批 commit**，每批可獨立回溯
  - [ ] 階段二 C **⚪ 穩定文檔逐份核對**（原 7-D5 / 8-1a）：已知 `api-spec.md` 只記載
        81 個實際路由中的 40 個（**51% 缺口**：classes / code files / dashboard / dev /
        comprehension trigger）；`db-schema.md` 缺 `unit_content_staging`
  - **不拆檔**：清理後行數自然回到合理範圍，拆檔只是把不該存在的內容換地方放
- [ ] 7-D3' **文檔 ↔ 程式碼對齊**（2026-08-07 使用者指定，**待階段二全部完成後才做**）
  - 逐份確認文檔敘述與實際程式碼相符、無衝突（本次已示範方法：路由/資料表/元件機械比對）
  - **確保未來持續對齊**：檢視 `CLAUDE.md` 與 `.claude/rules/` 的規定是否夠清晰明確，
    足以讓「改程式碼時同步改文檔」成為不需要提醒的預設行為；不足處補規則或補機械檢查
- [ ] 7-D4 **7-R R6 收尾**：教材健檢解除每日上限（`verify_code_snippets.py` `DAILY_BUDGET = 20`，
      Judge0 額度限制已隨自建 runner 消失）+ 30 並行壓測驗證 server-plan 容量假設
      （原列的「hook 提示仍寫 Judge0 50 次/天」**2026-08-06 查證已不復現**，session 啟動輸出無此字樣）
- ~~7-D5 其餘文件稽核~~ → **已併入 7-D3 階段二**（同一件事，不重複列）
- [ ] 7-D6 **全站 429 / 5xx toast**（tech-debt B4 剩餘）：引入 sonner，把 quiz / learn / 教師端
      各自為政的 catch 收斂成統一攔截（chat 路徑已於 7-C2b 單獨修好）
- [ ] 7-D7 **無意義／冗餘註解清查**（2026-08-07 使用者提出，獨立一輪執行）：
      linter 做不到——判斷「這行註解有沒有講程式碼本身沒講的事」屬語意判斷。
      掛進 `code-health` skill 當一個階段；會動到大量檔案的註解，值得單獨審
- [~] 7-D8 **Claude Code / Codex 規則零漂移**（2026-08-08 使用者定案：共同 canonical source + 各自 adapter）
  - [x] A **canonical guidance + 跨平台同步器**：`.agent-source/` 成為唯一來源，能重建
        `CLAUDE.md`、`.claude/rules/*` 與根／巢狀 `AGENTS.md`；`--check` 可偵測 drift
  - [x] B **project skills 雙端分發**：`code-health` 從 canonical source 同步至
        `.claude/skills/` 與 `.agents/skills/`，兩端 validator 與 drift 測試通過
  - [x] C **Claude / Codex lifecycle adapters**（2026-08-08）：雙端 SessionStart check、source edit 後同步、禁止直改生成物皆已實機驗收
  - [x] D **GitHub CI drift check**（2026-08-08）：PR / push 必跑，`Agent config drift` 已設為 `main` required check
  - [ ] E **跨平台 bootstrap**：macOS / Windows 首次手動安裝後可重建 agent 設定（不含 credential）
- 暫不處理（已記錄且有明確重評時機）：tech-debt B5 / C3 / C5 / D1 / D2 / E1–E3

### 7-E 使用者驗收（**7-C 與 7-D 全數完成後才開始**）
- [ ] 依 `docs/acceptance-checklist.md` 0~9 段走完；目前通過：**1-1 互動終端、4-7「我卡住了」按鈕**
- [ ] **本 session 新做的 UI 一律留到這輪驗**（使用者定序）：4-8 揭露階梯 / 4-9 NZEC 三層說明 /
      4-6 三種錯誤文案 / **5-5a~g 理解驗證 Modal**（含 5-5d AI 鎖、5-5g 觸發頻率是否惱人）
- [ ] 驗收發現的問題回饋 → 小問題當輪修（「當場修小問題」守則）、大問題重新排入 7-C

---

## Phase 8 — 專案健檢與整理（2026-08-06 使用者提出）

> **執行前提**：7-C 功能完成 → 7-D 技術債清償 → 7-E 使用者驗收，全數無阻斷問題後才動手。
> 排序原則：**先談清楚方向，再做不可逆的刪除**；能自動驗證的排前面，需要人判斷的排後面。
> ⚠ **2026-08-06 重排**：8-1c/8-1d/8-3a 已前移至 **7-D**（技術債統一在驗收前清）；
> 本 Phase 只剩 8-0a 討論、8-1a 文件稽核（＝7-D5）與 8-2 專案清理。

### 8-0 討論（不寫程式）
- [ ] 8-0a **是否還有新功能要加** — **2026-08-06 使用者裁決：等驗收跑完再盤點**（驗收過程本身可能冒出新需求，先不預設）
- [x] 8-0b **專案體積討論 ✅ 已釐清**（2026-08-06 全量重測）
  - **結論：體積不是問題，1.3G 這個數字被誤解了。** 其中 1.28G（98%）是三個**可由版控中的 lock 檔完整重建**的衍生目錄：
    | 目錄 | 大小 | 內容 | 重建方式 |
    |------|------|------|----------|
    | `web/node_modules` | 666M | next 169M + @next 116M + lucide-react 38M + date-fns 38M + typescript 23M… | `npm ci`（依 `package-lock.json`） |
    | `backend/.venv` | 390M | scipy 81M + pandas 48M + sklearn 40M + llama_index 29M + numpy 24M… | `pip install -r requirements.lock` |
    | `web/.next` | 226M | `.next/dev` 155M（dev 熱重載快取）+ standalone 41M + server 21M + static 7.3M | `npm run dev` / `npm run build` |
  - **實際被版控追蹤的內容：678 個檔案、打包後 378 KB**（`git count-objects -vH`）
  - **生產映像不含這些**：`web/Dockerfile` 是 multi-stage，production 階段只 COPY `.next/standalone` + `.next/static` + `public`；`backend/Dockerfile` 在容器內依 lock 重裝。兩份 `.dockerignore` 已正確排除 `node_modules/` `.next/` `.venv/` `tests/` `.env`
  - **唯一實質可瘦身處**：`.git` 36M 中有 **3866 個 loose object 佔 35.38 MiB**，而已打包部分僅 378 KB — 成因是 `changelog.md`（單檔 356 KB）每個 commit 存一份完整壓縮副本 × 295 commits。`git gc` 可 delta 壓縮，零風險
  - **副產物發現**：scipy/pandas/sklearn 169M 未在任何依賴宣告中（見 tech-debt「本機 `.venv` 與宣告的依賴脫鉤」）
- [x] 8-0c **工作流檢討 ✅ 已定案**（2026-08-06）
  - **量測**：最近 60 commits — 程式碼 +15512/-1994 行，文件 +1719/-300 行。**文件僅佔約一成churn，「文件同步拖慢開發」不成立**
  - **真正的成本是準確度而非份量**：文件中的機械事實（行數 / 測試數 / 檔案是否存在 / 是否全綠）全靠手寫敘述，沒有任何機制會在它失真時報錯。已抓到兩個實例 ——
    ① tech-debt 2026-08-06 寫「無任何檔案超過硬上限」，實際有 4 個檔案超過 250
    ② `CLAUDE.md` 自訂「目標 ≤ 60 行」，實際 89 行（當前狀態一段就佔 48 行）
  - **裁決**：工作流本身（單一 session 多批 + 每批 commit/push）運作良好**不改**；改為導入 **8-1d 自檢 script（手動跑，不掛 pre-commit）**
  - **同場處理**：`CLAUDE.md` 已依裁決瘦身 89 → 64 行（當前狀態只留現在進行式；`push 即自動部署` / OAuth 100 人上限兩條唯一紀錄先遷入 `deployment.md` Step 6 才刪）

### 8-1 文件一致性全面稽核
> 2026-08-06 已先修三份（roadmap / 驗收清單 / tech-debt），其餘尚未逐字核對。
- ~~8-1a 逐份核對 `docs/`~~ → **已併入 7-D3 階段二**
- [x] 8-1b ~~修正 `CLAUDE.md` 文件索引的過時描述~~ — 2026-08-06 已隨 8-0c 瘦身處理完（文件索引兩處描述先前已修；同時修 `技術棧` 仍寫 Judge0 / GPT-4o → 改自建 runner + gpt-5.6）
- [ ] 8-1c `changelog.md` 4500+ 行 → 拆 `changelog-archive.md`（2026-07 以前）→ **已前移為 7-D3**
- [x] 8-1d **文件自檢 script ✅ 完成**（2026-08-06）：`scripts/doc_selfcheck.py`（手動跑，不掛 pre-commit）
  - 掃三件機械可判定的事：① 超門檻檔案（⚠150 / 🚫250，排除 tests）② 文件中 backtick 標注的路徑是否存在
    ③ 後端 / runner 測試函式數；輸出即可貼進文件的 markdown，杜絕手抄
  - **歷史日誌（changelog / roadmap-archive）不掃路徑**——它們如實記錄當時的檔案，事後刪除是正常的
  - **首跑即抓到 4 處真實漂移並當場修正**（見 tech-debt 已消除節）
  - **執行時機**：session 結束前 AI 自行跑一次，結果併入該次文件同步

### 8-2 專案清理（2026-08-06 依 8-0b 量測結果縮減範圍）
- [x] 8-2a ~~清除 `.DS_Store` / `.pytest_cache` / `.next` 快取，確認 `.gitignore` 涵蓋完整~~
  — **已查證無事可做**：8 個 `.DS_Store`、3 個 `.pytest_cache`、`web/.next`、`backend/.venv`、`web/node_modules`、`ScreenShot/`
  **全部已被 `.gitignore` 涵蓋**（`git check-ignore` 逐項驗證），不影響版控也不進映像。刪與不刪只差本機磁碟
- [ ] 8-2b `git gc` 壓縮 loose objects（3866 個 / 35.38 MiB → 預期剩數 MB；**8-0b 認定的唯一實質可瘦身處**）
- [ ] 8-2c 盤點死程式碼與孤兒檔案（提出清單由使用者裁決，**不自行刪除**）；已知納入：`.venv` 未宣告的 scipy/pandas/sklearn、`docker-compose.judge0.yml`（Judge0 自架方案已作廢僅供追溯）
- [ ] 8-2d `ScreenShot/` 676K 未進版控——確認用途，決定保留或移除

### 8-3 前端測試基礎設施（tech-debt C1）
- [ ] 8-3a Vitest 建置 + 純函式測試固化 → **已前移為 7-D1**（`hint-escalation` 已於 7-C2a 刪除，不在清單內）
- [ ] 8-3b 視情況再評估 React 元件測試與 Playwright

---

## 已確認決策

- ~~Terminal：Batch 模式，不需即時互動式 terminal~~ → **2026-08-05 推翻**：批次模式無法提供本地編譯器體驗（`cin` 必須預先填完、按 Run 不等輸入），且 RapidAPI 50 次/天不敷課堂使用 → 改自建互動 runner（見 7-R 與末條決策）
- 介面語言：繁體中文為主，暫不做多語系
- UI：GitHub Dark + VS Code 風格，純 Dark Mode
- ~~Judge0：開發期 RapidAPI (免費 50 次/天) → 上線後自架~~ → **2026-08-05 改自建 runner**：自架 Judge0 需 GRUB 切 cgroup v1（淘汰中機制）+ privileged，且仍是批次判題；Judge0 降為 fallback（`RUNNER_BACKEND` 切換回 RapidAPI）
- 部署：Zeabur (Tencent Tokyo VPS) | 使用者規模：初期 < 100 人
- 即時通訊：Phase 1 用 REST + SSE (chat streaming)，未來視需求加 WebSocket
- 介面借鑑：6 份來源僅貢獻結構模式，視覺基本元素統一為 GitHub Dark（`frontend.md` R1–R8）
- **OSS 重用**：開發前必查 `docs/references.md` §1 決策矩陣；禁止 AGPL/GPL 套件；禁止移植已有對應套件的演算法（如 BKT 必用 pyBKT）
- **執行順序**：功能優先（Phase 2 → 3）→ 部署準備（Phase 4）→ **Phase 5 教師端 ⇄ Phase 6 教學內容建構（可平行）** → 上線實測（Phase 7）；所有需要實際部署才能驗證的工作集中在 Phase 7
- **Phase 6 採 NotebookLM grounded 模式**（2026-05-07 確認）：所有 LLM 生成的 unit content / 練習題必須 grounded 在教授實際 YT 影片字幕上，禁止 LLM 自由發揮；source 採 Whisper API（B1 方案，6-1e 已完成 62 部 transcribe），品質不夠的 unit 在 6-4 抽查時局部重跑
- **Concept 範圍 62 個**（2026-05-07 確認 / 2026-05-22 修訂）：video_order 1-62 全部 seed 為 concept 且**全部進學習路徑**；1-3 仍保留 `category="課程介紹"` 供知識圖譜 styling 區分使用
- ~~知識圖譜重構為 Phase 6 後續工作（2026-05-07）~~ → **已於 2026-07-04 K1a 完成**：線性鏈已替換為 curated 多對多依賴 DAG（90 條邊，AI curated + 實機驗證，教授人工標註已隨教授抽查一併移除）
- **Phase 6-K 自適應學習引擎**（2026-07-04 功能規格書確認）：五大功能執行順序 K1→K2→K3→K4→K5（依技術相依性：資料基礎 → 狀態 → 診斷 → Coddy 整合 → 視覺）；原 6-5/6-6 整併入 K 系列；視覺化套件預設維持 Cytoscape.js（K5a 調研驗證此預設）
- **K6 熟練度演算法 v2**（2026-07-06 確認）：訊號分級（quiz 強證據 / chat 弱證據，以 BKT slip/guess/learn 參數表達，不外掛權重係數）+ 遺忘曲線惰性衰減（floor 下限、半衰期隨練習次數成長）；透明化採「事件級解釋，不給逐筆帳本」、衰減 framing 為複習提示；**關鍵技術文獻標注於 references.md §5.1 供論文引用**
- **作業指派＝TronClass 式文件繳交**（2026-07-07 確認）：非題庫 quiz——教師建作業（標題+內容+附件）指派整班 → 學生繳交（文字+附件）→ 教師人工評分+評語；檔案存 Postgres bytea（單檔 ≤ 10MB + 型別白名單）；學生雙入口（作業 tab + Dashboard 卡片）；原 5-5b 熱力圖/錯誤統計改隸 5-4
- **題庫策略**（2026-07-06 確認）：不採 NotebookLM（無公開 API、輸出無法對齊題目 schema 與 citation）；成本控制走「批次 grounded 生成 + 題庫優先」；即時生成題目 validated=True 後永久入庫持續擴充題庫（現行機制確認保留）；QUIZ tab 弱項出題改題庫優先列 U2d
- **LEARN 摘要移除**（2026-07-06 確認）：摘要 tab 直接移除（U2b）；依據＝提供現成摘要的被動學習效益低（Fiorella & Mayer 2015 生成式學習）+ 冗餘效應增加外在認知負荷
- **反思計畫粒度**（2026-07-06 確認）：現行即為「每題一份」（Quiz 與 Learn 練習皆以 `sourceType="quiz"` + question id 建立），符合預期不需改；Workspace 顯示 gating 問題列 U1c
- **自建互動執行引擎（2026-08-05 定案，7-R）**：nsjail 沙箱（Google 維護，不自造輪子）+ PTY（stdout 行緩衝，提示字即時出現——修掉 V1 pipe 緩衝缺陷）+ WebSocket；拓撲＝Browser `wss` → A 機 backend（綁公開子網域；Next.js Route Handler 不支援 WS proxy）中繼 → B 機 runner；**一律互動終端**（`POST /run` 批次僅供題庫驗證 / 教材健檢 / 實作題判定）；Judge0 降為 fallback（`RUNNER_BACKEND`）；`ExecutionResult` 欄位不變 → EDF / analytics / run_help 零改動；B 機另租不動 PokerNote（總 $12/月）；「僅放行 A 機」防火牆規則**保留並加 `X-Runner-Token` 縱深**（B 機不持有任何 credential）；已知兩缺陷（stdin 提示不即時 / Run 不攔截）不修、由 R4 取代；UI＝終端機嵌入 Output 面板（非 V1 modal）+ ANSI 16 色例外（僅終端畫布，frontend.md 白名單）
- **LLM 模型選型 v2**（2026-07-06 確認）：放棄單一 GPT-4o，改任務導向路由（詳見 6-M 節選型表）；cascade 設計 = `gpt-5-mini` 生成 + `gpt-5.4` 審查；Unit content 批次用 `gpt-5.4`（教科書品質優先）；對話/分析組 `gpt-5.4-mini` 起步、K4d 實測後定案；文獻依據 FrugalGPT / RouteLLM（references.md §5.1）；論文記錄實驗當下確切模型版本
- ~~**實作執行順序**（2026-07-06 定案，共 10 批）~~ → **已全數執行完畢，保留供追溯**。2026-08-06 起的順序改為：驗收清單 1–8 段 → Phase 8 健檢整理（8-0 討論先行）→ 7-2 監控 → 7-3 效能 baseline → 5-3/5-4 行為分析（等真實資料）。原文：① U1a/b/c bug 修正 → ② U2b 移除摘要 + U2c 拔 1-3 範例 → ③ knowledge-graph.tsx 拆分（已核可）+ K6a/b/c → ④ U2d 題庫優先 + U2a QUIZ 美化 + 練習題重複曝光 → ⑤ 6-M1 模型分組 + 6-3a-3/6-4a 實機批次 + deferred-ui + K4d 調參（需 OpenAI 儲值 $10；key 已在 backend/.env） → ⑥ ~~U2f 範例程式~~ **改 U2g tab 重構+移除範例** → ⑥' 6-3c 知識點驅動題庫 → ⑦ 教師端 5-1 → 5-2 → DEV-E → 5-5 → ⑧ U2e Workspace 存檔 + 7-2a/b/c 監控程式碼 → ⑨ Phase 7 部署實測 → ⑩ 5-3/5-4 行為分析（待真實資料）；真人驗收（K1d/K5d/K4d 語氣）改使用者 session 後自測（2026-07-06 晚間修訂：U2f 作廢、新增 U2g/6-3c、簡答題型不做）
- **Decision 層重構：累積式階梯 + 動態選層**（2026-08-06 設計討論定案，**方案 B**；實作見 7-C2a）
  - **問題**：Hint Ladder 借自 OATutor，那裡 L0 的語意是「學生按了提示鈕但還沒給提示」。搬到 chat 後，
    **L0 實際變成「學生開口的第一句話」**——可能是提問、求審閱、查教材。一律回「請你用自己的話解釋
    這段程式碼」是把「該給多少幫助」與「該做什麼對話動作」混成一軸（類別錯誤，非單純措辭問題）。
    佐證：Quiz 自己的階梯 `services/quiz/hint.py` 是 **1–5 沒有 0**——因為在 Quiz 裡「沒求助」不需要編號
  - **決策一：六層改累積式**，單調維度＝「本題解法被揭露多少」而非「講了多少話」。
    L0 重新定義為「回答學生實際問的問題 + 解釋概念 + 本題解法揭露 0%」
  - **決策二：動態選層** `reveal_level = min(5, base(error_type) + persistence)`——
    需求決定起點（無錯誤 L0 / syntax·compilation·runtime L2 / logic·semantic L1），堅持程度往上加
  - **決策三：採方案 B**（6 等級指令 + 6 Bloom 修飾＝12 條，取代 36 格矩陣）。
    理由：累積語意在「36 格互相獨立的字串」裡表達不出來；且 2026-08-06 已被「手寫的東西沒有機制驗證」
    咬過三次（tech-debt 檔案數 / llm_params 結論 / hint_level 寫死），不再新增手寫格子
  - **決策四：persistence 計算搬後端**，刪除 hint-escalation.ts 與其人工鏡像 eval_coddy/ladder.py；
    chat 不再由前端傳 `hint_level`（Quiz 的同名欄位語意不同，維持原樣）
  - **洩答的重新界定**（修正 2026-08-06 早先的判斷）：閏年題屬章節 25「if-else」，**學習目標是 if-else
    與模數，「閏年怎麼定義」只是背景設定**——講出規則其實移除了與目標無關的認知負荷，是對的教法。
    真正不該給的是程式碼結構，而那條線 RULE-1/2 本來就守得住。**例外**：若學生問的正是本題的目標概念
    （如演算法題要學生自己想出判斷法），則改為引導而非直述
  - **RULE-1 vs L5 矛盾的解法**：不是新裁決，是**移除離群值**——`quiz/hint.py` 早已寫明
    「不可直接給完整答案」，`validate_output` 也一直照此執行（>8 行無 TODO 即截斷），
    **只有 `decision.py` 的 L5 措辭在說謊**。原則明文化：
    **RULE-1／RULE-2 是階梯之上的不變量，任何等級都不得突破；L5 的「完整」指解釋完整、非程式碼完整**。
    依據＝`modules.md` 引用的 CodeAid 研究（不給直接程式碼的 AI 學習效果更好）是整個設計的證據基礎
