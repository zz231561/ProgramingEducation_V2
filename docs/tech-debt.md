# 技術債追蹤

> 記錄已知的技術債項目，每次消除後標記 ✅ 並註明日期。

## ⚠ 待處理

### 檔案大小逼近門檻（⚠ 提醒，未超硬上限）
- [ ] `code-files-sidebar.tsx` 207 / `run-block.tsx` 201 / `services/workspace_files.py` 174 / `use-named-file.ts` 159 / `api/routes/code_files.py` 153 / `toolbar.tsx` 147

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
- [x] ~~Judge0 自架 docker-compose 未在生產驗證~~ — **2026-08-05 作廢**：正式方案改 7-R 自建 runner（roadmap 7-R / server-plan.md），Judge0 降為 RapidAPI fallback、不再自架；`docker-compose.judge0.yml` 保留僅供追溯

### 7-R 過渡期已知缺陷（刻意不修，由 R4 取代）
- [ ] **Workspace stdin 預填 UI 兩缺陷**（2026-08-05 A12 驗收發現）
  - ① `output-panel.tsx` 的 `getCode()` 在 render body 讀值、無編輯器變化訂閱 → 「程式在等待輸入」提示要跑過一次才出現
  - ② `use-run-code.ts` `run()` 不檢查「程式讀輸入但 stdin 為空」→ 按 Run 直接送出
  - **不修理由**：7-R R4 互動終端上線後整組 stdin 預填 UI 降級為「進階：預先餵入」，兩缺陷隨之消滅
  - **回退條款**：若 7-R 中止，必須回頭修這兩處

### 內容層（教學課綱）
- [x] ~~🔴 **章節 41 教材把 `extern` 寫成 `external`**~~ — 2026-08-05 全數修畢（corrections + RAG 重建 + 內容題目重生 + promote + **生產同步完成**，四張表殘留皆 0）
- [ ] ~~原記錄（已消除，保留說明供追溯）~~ **章節 41 教材把 `extern` 寫成 `external`**（2026-08-05 盤點 Judge0 能力矩陣時發現）
  - **根因**：Whisper 逐字稿 [00:35]「在資料型態的前面加上 external 這個字」→ grounded 生成忠實複製錯誤關鍵字
  - **影響**：學生照打 `external int x;` 編譯必失敗；本機與**生產庫皆有**（RAG 2 chunks / staging 1 / learning_units 1 / questions 2）
  - **極可能是 v41 題庫掛零主因**（生成端依錯誤教材出題 → 審查端打回）
  - **修法鏈**：`corrections.json` 加 `"external": "extern"` → `apply_corrections --only 41` → RAG 重 ingest v41 → 重生 v41 content + questions → promote → 生產重播種
- [ ] **題庫 coding 題 validate 通過率偏低**（2026-07-06 實機批次觀察；2026-08-05 修訂）
  - **v17/v41 掛零已解除**：v17 實查有 8 題（6-3c 批次已補，原記錄過期）；v41 因 `external` 錯字重生後有 5 題
  - **現況**：批次仍有部分題目 `VALIDATION_RETRY_EXHAUSTED`（v41 重生時 8 題中 3 題 MC 失敗）
  - **如何處理**：6-4b 檢視 validate 失敗 reason 分佈後調整 generate prompt

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

- ~~`requirements.lock` 與 `pyproject.toml` 脫鉤（缺 python-multipart）~~ — 2026-08-04 Phase 7 部署前置檢查發現；lock 停留 4-1a 版導致生產映像缺套件、backend 容器啟動即崩；已 `uv pip compile` 重產並以 docker build 實測 app 可載入 81 routes。deployment.md checklist 同步改為「改 pyproject 必重產 lock」
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
