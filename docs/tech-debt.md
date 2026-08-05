# 技術債追蹤

> 記錄已知的技術債項目，每次消除後標記 ✅ 並註明日期。
> **機械事實（行數 / 測試數 / 路徑）一律以 `python3 scripts/doc_selfcheck.py` 產出為準，不手寫。**
> 清償排程見 `docs/roadmap.md` 的 **7-D 技術債清償**（新功能之後、驗收之前）。

## ⚠ 待處理

### 🔴 A. 功能缺口（學生實際碰不到）

**A1. Phase 2-6 Comprehension 整個前端不存在**（2026-08-06 審計發現）
- [ ] `web/` 全目錄 grep `comprehension|epl|predict|variation` **零 API 呼叫**；git 歷史確認前端從未存在
  - 後端活著：8+ 條路由（EPL / Predict / Variation / trigger-suggestion）+ `mastery_hook`（通過→BKT 上調）
    + `trigger.py` 動態頻率規則 + 約 100 個測試持續維護
  - roadmap 主表把 2-6 勾成 ✅「…動態觸發 + BKT 串接」，讀起來像整條完成；archive 實際寫的是
    「**後端**教學引擎…就緒」，2-6d 更註明「『禁用 AI』屬**前端責任**」——前端從未被任何條目追蹤
  - **後果**：論文教學設計（EPL/Fowler、Variation Theory/Marton，references.md §5.1）是死功能
  - **處置**：使用者 2026-08-06 裁決＝**補前端 UI**（排 roadmap 7-C3）

### 🔴 B. Coddy 教學品質（7-C2 排程中）

**B1. 執行狀態 `Runtime Error (NZEC)` 對教學情境會誤導**
- [ ] `runner/app/executor.py` 非零 exit → `Runtime Error (NZEC)`（沿用 Judge0 判題慣例）
  - 學生程式**正常執行、輸出正確、沒有崩潰**，只因 `return 1` 被標成「執行錯誤」
  - 對競賽判題正確，對教學平台是**平台自製的困惑**：學生以為 C++ 出錯，實際是本平台的約定
  - 需與「真的被 signal 打死」區分（`_signal_status` 已有分支，缺的是非零 exit 的教學語意）

**B2. `run_help.py` 逾時固定文案已與互動終端脫節**
- [ ] `_TIMEOUT_TEMPLATE` 仍寫「這裡是一次跑完的**批次執行**…要先在 Output 上方的『**輸入**』填好內容」
  - R4 互動終端 + R5d 移除 stdin 預填 UI 之後**這個欄位已不存在**
  - 零 LLM 的機械固定文案 → 會非常有自信地叫學生去點一個不存在的東西

**B3. 洩答殘留：prompt 層防線不保證散文不給完整解法**（2026-08-06 模擬驗收）
- [ ] hint 0-2 的洩答防線已消除字面條件（`year % 400 == 0`），但**散文描述完整規則組仍會出現**
  - 本質：LLM 指令遵循的軟性極限——「想幫忙」的傾向蓋過矩陣第 0 欄的「只提問不給提示」
  - **升級選項**：① 條件式二次檢查（僅在機械偵測到「解法形狀」時才多一次呼叫，非每輪）
    ② hint 0-1 回應模板約束 ③ 接受現狀（洩的是題目領域規則而非程式碼，學生仍須自行實作）
  - 觀測工具已備：`scripts/eval_coddy/` P3 腳本可隨時重測，此項**可量測不需憑感覺**

**B4. 前端 429 / 5xx 統一攔截宣告了但沒實作**
- [ ] `web/lib/api.ts` 檔頭與 `frontend.md` 皆寫「429 → 冷卻倒數 toast、5xx → 錯誤 toast」，實作**只有 401**
  - 後端 429 回的 `retry_after_seconds` 從未被任何前端程式碼消費
  - `use-chat.ts` 的 `catch {}` 不分辨 `ApiRequestError`：**撞每日 60 次 LLM 配額的學生看到
    「無法取得 AI 回應，請稍後再試」**——把配額誤導成故障，學生會一直重試
  - 相關：429 toast 需先引入 shadcn/ui toast（sonner）基礎設施

**B5. Evidence concept tag 雜訊 fan-out 到無關概念**（2026-08-06 模擬實證）
- [ ] hello world 被標 `control-flow` → 寫入 cpp-25-if-else；overflow 程式被標 `io-streams`（因有 cout）
  - 7-C1' 三修（無碼跳過 / 證據去重 / kgraph 先讀）已大幅降噪，但 tag 本身的誤標仍在
  - 重評時機同 K2c：Phase 5 行為資料可檢驗 LLM tagging 可靠度後（pyBKT `fit()` / AST 輔助）

### 🔴 C. 測試與工程品質

**C1. 前端零自動化測試**
- [ ] `web/` 沒有任何測試框架，但 `frontend.md` 寫著 Vitest + Playwright
  - **代價已經在付**：2026-08 十幾批 UI 改動全靠 `tsc`/`eslint`/`build` 加手動點。7-U3/U4/U5 與
    7-C1 的純函式我只能「把原始碼 `tsc` 編出來再用 node 跑斷言」——有效但**無法納入 CI、沒人會記得重跑**
  - **最小可用起點**：Vitest + 純函式測試（`lib/transcript-timestamps.ts`、`lib/hint-escalation.ts`、
    `components/workspace/use-run-history.ts`、`components/editor/cpp-completion-source.ts`）
  - ⚠ `lib/hint-escalation.ts` 另有 `backend/scripts/eval_coddy/ladder.py` 鏡像移植，**兩邊改動必須同步**——
    這正是最需要測試釘住的地方

**C2. 檔案大小超過門檻**（⚠ 150 / 🚫 250；數據來自 `scripts/doc_selfcheck.py`，2026-08-06）
- [ ] 🚫 **超過硬上限 250（8 個）**：`api/routes/quiz.py` 347 / `services/quiz/generate.py` 307 /
      `services/chat.py` 299 / `concept-detail-panel.tsx` 279 / `services/quiz/batch_generator.py` 267 /
      `services/comprehension/variation.py` 255 / `api/routes/comprehension.py` 255 / `services/quiz/feedback.py` 251
  - ⚠ 逼近提醒線者 74 個（清單跑 script 取得，不在此手抄）
  - **拆分提案**：`chat.py` → mastery gating（`_is_repeat_evidence` + skip 邏輯）抽出為獨立模組
  - 測試檔不計入（性質為條列案例而非邏輯複雜度）

**C3. OpenAI client lazy-singleton 邏輯重複於 9 個服務模組**
- [ ] evidence / feedback / quiz×4 / reflection / comprehension×2 / learning 各有一份 `_get_client`
  - **刻意延後**：各模組測試都對自己的 `_client` 做 monkeypatch，抽共用模組需連動改 9 檔 + 大量測試
  - **重評時機**：下次需統一調整 LLM client 行為（retry / timeout）時一併抽取
  - ⚠ 2026-08-06 已見代價：gpt-5.6 reasoning 參數修正雖集中在 `core/llm_params.py`，
    但**空回應的 fail-open 處理散在各模組**，同一個 root cause 要逐處補 log

**C4. `changelog.md` 已 4500+ 行**
- [ ] 單檔持續成長，查閱成本高（內容本身沒錯，是時間序日誌）
  - **如何處理**：比照 `roadmap-archive.md`，把 2026-07 以前條目移到 `changelog-archive.md`

**C5. 本機 `.venv` 與宣告的依賴脫鉤**
- [ ] `backend/.venv` 裝有 scipy 81M + pandas 48M + scikit-learn 40M（共 169M），
      但三者**既不在 `pyproject.toml` 也不在 `requirements.lock`**
  - **影響**：生產映像不受影響（Docker 內照 lock 重裝）；純本機磁碟 + 「以為裝了就能用」的錯覺
  - **如何處理**：5-3 若要用**必須先寫進 `pyproject.toml` 再重建 lock**，否則重建 venv 即消失

### 🟡 D. 部署與基礎設施

**D1. A↔B runner 走明文 HTTP**（7-R R5 已知限制）
- [ ] B 機無網域故無 TLS；`RUNNER_TOKEN` 與學生程式碼明文往返公網
  - **現行防線**：ufw + 騰訊安全群組雙層鎖來源 IP + 共享密鑰；B 機不含任何機密、被攻陷即重灌
  - **改善選項**：① B 機掛子網域 + Caddy 自動 TLS ② A↔B 建 WireGuard 隧道並綁 127.0.0.1
  - **重評時機**：2027-01 可用性評估前（與自訂網域送 Google 驗證一併處理）

**D2. `backend.md`「OpenAI 失敗 → 快取最近回應」降級策略未實作**
- [ ] 現況：6-R6 已保證 LLM 失敗時學生輸入不丟失（user message 先 commit），前端可重試
  - **如何處理**：Redis 存 per-user 最近一次成功回應，LLM 5xx 時回傳並標註 fallback

### 🟡 E. 內容與視覺（低優先）

**E1. 題庫 coding 題 validate 通過率偏低**
- [ ] 批次仍有部分題目 `VALIDATION_RETRY_EXHAUSTED`（v41 重生時 8 題中 3 題 MC 失敗）
  - v17/v41 掛零已解除（v17 有 8 題、v41 重生後 5 題）
  - **如何處理**：6-4b 檢視 validate 失敗 reason 分佈後調整 generate prompt

**E2. Learn 頁卡片版 ≠ ui-wireframes.md 期望的「節點+箭頭」graph 版**
- [ ] 與 `/knowledge` 風格不統一；無法直觀顯示多對多 PREREQUISITE 分支
  - **如何處理**：復用 knowledge 頁 Cytoscape 元件（K5 已完成，隨時可評估）

**E3. 真 AST（tree-sitter / libclang）暫不引入**（K2c 決策記錄）
- [ ] 現以 LLM Evidence 為程式碼分析信號；自建 AST 特徵規則工程成本高且與 LLM 重複
  - **重評時機**：同 B5——Phase 5 行為資料可檢驗 LLM tagging 可靠度後

---

## ✅ 已消除

### 2026-08-06（7-C 系列 + 文件稽核）
- ~~🔴 **Hint Ladder 在對話路徑上從未接通**~~ — 7-C1：`hint_level` 原寫死 0，36 格策略矩陣只用得到第 0 欄、
  學生連問四次也不升級。修＝`web/lib/hint-escalation.ts` + `use-chat.ts` ref 追蹤；
  下游 hint_request 行為事件與 ASKING_HINT 分支隨之復活
- ~~🔴 **Evidence 層拿不到 exit_code / status_description**~~ — 7-C1：NZEC 時 stderr 全空，
  prompt 原本對 LLM 說「程式執行成功」而學生螢幕是 Runtime Error。修＝兩參數注入 + `_has_execution_error` 同步
- ~~🔴 **gpt-5.6 reasoning 預算間歇吃光輸出**~~ — 7-C1'：2026-08-05「拒收 reasoning_effort」結論**錯誤**
  （只是值域改為 none/low/…）；預設浮動燒 reasoning 與正文共用預算 → 整包空輸出，
  **反思評分因此在生產一直靜默 fail-open**。修＝gpt-5.6 一律 `reasoning_effort="none"` + 補 log
- ~~🔴 同一份執行結果被重複計為 BKT 負證據~~ — 7-C1'：`_is_repeat_evidence` 去重
- ~~🔴 無程式碼的導覽性提問建立精熟度~~ — 7-C1'：code 空白不更新 BKT
- ~~🔴 kgraph 鷹架被當輪 tag 雜訊污染~~ — 7-C1'：改在 mastery 更新**前**讀取
- ~~🟡 off_topic 回填輸給關鍵字誤標~~ — 7-C1'：LLM 判定離題一律覆寫
- ~~🟡 RAG 查詢不含學生問句~~ — 7-C1'：問句放最前；課程定位型問句只用問句檢索
- ~~🟡 Coddy 反過來要學生提供教材連結~~ — 7-C1'：NO_SOURCE_RULE / CITATION_RULE 各補一條
- ~~文件路徑漂移 4 處~~ — 2026-08-06 `doc_selfcheck.py` 抓出並當場修正：
  `shadcn/ui/button.tsx` → `web/components/ui/button.tsx`；`backend/app/core/config.py` → `backend/core/config.py`；
  K4f 寫的 `services/compile_error.py` 實為 `services/run_help.py`；`galaxy-backgrounds.ts` 早已刪除卻寫「留作備援」
- ~~**7-R 過渡期 stdin 預填 UI 兩缺陷**~~ — 2026-08-06 關閉：R4 互動終端 + R5d 移除該 UI 皆已上線並驗收，
  「回退條款」前提（7-R 中止）已不可能成立
- ~~**Zeabur PREBUILT + source.type=IMAGE schema 未實測**~~ — 2026-08-06 關閉：7-1a 實際部署走
  **dashboard 手動建立四 service**，未使用 `zeabur.json` template 路徑，此風險項已無對應現實
- ~~tech-debt「延遲驗收 Phase 6-2」整段過期~~ — 移除（6-2c 已驗收、6-2d/e 的 tab 早被 U2g/U2b 刪除）
- ~~驗收清單含已作廢項目~~ — 全面重寫為 0~9 段操作動線 + 已作廢項目對照表

### 2026-08-05 及更早
- ~~🔴 **章節 41 教材把 `extern` 寫成 `external`**~~ — 2026-08-05 全數修畢（corrections + RAG 重建 +
  內容題目重生 + promote + 生產同步，四張表殘留皆 0）。根因＝Whisper 逐字稿錯字被 grounded 生成忠實複製
- ~~Judge0 自架 docker-compose 未在生產驗證~~ — 2026-08-05 作廢：正式方案改 7-R 自建 runner，
  Judge0 降為 RapidAPI fallback；`docker-compose.judge0.yml` 保留僅供追溯
- ~~`requirements.lock` 與 `pyproject.toml` 脫鉤（缺 python-multipart）~~ — 2026-08-04：lock 停留 4-1a 版
  導致生產映像缺套件、容器啟動即崩；已重產並 docker build 實測（81 routes）
- ~~judge0.py 不支援自架 authn header~~ — 2026-07-18 `_build_headers` 加 authn 分支 + 4 tests
- ~~lazy-seed 新使用者的 unit content 仍是空骨架~~ — 2026-07-18 seed 時讀 staging（approved）帶入 content
- ~~`backend/pyproject.toml` 沒設 hatchling packages~~ — 2026-07-18 補 wheel target
- ~~git user.name / user.email 未設定~~ — 2026-07-18 確認已設定
- ~~backend/uv.lock 未追蹤副產品~~ — 2026-07-18 加入 .gitignore（正本維持 requirements.lock）
- ~~練習題重複曝光~~ — 2026-07-06 U2d：bank service 加 `exclude_answered_by`，兩入口同時生效
- ~~`knowledge-graph.tsx` 265 行超標~~ — 2026-07-06 拆出 `use-graph-nav.ts`（主元件 212 行）
- ~~unit content 生成管線的 `summary` 欄位閒置~~ — 2026-07-06 U2b：整條管線移除，批次省 1/3 calls
- ~~`backend/.env` 的 `OPENAI_API_KEY` 未填~~ — 2026-07-06 確認已填
- ~~跨章節 PREREQUISITE 邊未標~~ — 2026-07-04 K1a：90 條多對多邊，0 孤兒 / 0 反向邊
- ~~EDF chat ConceptTag 不寫入 BKT mastery~~ — 2026-07-04 K2a：`edf_parent_tag` + 三層 fan-out
- ~~`concept_edges` seed 的 23 條邊為 AI 暫定值~~ — 2026-05-05 替換為線性 PREREQUISITE（後由 K1a 再替換）
- ~~`concepts` seed 的 category / difficulty_level / name_zh 為暫定值~~ — 2026-05-05 替換為 59 影片 concept
- ~~`backend/requirements.lock` 過時~~ — 2026-05-05 以 `uv pip compile` 重產
