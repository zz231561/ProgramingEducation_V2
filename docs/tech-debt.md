# 技術債追蹤

> 記錄已知的技術債項目，每次消除後標記 ✅ 並註明日期。

## ⚠ 待處理

### 延遲驗收（Phase 6-2 → 6-4 必跑）
- [ ] **6-2 grounded UI 狀態尚未真機驗收** → **6-4a-deferred-ui 必驗（roadmap 已標）**
  - **背景**：6-2c / 6-2d / 6-2e 完成時 DB 內無任何 promoted `concept_explanation` / `code_examples` / `summary` object，使用者只能驗 fallback / placeholder 狀態。grounded 主路徑必須等 6-2b 實機批次（延至 6-4 合併執行）跑完才驗得到
  - **必驗項目**（任一 promoted unit 即可作 sample）：
    - 6-2c：grounded markdown render + 點 citation 真的呼叫 `player.seekTo`
    - 6-2d：卡片列表（title/code/explanation/citation）+ 「在 Workspace 開啟」→ CodeEditor `initialValue` 載入 + 一次性消費（重整不再覆蓋）
    - 6-2e：摘要 tab 三狀態切換 — (a) `summary.needs_more_source=true` notice；(b) `summary.key_points` bullet + `summary.citations` 標籤；(c) 舊 `summary: string` legacy fallback（同 lazy seed 空字串時不應觸發）
    - 6-3b：ExercisesTab 命中題庫 path（前端 Loading 顯示「查找題庫題目」< 1 秒、不打 LLM、直接顯示題目）— 當前只能驗 fallback 「AI 正在生成」path
- [ ] **練習題重複曝光**（6-3b 已標）→ Phase 6 後段 / Phase 7 前
  - **背景**：`/quiz/from-bank` service 已支援 `exclude_question_ids` 但前端 ExercisesTab 未維護已答題清單，學生重複進同 unit 練習可能抽到同題
  - **如何處理**：前端在 `useEffect` 用 `getQuizHistory` 取出該 concept 已答 question_ids → 傳給 from-bank（需 endpoint 也支援 query param 或新 POST 形式）；或後端直接 join student_answers 在 service 內過濾
  - **影響**：學生短時間重練命中率低時感受不明顯（grounded 題庫每 concept 2-3 題不大），但長期會被學生抱怨；6-4 自行品管時若發現此問題優先處理
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
- ✅ ~~`concept_edges` seed 的 23 條邊為 AI 暫定值~~ — 2026-05-05 完全替換為 58 條線性 PREREQUISITE（隨 e1f2a3b4c5d6 重 seed）
- ✅ ~~`concepts` seed 的 `category` / `difficulty_level` / `name_zh` 為暫定值~~ — 2026-05-05 完全替換為 59 影片 concept

### 內容層（教學課綱）— 新一批待補
- 🔄 **YT video metadata 未補**（已從 59 → 62 個影片 concept；2026-05-07 教授交付 playlist URL，fetcher script 已產 59 列 CSV，待擴充至 62 列）→ **正式追蹤於 roadmap Phase 6-1**
  - **影響**：3-1d 學習單元頁的概念說明 tab 無法 embed YT player；只能顯示影片標題與「待補」placeholder
  - **進度**：6-1a/b 已完成；6-1b+/c/d/e/f 進行中
  - **如何處理**：fetcher 已寫好（`backend/scripts/fetch_playlist_metadata.py`）；接下來擴充 EXPECTED 1-62、加 video 1-3 migration、PATCH script 寫入 DB、字幕 RAG ingest
  - **格式**：CSV，欄位 `video_order, youtube_id, duration_seconds, title_zh`，已產出於 `data/teaching_content/videos.csv`
- [ ] **跨章節 PREREQUISITE 邊未標**（目前只有線性 04→05→...→62 共 58 條）→ **延後到 Phase 6 教學內容建構完成後執行（2026-05-07 決議）；正式追蹤於 roadmap Phase 6-6（2026-06-23 擴大為視覺 + 核心機制優化）**
  - **影響**：拓撲排序生成路徑時，學生 confidence 高跳過某 unit 後不會牽連解鎖實際依賴的後續 unit
  - **範例**：47 遞迴函式真正依賴 36 函式 + 29 for 迴圈；52 指標與陣列依賴 48 陣列 + 51 指標；目前圖譜只有 N→N+1 線性鏈
  - **如何處理**：Phase 6 完成後，教授標關鍵跨章依賴（< 30 條，可參考 6-1e RAG 中的字幕內容輔助判斷）→ AI 加 patch migration
  - **新增範圍**：video_order 1-3（課程簡介、環境安裝、語言簡介）標記 `category="課程介紹"` 不參與 PREREQUISITE 鏈（2026-05-07 確認）；重構時保持此設計
- [ ] **學習單元 content 為空骨架**（`{summary: "", examples: [], exercise_question_ids: []}`）→ **正式追蹤於 roadmap Phase 6-2 / 6-3 / 6-4**
  - **影響**：3-1d 學習單元頁的「範例程式」「摘要」tab 無實質內容
  - **如何處理**：兩種策略可選 —
    - (a) LLM 依 concept name + difficulty 自動生成 summary + examples（成本低）— Phase 6-2 採此策略
    - (b) 教授/助教手動填寫（品質高，工時大）— Phase 6-4 抽查階段視需要補充
  - **決策**：先 (a) MVP，Phase 6-4 自行抽查後決定是否人工校對（2026-07-04 修訂：教授抽查已移除）

### Learn 頁面視覺化升級
- [ ] **3-1c 卡片版 ≠ ui-wireframes.md 期望的「節點+箭頭」graph 版**
  - **影響**：與知識圖譜頁 (`/knowledge`) 風格不統一；無法直觀顯示 PREREQUISITE 依賴的分支
  - **如何處理**：3-1d/e 完成後，回頭把 detail 頁從 ordered list 升級為 reactflow / d3 graph（可復用 knowledge 頁的元件）

### EDF Mastery 連動暫時退場
- [ ] **EDF chat 評估的 ConceptTag 不再寫入 BKT mastery**
  - **背景**：3-1c+ 把 concepts 表完全替換為 59 影片 concept；EDF 的 20 粗 tag 只留在 `services/edf/models.py` enum 給 LLM 提示用；`update_mastery` 找不到 concept 自動跳過
  - **影響**：學生在 Workspace 與 AI Tutor 對話時的 mastery 不再上下調；只有 quiz 答題 + comprehension 驗證會驅動 BKT
  - **如何處理**：兩種策略可選 —
    - (a) 接受現狀（chat 評估本來噪音多，quiz/comprehension 是更可信信號）
    - (b) 在 concepts 表加 `edf_parent_tag` 欄位，建立粗 tag → 多影片 concept 的 mapping，讓 EDF 評估平均更新到對應影片 concept

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
- ✅ ~~`backend/requirements.lock` 過時~~ — 2026-05-05（4-1a）已透過 `uv pip compile pyproject.toml -o requirements.lock` 重產（38 行 → 272 行，含全部 transitive）；pyproject.toml 補完 LlamaIndex 三套件 + psycopg2-binary。pyBKT 註解確認**未實際 import**（updater.py 註解保留為未來演算法升級線索），無需安裝
- [ ] **`backend/pyproject.toml` 沒設 hatchling packages**
  - 直接 `pip install -e .` 會失敗（hatchling 找不到 wheel target）
  - 目前繞過：直接列依賴而非 install self
  - **如何處理**：因 backend 是 application 不是 library，可加 `[tool.hatch.build.targets.wheel] packages = [...]` 或改用 `uv sync`（需要重組為 src/ layout）

## ✅ 已消除

（無）
