# Roadmap

> **執行策略**：功能優先（Phase 2 → 3）→ 部署準備程式碼（Phase 4）→ **Phase 5 教師端 / Phase 6 教學內容建構（兩者可平行或先後，依教授資料準備進度而定）** → 上線實測（Phase 7）。
> **核心原則**：需要實際 Zeabur / VPS 部署才能驗證的工作（Golden path / 監控 / 效能 baseline）集中在 Phase 7。本機可完成的程式碼準備全部排在 Phase 7 之前。
> **OSS 重用**：開發前必查 `docs/references.md` §1 決策矩陣（CLAUDE.md 守則 #7）。
> **完成細節**：已完成 sub-task 細節已歸檔至 `docs/roadmap-archive.md`（按 phase 結構） / `docs/changelog.md`（按時間）。本檔只保留「現在要做什麼」+「未來地圖」+「已確認決策」。

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
> **資料策略**：5-1 / 5-2 / 5-5 純檔案，本機 dev 即可開發 + 測試；5-3 / 5-4 演算法可先用合成資料寫 + 單元測試，等 Phase 7 部署後用真實資料調校。

### 5-1 班級管理
- [ ] 5-1a classes + class_members 表 migration
- [ ] 5-1b 班級 CRUD API（建立/邀請碼/加入/移除）
- [ ] 5-1c 教師 Dashboard 頁面骨架 + 班級管理 UI

### 5-2 行為資料收集（Module 9）
> **OSS**：✅ Tier 2 採用 ProgSnap2 EventType schema + StudyChat dialogue act 分類 schema
- [ ] 5-2a coding_events 表 migration（**採用 ProgSnap2 五欄主鍵 + EventType 列舉**）
- [ ] 5-2b 後端 event logging service（從 Judge0 + EDF 現有流程擷取資料）
- [ ] 5-2c chat_messages 擴充 dialogue_act 欄位（**採用 StudyChat schema**：asking_hint/clarification_request/debugging/off_topic/acknowledgment/verification）
- [ ] 5-2d 行為指標聚合 service（編譯頻率/成功率/修復時間/hint 分布等）

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

### 5-5 作業指派
- [ ] 5-5a 作業指派功能（選題 + 指定學生/班級）
- [ ] 5-5b 學生進度查看（精熟度熱力圖 + 常見錯誤統計）

---

## Phase 6：教學內容建構（NotebookLM grounded 模式 — 內容必須來自實際影片）🎯 進行中
> 62 個學習單元的 4 個 tab 全部有實質內容、且 LLM 生成內容**完全 grounded 在教授實際影片字幕上**；`learning_units.content` 不再是空骨架。
> **核心架構（NotebookLM 模式）**：YT 字幕 → LlamaIndex IngestionPipeline 入庫 → 生成時 retrieve 該 video 字幕 chunks 注入 prompt → LLM 生成必須引用 timestamp citation、不引入字幕未出現的概念 → 教授抽查時可比對「LLM 生成 vs 影片實際 timestamp 處內容」。
> **資料流**：YT playlist URL → fetcher 抓 metadata + 字幕 → PATCH 寫入 concepts metadata + RAG ingest 字幕 → LLM grounded 生成 unit content → 教授抽查 → 修正 prompt 重跑（如需）。
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
  - [ ] 6-3a-3 實機 LLM 全跑（延至 6-4 合併執行；預估 62 concept × 2 題 × 2 LLM call ≈ 250-500k token / $5-15 USD）
- [x] 6-3b ExercisesTab 改造：從「按需現生」→「優先讀題庫，題庫不足才現生」(GET /quiz/from-bank + ApiRequestError 404 QUESTION_BANK_EMPTY fallback；6 bank service tests + 5 route integration tests；前端 Loading 文案分「查找題庫題目 (< 1 秒)」/「AI 正在生成 (5-15 秒)」兩階段)

### 6-4 內容品管
- [ ] 6-4a 教授抽查 5-10 個 unit 全部 4 tab 品質：核心檢查「LLM 生成內容是否真的反映該 video timestamp 處的教法」（可直接點 citation 跳到影片時間點對照）；不脫離 C++ 教學情境；程式碼可編譯；**6-2b 的 59 部實機批次跑在此階段合併執行**
- [ ] **6-4a-deferred-ui 必驗（grounded 資料就緒後立即跑，不可跳過）**：批次跑完取得至少 1 個 promoted unit 後，重新驗收以下「6-2 系列因無資料而延後驗收」的 UI 狀態
  - **6-2c grounded path**：概念說明 tab 的 grounded markdown 渲染 + 內嵌 citation 點擊跳轉是否真的 `player.seekTo`（之前只驗了 pending fallback path）
  - **6-2d grounded path（含卡片 + Workspace 轉場）**：範例 tab 卡片列表（title / code / explanation / citation 標籤）+ 「在 Workspace 開啟」按鈕 → Workspace `<CodeEditor initialValue>` 是否載入範例程式碼 + 重整 / 再 navigate 後不重複覆蓋（一次性消費）
  - **6-2e grounded path**：摘要 tab 的 grounded 三狀態渲染 — (a) `summary.needs_more_source=true` notice + reason；(b) `summary.key_points` bullet list + `summary.citations` 時間戳/節錄標籤；(c) 同概念 tab 的 `parseTimestampStart` 跳轉行為**不**在摘要 tab 重做（UI 提示使用者回概念 tab 點 citation）— 驗收僅需確認三狀態正確切換、不需驗 seekTo
- [ ] 6-4b 依抽查反饋調整 6-2a prompt template 並針對問題 unit 局部重跑；對品質太差的 unit 評估升級到 Whisper 重 transcribe（B 方案）作為 source

### 6-5 Coddy（EDF Chat）對話品質優化（2026-06-23 使用者反饋新增）
> 背景：使用者實測 Workspace AI 對話後反饋 Coddy 目前不太討學生喜歡——反問問題語氣生硬、不自然；且 RAG 是否檢索影片內容目前綁在 `hint_level >= 2` 門檻（見 `services/edf/decision.py` `use_rag` 判斷），而非「這個問題是否真的需要/提到影片內容」，導致該查影片時沒查、語氣也不夠自然。
- [ ] 6-5a RAG 觸發條件改為「內容相關性」而非 hint_level 門檻：評估方案（如先 retrieve 再用相似度分數判斷是否要注入，取代現有 `clamped_hint >= 2 and bloom >= ANALYZE` 寫死規則）
- [ ] 6-5b Persona / 語氣優化：重新檢視 `services/edf/feedback.py` 的 persona/preamble 文字，改善反問語氣的自然度，降低「為了套用策略矩陣而硬問」的生硬感
- [ ] 6-5c 真人測試驗收：抽幾輪實際對話比對改動前後語氣與 RAG 命中率差異

---

## Phase 7：上線實測（須實際部署到 Zeabur / VPS）
> Golden path 跑通、監控告警接通、效能 baseline 記錄；可對外開放給真實學生使用。
> **前置條件**：Phase 4 配置層完成；Phase 6 至少 6-1 + 6-2b 完成（含字幕 RAG ingest + grounded LLM 生成 unit content）；Zeabur 帳號 + VPS（Judge0 self-host）就緒。
> ⚠ 上次卡關於 API 串接（前後端 proxy / NextAuth callback URL / CORS / Judge0 endpoint），重啟前先排查 `web/app/api/*` proxy 設定、`backend/app/core/config.py` 環境變數、Zeabur dashboard service 連線狀態。

### 7-1 Golden path 整合驗證
- [ ] 7-1a 部署到 Zeabur（web + backend + pgvector + redis）+ Judge0 self-host VPS
- [ ] 7-1b Golden path 跑通：登入 → 寫碼 → 執行 → AI 對話 → RAG 檢索 → 出題作答
- [ ] 7-1c 教師端帳號 / 班級 / 行為資料端到端驗證（Phase 5 程式碼以真實流量驗收）

### 7-2 監控與告警
> Sentry / 結構化日誌 / 健康檢查端點的**程式碼**可在本機預先寫好，但接通告警鏈路、Log aggregation、Sentry 收 issue 都需實際部署。
- [ ] 7-2a Sentry SDK 整合（前後端 init + DSN 環境變數 + 異常捕捉）— 程式碼可本機完成
- [ ] 7-2b 結構化日誌（structlog / loguru + request_id middleware）— 程式碼可本機完成
- [ ] 7-2c 健康檢查端點分離（/health/live + /health/ready）— 程式碼可本機完成
- [ ] 7-2d 部署後告警鏈路驗證（Sentry 收 issue / 日誌聚合可查 / 健康檢查告警觸發）— **須實際部署**

### 7-3 效能 baseline
- [ ] 7-3a 首次互動時間（TTFB / LCP）量測
- [ ] 7-3b LLM p95 延遲量測（EDF interact / Quiz generate / Comprehension grade）
- [ ] 7-3c Judge0 成功率與佇列等待時間量測
- [ ] 7-3d 將上述指標記入 `docs/performance-baseline.md` 作為後續優化基準

---

## 已確認決策

- Terminal：Batch 模式，不需即時互動式 terminal
- 介面語言：繁體中文為主，暫不做多語系
- UI：GitHub Dark + VS Code 風格，純 Dark Mode
- Judge0：開發期 RapidAPI (免費 50 次/天) → 上線後自架
- 部署：Zeabur (Tencent Tokyo VPS) | 使用者規模：初期 < 100 人
- 即時通訊：Phase 1 用 REST + SSE (chat streaming)，未來視需求加 WebSocket
- 介面借鑑：6 份來源僅貢獻結構模式，視覺基本元素統一為 GitHub Dark（design-plan.md §0.3 七條硬規則）
- **OSS 重用**：開發前必查 `docs/references.md` §1 決策矩陣；禁止 AGPL/GPL 套件；禁止移植已有對應套件的演算法（如 BKT 必用 pyBKT）
- **執行順序**：功能優先（Phase 2 → 3）→ 部署準備（Phase 4）→ **Phase 5 教師端 ⇄ Phase 6 教學內容建構（可平行）** → 上線實測（Phase 7）；所有需要實際部署才能驗證的工作集中在 Phase 7
- **Phase 6 採 NotebookLM grounded 模式**（2026-05-07 確認）：所有 LLM 生成的 unit content / 練習題必須 grounded 在教授實際 YT 影片字幕上，禁止 LLM 自由發揮；source 採 Whisper API（B1 方案，6-1e 已完成 62 部 transcribe），品質不夠的 unit 在 6-4 抽查時局部重跑
- **Concept 範圍 62 個**（2026-05-07 確認 / 2026-05-22 修訂）：video_order 1-62 全部 seed 為 concept 且**全部進學習路徑**（PREREQUISITE 鏈 1→2→3→…→62）；1-3 仍保留 `category="課程介紹"` 供未來知識圖譜 styling 區分使用
- **知識圖譜重構為 Phase 6 後續工作**（2026-05-07 確認）：目前線性 04→05→...→62 的 PREREQUISITE 鏈為 MVP；Phase 6 完成後依教授標的跨章依賴重構為多對多圖（記入 tech-debt 追蹤）
