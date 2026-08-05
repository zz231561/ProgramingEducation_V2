# 技術債追蹤

> 記錄已知的技術債項目，每次消除後標記 ✅ 並註明日期。

## ⚠ 待處理

### 🔴 Hint Ladder 在對話路徑上從未接通（2026-08-06 使用者回報 Coddy 對話後查證）
- [ ] **`web/hooks/use-chat.ts:75` 把 `hint_level: 0` 寫死**，前端從未遞增
  - `decide_strategy()` 的 docstring 寫「hint_level 由前端追蹤（學生同一問題連續求助次數）」，
    但**只有 quiz 路徑真的有傳**（`quiz-runner.tsx` / `weakness-quiz-runner.tsx` 傳 `hints.length + 1`），chat 路徑恆為 0
  - **後果**：`_STRATEGY_MATRIX` 36 格中，對話永遠只用得到第 0 欄——最不肯給資訊的一欄
    （`(2,0)` 請學生用自己的話解釋、不給提示／`(3,0)` 問學生打算怎麼應用／`(4,0)` 請學生分析結構），
    且 `allow_code_snippet` 恆為 False。**學生連問四次同一件事也不會升級到直接說明**
  - 這是 `.claude/rules/edf-pipeline.md` 明列的核心設計（Hint Ladder 0-5）在對話裡實際是死的
  - **實例**：學生問「誰定義 return 0 代表正常」，Coddy 連續反問，最後由學生 push back 兩次才逼出正確答案
  - **下游災情（2026-08-06 全面審計確認，同一根因）**：
    ① `chat_sse.py:83` `if body.hint_level > 0` 記 hint_request 行為事件——**永不觸發**，
       5-2 行為資料的 hint 分布在 chat 恆為空（未來 5-3 行為分析直接缺一軸）
    ② `classify_dialogue_act` 第一優先分支 `hint_level > 0 → ASKING_HINT` 在 chat 是死路，
       只剩關鍵字啟發式在撐
    → 修 hint_level 接線後這兩項**自動復活**，不需另外動

### 🔴 Phase 2-6 Comprehension 整個前端不存在——後端閉環完整但學生永遠碰不到（2026-08-06 審計發現）
- [ ] **`web/` 全目錄 grep `comprehension|epl|predict|variation` 零 API 呼叫**；git 歷史確認前端**從未存在過**
  - 後端活著的部分：8+ 條路由（EPL generate/grade、Predict、Variation、trigger-suggestion）+
    `mastery_hook`（通過→BKT 上調）+ `trigger.py` 動態頻率規則 + **約 100 個測試持續維護中**
  - roadmap 主表把 2-6 勾成 ✅「EPL + Predict + Variation + **動態觸發 + BKT 串接**」——讀起來像整條功能完成；
    實際 archive 寫的是「**後端**教學引擎…就緒」，且 2-6d 註明「『禁用 AI』屬**前端責任**」——前端從未被任何條目追蹤
  - **後果**：Post-Solution Comprehension（論文教學設計：EPL/Fowler、Variation Theory/Marton，
    references.md §5.1 有標）是死功能；其 BKT 強證據訊號源也一併缺席
  - **處置需使用者裁決**：補前端 UI（量體不小：三種驗證各有作答流程）vs 降級為論文描述「已實作未部署」vs 移除

### 🔴 Evidence 層拿不到 exit_code / status_description——執行結果注入不完整（2026-08-06 審計發現）
- [ ] `services/chat.py` 只從 execution_result 抽 `stdout / stderr / compile_output` 餵給 `analyze_evidence()`，
      **`exit_code` 與 `status_description` 被丟棄**（前端明明有送——`ExecutionResult` 型別完整）
  - **後果**：非零 exit（NZEC）時 stderr 全空 → Evidence LLM **機械上看不到任何異常訊號**；
    使用者實例中 Coddy 知道 Runtime Error 是因為**學生自己打字說的**，不是管線給的
  - 同族：`classify_dialogue_act._has_execution_error` 也只看 stderr/compile_output →
    學生那句「出現了Runtime Error 為什麼？」**沒被分類成 DEBUGGING**（行為資料又失真一筆）
  - edf-pipeline.md 寫「注入 Judge0 執行結果（stdout/stderr）作為分析脈絡」——文件如實描述了縮水範圍，
    但 7-R 之後 status_description 已是學生實際看到的主要訊號，管線卻看不到

### 🟡 前端 429 / 5xx 統一攔截宣告了但沒實作（2026-08-06 審計發現）
- [ ] `web/lib/api.ts` 檔頭註解與 `frontend.md` 皆寫「401 → 重導登入、**429 → 冷卻倒數 toast、5xx → 錯誤 toast**」，
      實作**只有 401**；後端 429 回的 `retry_after_seconds` 從未被任何前端程式碼消費
  - `use-chat.ts` 的 `catch {}` 不分辨 `ApiRequestError`：**撞每日 60 次 LLM 配額（6-M3）的學生
    看到的是「無法取得 AI 回應，請稍後再試」**——把配額誤導成故障，學生會一直重試
  - 使用者實測對話中那次「無法取得 AI 回應」無法從 UI 分辨是 502 還是 429，正是此缺陷的體現

### 🔴 執行狀態 `Runtime Error (NZEC)` 對教學情境會誤導
- [ ] `runner/app/executor.py:67` 非零 exit → `Runtime Error (NZEC)`（沿用 Judge0 判題慣例）
  - 學生程式**正常執行、輸出正確、沒有崩潰**，只因 `return 1` 被標成「執行錯誤」
  - 對競賽判題是對的，對教學平台是**平台自製的困惑**：學生以為 C++ 出錯，實際是本平台的約定
  - 需與「真的被 signal 打死」區分（`_signal_status` 已有分支，缺的是非零 exit 的教學語意）

### 🔴 `run_help.py` 逾時固定文案已與互動終端脫節
- [ ] `_TIMEOUT_TEMPLATE` 仍寫「這裡是一次跑完的**批次執行**，程式不會停下來等你打字，
      要先在 Output 上方的「**輸入**」填好內容」
  - R4 互動終端上線 + R5d 移除 stdin 預填 UI 之後，**這個「輸入」欄位已不存在**
  - 此為零 LLM 的機械固定文案 → 會非常有自信地叫學生去點一個不存在的東西

### 🔴 前端零自動化測試
- [ ] **`web/` 沒有任何測試框架**，但 `frontend.md` 寫著 Vitest + Playwright
  - **代價已經在付**：2026-08 這一輪十幾批 UI 改動，全靠 `tsc` / `eslint` / `build` 加使用者手動點。7-U3/U4/U5 的純函式（時間戳改寫、per-file 歷史 store、識別字掃描）我只能用「把真實原始碼 `tsc` 編出來再用 node 跑斷言」來驗——**這個做法有效但無法納入 CI、也沒人會記得重跑**
  - **最小可用起點**：Vitest + 幾支純函式測試（`lib/transcript-timestamps.ts`、`components/workspace/use-run-history.ts`、`components/editor/cpp-completion-source.ts`）即可把上述臨時驗證固化下來；React 元件測試與 Playwright 可後續再加
  - **時機**：介面已於 7-U 收斂完畢，適合現在補

### 文件一致性（2026-08-06 稽核發現）
- [x] ~~tech-debt「延遲驗收 Phase 6-2」整段過期~~ — 2026-08-06 移除：6-2c 已驗收、6-2d/6-2e 的 tab 早被 U2g/U2b 刪除、排查指引還指向已不存在的 `web/lib/pending-workspace-code.ts`
- [x] ~~驗收清單含已作廢項目~~ — 2026-08-06 全面重寫：移除 A12（stdin 預填 UI 已隨互動終端移除）等，改依操作動線編排並附「已作廢項目」對照表
- [ ] **`changelog.md` 已 4500+ 行**，單檔持續成長
  - **影響**：查閱成本高；但它是時間序日誌，內容本身沒錯
  - **如何處理**：比照 `roadmap-archive.md` 的做法，把 2026-07 以前的條目移到 `changelog-archive.md`

### 檔案大小超過門檻（⚠ 提醒線 150，硬上限 250）
> ⚠ **2026-08-06 首次量測的「無任何檔案超過硬上限」是錯的** —— 那次只掃了 7-U 期間動過的檔案，
> 卻寫成全域結論。同日 8-0 討論時全專案重掃，發現 **4 個非測試檔超過硬上限 250**。
> 這正是 8-1d 自檢 script 要消滅的錯誤類型（手寫數字沒有東西會在它失真時報錯）。

- [ ] 🚫 **超過硬上限 250**：`api/routes/quiz.py` 347 / `services/quiz/generate.py` 307 /
      `components/knowledge/concept-detail-panel.tsx` 279 / `services/quiz/batch_generator.py` 267
  - **處理方式**：不趕在驗收期動刀（改動風險大於收益），列入 Phase 8 由使用者裁決拆分順序
- [ ] ⚠ **逼近提醒線 150–250**：`code-files-sidebar.tsx` 207 / `api/routes/chat.py` 208 / `run-block.tsx` 201 /
      `workspace/page.tsx` 190 / `services/workspace_files.py` 174 / `runner/app/terminal.py` 165 /
      `output-panel.tsx` 164 / `use-named-file.ts` 159 / `api/routes/code_files.py` 153
- 測試檔不計入（`tests/` 最大 574 行，性質為條列案例而非邏輯複雜度）

### 本機 `.venv` 與宣告的依賴脫鉤（2026-08-06 8-0b 量測發現）
- [ ] `backend/.venv` 裝有 **scipy 81M + pandas 48M + scikit-learn 40M（共 169M）**，
      但這三個套件**既不在 `pyproject.toml` 也不在 `requirements.lock`**
  - **推測來源**：早期評估 pyBKT / 5-3 行為分析時試裝，後來未宣告也未移除
  - **影響**：生產映像不受影響（Docker 內是照 `requirements.lock` 重裝，不會帶到）；
    純粹是本機磁碟佔用 + 「以為裝了就能用」的錯覺風險
  - **如何處理**：5-3 開發時若真要用，**必須先寫進 `pyproject.toml` 再重建 lock**；
    否則重建 venv 即消失。列入 8-2c 盤點

### 部署相關（待實測）
- [ ] **A↔B runner 走明文 HTTP**（7-R R5 已知限制）
  - B 機無網域故無 TLS；`RUNNER_TOKEN` 與學生程式碼明文往返公網
  - **現行防線**：ufw + 騰訊安全群組雙層鎖來源 IP + 共享密鑰；B 機不含任何機密、被攻陷即重灌，最壞情況是被當免費算力
  - **改善選項**：① B 機掛自訂子網域 + Caddy 自動 TLS ② A↔B 建 WireGuard 隧道並改綁 127.0.0.1
  - **重評時機**：2027-01 可用性評估前（與自訂網域送 Google 驗證一併處理）
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
