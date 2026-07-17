# 技術債追蹤

> 記錄已知的技術債項目，每次消除後標記 ✅ 並註明日期。

## ⚠ 待處理

### 延遲驗收（Phase 6-2 → 6-4 必跑）
- [ ] **6-2 grounded UI 狀態尚未真機驗收** → **6-4a-deferred-ui 必驗（roadmap 已標）**
  - **背景**：6-2c / 6-2d / 6-2e 完成時 DB 內無任何 promoted `concept_explanation` / `code_examples` / `summary` object，使用者只能驗 fallback / placeholder 狀態。grounded 主路徑必須等 6-2b 實機批次（延至 6-4 合併執行）跑完才驗得到
  - **必驗項目**（任一 promoted unit 即可作 sample）：
    - 6-2c：grounded markdown render + 點 citation 真的呼叫 `player.seekTo`
    - 6-2d：卡片列表（title/code/explanation/citation）+ 「在 Workspace 開啟」→ CodeEditor `initialValue` 載入 + 一次性消費（重整不再覆蓋）
    - ~~6-2e：摘要 tab 三狀態切換~~ → **已作廢（2026-07-06 U2b 決策：LEARN 摘要 tab 直接移除）**
    - 6-3b：ExercisesTab 命中題庫 path（前端 Loading 顯示「查找題庫題目」< 1 秒、不打 LLM、直接顯示題目）— 當前只能驗 fallback 「AI 正在生成」path
  - **如何處理**：批次跑完拿到至少 1 個 promoted unit 後，依 changelog 2026-05-22 6-2d 條目「How to verify」步驟 1-4 逐項操作；其中第 3-4 步是 sessionStorage 一次性消費的關鍵驗收，**不可漏跑**
  - **若驗收失敗**：第一優先檢查 `web/lib/pending-workspace-code.ts` 的 `consumePendingWorkspaceCode()` 是否真的有 `removeItem`；其次檢查 `web/app/(app)/workspace/page.tsx` 是否用 `useState` lazy initializer（而非直接呼叫，會導致 re-render 多次 consume）

### 部署相關（待實測）
- [ ] **Zeabur PREBUILT + source.type=IMAGE schema 未實測**
  - 4-1b 將 `zeabur.json` 的 postgres 從 marketplace `postgresql`（不含 pgvector）改為 `template: PREBUILT` + `source: {type: "IMAGE", image: "pgvector/pgvector:pg16"}`
  - 此 schema 細節依 Zeabur template.json 規範撰寫，但**未經實際部署驗證**
  - **如何處理**：4-2 實際 Zeabur 部署時若 schema 被拒，依 deployment.md §A 的 fallback 改用 marketplace pgvector 或 GIT + 一行 Dockerfile
- [ ] **Judge0 自架 docker-compose 未在生產驗證**
  - 4-1c 新增 `docker-compose.judge0.yml` + `judge0.conf.example`，僅在規格層面撰寫
  - **限制**：Zeabur 等雲平台禁用 `privileged: true` → 自架 Judge0 只能在自己的 VPS 跑
  - **如何處理**：self-host VPS 部署時實測 stack 啟動 → workers 成功 register languages → backend 能透過 `/about` 與 `/submissions` 對話；若 worker fail 多半是 cgroups / privileged 問題

### 內容層（教學課綱）
- 🔄 **YT video metadata 未補**（已從 59 → 62 個影片 concept；2026-05-07 教授交付 playlist URL，fetcher script 已產 59 列 CSV，待擴充至 62 列）→ **正式追蹤於 roadmap Phase 6-1**
  - **影響**：3-1d 學習單元頁的概念說明 tab 無法 embed YT player；只能顯示影片標題與「待補」placeholder
  - **進度**：6-1a/b 已完成；6-1b+/c/d/e/f 進行中
  - **如何處理**：fetcher 已寫好（`backend/scripts/fetch_playlist_metadata.py`）；接下來擴充 EXPECTED 1-62、加 video 1-3 migration、PATCH script 寫入 DB、字幕 RAG ingest
  - **格式**：CSV，欄位 `video_order, youtube_id, duration_seconds, title_zh`，已產出於 `data/teaching_content/videos.csv`
- [ ] **題庫 coding 題 validate 通過率偏低 + v17/v41 掛零**（2026-07-06 實機批次觀察）
  - **現況**：首輪 17 個失敗中 13 個為 coding 題 `VALIDATION_RETRY_EXHAUSTED`（cascade gpt-5-mini 生成 + gpt-5.4 審查）；補跑後仍有 v17 cpp-17-incr-decr / v41 cpp-41-extern-vars 兩輪全滅（0 題）、v11/v53/v61 各缺 1 題
  - **影響**：該 5 個 concept 的 Learn 練習 tab / Quiz 題庫覆蓋不足，fallback 現生（可用但較慢）
  - **如何處理**：6-4b 檢視 validate 失敗 reason 分佈，調整 coding 題 generate prompt（如 expected_output 格式規則）後對缺題 concept 局部重跑

### Learn 頁面視覺化升級
- [ ] **3-1c 卡片版 ≠ ui-wireframes.md 期望的「節點+箭頭」graph 版** → **併入 roadmap K5 一併評估（2026-07-04）**
  - **影響**：與知識圖譜頁 (`/knowledge`) 風格不統一；無法直觀顯示 PREREQUISITE 依賴的分支（K1a 後已是多對多 DAG，分支資訊更豐富）
  - **如何處理**：K5 視覺改版時評估復用 knowledge 頁 Cytoscape 元件

### AST 程式碼分析信號（K2c 決策記錄，2026-07-04）
- [ ] **真 AST（tree-sitter / libclang）暫不引入** — 現以 LLM Evidence 為程式碼分析信號
  - **理由**：LLM 已輸出 concept_tags + error_type + bloom（等效 AST→概念對映產物）；自建 AST 特徵規則工程成本高且功能重複
  - **重評時機**：Phase 5 行為資料可檢驗 LLM tagging 可靠度後；若誤標率高再走 references.md §1 決策矩陣評估 tree-sitter

### 程式碼層（2026-07-04 健壯性審查新增）
- [ ] **OpenAI client lazy-singleton 邏輯重複於 9 個服務模組**（evidence / feedback / quiz×4 / reflection / comprehension×2 / learning）
  - **刻意延後**：各模組測試都對自己模組的 `_client` / `_get_client` 做 monkeypatch，抽共用 `core/llm.py` 需連動改 9 檔 + 大量測試，風險與收益不成比例
  - **如何處理**：待某次需要統一調整 LLM client 行為（如加 retry / timeout 參數）時一併抽取
- [ ] **429 冷卻倒數 toast UI 未實作**（frontend.md 規範有、無 toast 基礎設施）
  - **現況**：6-R3 後端 429 訊息已帶「請於 N 秒後再試」，經 `ApiRequestError.message` 透傳給各頁面既有錯誤顯示，功能可用但非 toast 形式
  - **如何處理**：待引入 shadcn/ui toast（sonner）後在 `web/lib/api.ts` 統一攔截 429 發 toast
- [ ] **backend.md「OpenAI 失敗 → 快取最近回應」降級策略未實作**
  - **現況**：6-R6 已保證 LLM 失敗時學生輸入不丟失（user message 先 commit），前端可重試；降級快取為進一步優化
  - **如何處理**：Redis 存 per-user 最近一次成功回應，LLM 5xx 時回傳並標註 fallback

## ✅ 已消除

- ~~judge0.py 不支援自架 authn header~~ — 2026-07-18 `_build_headers` 加 authn 分支（URL 自動判斷 + 可選 `JUDGE0_AUTH_MODE` 顯式覆蓋；自架帶 `X-Auth-Token`）+ 4 tests；生產實測待 Phase 7
- ~~lazy-seed 新使用者的 unit content 仍是空骨架~~ — 2026-07-18 `generate_learning_path` seed 時讀 staging（approved）帶入 content，與 promote 整包覆蓋行為對齊 + 2 tests
- ~~`backend/pyproject.toml` 沒設 hatchling packages~~ — 2026-07-18 補 `[tool.hatch.build.targets.wheel] packages`（flat layout 顯式列出）；隔離環境驗證 wheel target 可解析
- ~~git user.name / user.email 未設定~~ — 2026-07-18 確認已設定（曾冠豪 / abbyabby41@gmail.com）
- ~~backend/uv.lock 未追蹤副產品~~ — 2026-07-18 加入 .gitignore；依賴鎖定正本維持 requirements.lock（Dockerfile 使用），避免雙鎖定檔 drift

- ~~練習題重複曝光~~ — 2026-07-06 **U2d 一併消除**：bank service 加 `exclude_answered_by`（server-side join student_answers），Learn/Quiz 兩入口同時生效；全答過 → 404 → fallback 現生新題入庫
- ~~`knowledge-graph.tsx` 265 行超標~~ — 2026-07-06 拆出 `use-graph-nav.ts` hook（章節游標 + 鏡頭動作）；主元件 212 行 + hook 119 行
- ~~unit content 生成管線的 `summary` 欄位閒置~~ — 2026-07-06 **U2b 完成**：Summary model / prompt / LLM call 全移除（非僅前端 tab），批次直接省 1/3 calls
- ~~`backend/.env` 的 `OPENAI_API_KEY` 未填~~ — 2026-07-06 確認已填（只驗證存在性未讀值）；第 5 批實機批次前使用者需確認 OpenAI 帳戶儲值 $10
- ~~`concept_edges` seed 的 23 條邊為 AI 暫定值~~ — 2026-05-05 完全替換為 58 條線性 PREREQUISITE（隨 e1f2a3b4c5d6 重 seed）
- ~~`concepts` seed 的 `category` / `difficulty_level` / `name_zh` 為暫定值~~ — 2026-05-05 完全替換為 59 影片 concept
- ~~`backend/requirements.lock` 過時~~ — 2026-05-05（4-1a）以 `uv pip compile` 重產（38 → 272 行含 transitive）；pyBKT 確認未實際 import，無需安裝
- ~~跨章節 PREREQUISITE 邊未標~~ — 2026-07-04 **K1a 完成**：migration `i5d6e7f8a9b0` curated 依賴 map 取代線性鏈 → 90 條多對多邊；實機驗證 0 孤兒節點 / 0 反向邊
- ~~EDF chat ConceptTag 不寫入 BKT mastery~~ — 2026-07-04 **K2a 完成**：`edf_parent_tag` mapping + 三層 fan-out，Workspace 對話重新驅動 BKT 且不淹沒 quiz 精準信號
