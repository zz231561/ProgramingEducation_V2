# 技術債追蹤

> 記錄已知的技術債項目，每次消除後標記 ✅ 並註明日期。

## ⚠ 待處理

### 前端檔案大小
- [ ] **`web/components/knowledge/knowledge-graph.tsx` 265 行（>250 硬性門檻）**（2026-07-05 K5 語意縮放改版產生）
  - **背景**：主元件同時負責 Cytoscape 生命週期、章節導覽游標、鏡頭動作（fitChapter / handleNav / zoomToCategory / handleOverview）
  - **如何處理**：抽 `use-graph-nav.ts` hook（章節游標 + 鏡頭動作，約 -80 行）；已提出待使用者核可後執行

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
- [ ] **練習題重複曝光**（6-3b 已標）→ Phase 6 後段 / Phase 7 前
  - **背景**：`/quiz/from-bank` service 已支援 `exclude_question_ids` 但前端 ExercisesTab 未維護已答題清單，學生重複進同 unit 練習可能抽到同題
  - **如何處理**：前端在 `useEffect` 用 `getQuizHistory` 取出該 concept 已答 question_ids → 傳給 from-bank（需 endpoint 也支援 query param 或新 POST 形式）；或後端直接 join student_answers 在 service 內過濾
  - **影響**：學生短時間重練命中率低時感受不明顯（grounded 題庫每 concept 2-3 題不大），但長期會被學生抱怨；6-4 自行品管時若發現此問題優先處理

### 內容生成管線（2026-07-06 U2b 決策衍生）
- [ ] **unit content 生成管線的 `summary` 欄位閒置**
  - **背景**：2026-07-06 決策直接移除 LEARN 摘要 tab（roadmap U2b），但 6-2a grounded prompt / Pydantic 模型 / staging 表仍會生成並儲存 `summary` object
  - **如何處理**：U2b 執行時先只移除前端 tab（資料留著無害）；6-4 實機批次重跑前評估從 prompt 移除 summary 段以省 token（62 unit × summary 生成成本）

### 部署相關（待實測）
- [ ] **Zeabur PREBUILT + source.type=IMAGE schema 未實測**
  - 4-1b 將 `zeabur.json` 的 postgres 從 marketplace `postgresql`（不含 pgvector）改為 `template: PREBUILT` + `source: {type: "IMAGE", image: "pgvector/pgvector:pg16"}`
  - 此 schema 細節依 Zeabur template.json 規範撰寫，但**未經實際部署驗證**
  - **如何處理**：4-2 實際 Zeabur 部署時若 schema 被拒，依 deployment.md §A 的 fallback 改用 marketplace pgvector 或 GIT + 一行 Dockerfile
- [ ] **Judge0 自架 docker-compose 未在生產驗證**
  - 4-1c 新增 `docker-compose.judge0.yml` + `judge0.conf.example`，僅在規格層面撰寫
  - **限制**：Zeabur 等雲平台禁用 `privileged: true` → 自架 Judge0 只能在自己的 VPS 跑
  - **如何處理**：self-host VPS 部署時實測 stack 啟動 → workers 成功 register languages → backend 能透過 `/about` 與 `/submissions` 對話；若 worker fail 多半是 cgroups / privileged 問題

### 環境設定（使用者手動）
- [ ] **`backend/.env` 的 `OPENAI_API_KEY` 未填**
  - **影響**：2-1b 跑 LlamaIndex 索引、EDF Chat 互動會 401
  - **如何處理**：使用者手動填入；不可由 AI 寫入（敏感資訊）
- [ ] **git user.name / user.email 未設定**
  - **影響**：commit `3f702be` 與後續 commits 會用系統預設身分顯示在 GitHub
  - **如何處理**：
    ```bash
    git config --global user.name "你的名字"
    git config --global user.email "你的 email"
    ```

### 內容層（教學課綱）
- 🔄 **YT video metadata 未補**（已從 59 → 62 個影片 concept；2026-05-07 教授交付 playlist URL，fetcher script 已產 59 列 CSV，待擴充至 62 列）→ **正式追蹤於 roadmap Phase 6-1**
  - **影響**：3-1d 學習單元頁的概念說明 tab 無法 embed YT player；只能顯示影片標題與「待補」placeholder
  - **進度**：6-1a/b 已完成；6-1b+/c/d/e/f 進行中
  - **如何處理**：fetcher 已寫好（`backend/scripts/fetch_playlist_metadata.py`）；接下來擴充 EXPECTED 1-62、加 video 1-3 migration、PATCH script 寫入 DB、字幕 RAG ingest
  - **格式**：CSV，欄位 `video_order, youtube_id, duration_seconds, title_zh`，已產出於 `data/teaching_content/videos.csv`
- [ ] **學習單元 content 為空骨架**（`{summary: "", examples: [], exercise_question_ids: []}`）→ **正式追蹤於 roadmap Phase 6-2 / 6-3 / 6-4**
  - **影響**：3-1d 學習單元頁的「範例程式」「摘要」tab 無實質內容
  - **如何處理**：兩種策略可選 —
    - (a) LLM 依 concept name + difficulty 自動生成 summary + examples（成本低）— Phase 6-2 採此策略
    - (b) 教授/助教手動填寫（品質高，工時大）— Phase 6-4 抽查階段視需要補充
  - **決策**：先 (a) MVP，Phase 6-4 自行抽查後決定是否人工校對（2026-07-04 修訂：教授抽查已移除）

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

### 程式碼層
- [ ] **`backend/pyproject.toml` 沒設 hatchling packages**
  - 直接 `pip install -e .` 會失敗（hatchling 找不到 wheel target）
  - 目前繞過：直接列依賴而非 install self
  - **如何處理**：因 backend 是 application 不是 library，可加 `[tool.hatch.build.targets.wheel] packages = [...]` 或改用 `uv sync`（需要重組為 src/ layout）

## ✅ 已消除

- ~~`concept_edges` seed 的 23 條邊為 AI 暫定值~~ — 2026-05-05 完全替換為 58 條線性 PREREQUISITE（隨 e1f2a3b4c5d6 重 seed）
- ~~`concepts` seed 的 `category` / `difficulty_level` / `name_zh` 為暫定值~~ — 2026-05-05 完全替換為 59 影片 concept
- ~~`backend/requirements.lock` 過時~~ — 2026-05-05（4-1a）以 `uv pip compile` 重產（38 → 272 行含 transitive）；pyBKT 確認未實際 import，無需安裝
- ~~跨章節 PREREQUISITE 邊未標~~ — 2026-07-04 **K1a 完成**：migration `i5d6e7f8a9b0` curated 依賴 map 取代線性鏈 → 90 條多對多邊；實機驗證 0 孤兒節點 / 0 反向邊
- ~~EDF chat ConceptTag 不寫入 BKT mastery~~ — 2026-07-04 **K2a 完成**：`edf_parent_tag` mapping + 三層 fan-out，Workspace 對話重新驅動 BKT 且不淹沒 quiz 精準信號
