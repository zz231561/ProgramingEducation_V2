# 技術債追蹤

> 記錄已知的技術債項目，每次消除後標記 ✅ 並註明日期。
> **機械事實（行數 / 測試數 / 路徑）一律以 `python3 scripts/doc_selfcheck.py` 產出為準，不手寫。**
> 清償排程見 `docs/roadmap.md` 的 **7-D 技術債清償**（新功能之後、驗收之前）。

## ⚠ 待處理

### 🔴 B. Coddy 教學品質

**B4. 全站 429 / 5xx toast 仍未實作**（7-C2b 已修掉最痛的 chat 路徑，其餘待辦）
- [x] ~~chat 撞配額被誤導成故障~~ — 7-C2b：`lib/chat-error.ts` 分辨 `DAILY_QUOTA_EXCEEDED`
      （原文照用，已寫明何時恢復）與 `RATE_LIMITED`（消費 `retry_after_seconds` 顯示秒數）
- [ ] `web/lib/api.ts` 檔頭與 `frontend.md` 寫的是**全站** toast 攔截，目前仍只有 401 重導
  - 其他頁面（quiz / learn / 教師端）撞 429 或 5xx 仍是各自的 catch，訊息不一致
  - 需先引入 shadcn/ui toast（sonner）基礎設施 → **排 7-D6**

**B5. Evidence concept tag 雜訊 fan-out 到無關概念**（2026-08-06 模擬實證）
- [ ] hello world 被標 `control-flow` → 寫入 cpp-25-if-else；overflow 程式被標 `io-streams`（因有 cout）
  - 7-C1' 三修（無碼跳過 / 證據去重 / kgraph 先讀）已大幅降噪，但 tag 本身的誤標仍在
  - 重評時機同 K2c：Phase 5 行為資料可檢驗 LLM tagging 可靠度後（pyBKT `fit()` / AST 輔助）

### 🔴 C. 測試與工程品質

**C1. 前端零自動化測試** — ✅ **框架已建立（2026-08-07，7-D1）**，剩 E2E
- [x] ~~`web/` 沒有任何測試框架~~ — Vitest(jsdom) + `npm test`／`npm run test:watch`；
      三支純函式測試共 31 個 `it`（`transcript-timestamps` / `use-run-history` / `cpp-completion-source`）；
      `doc_selfcheck.py` 已加計 web 測試數。**立刻回本**：測試寫到一半就抓出
      `cpp-completion-source.ts` 一個永遠不成立的條件分支（Ctrl+Space 手動觸發形同虛設）
- [ ] `frontend.md` 另寫的 **Playwright E2E 仍未建置**（golden path：登入 → 寫程式 → 執行 → AI 對話）
  - **刻意不在 7-D1 一起做**：E2E 需要跑起後端 + runner + DB，屬部署環境依賴，
    與「純函式單元測試」不同層級；**重評時機＝7-E 使用者驗收跑完後**（驗收動線本身就是 E2E 腳本的規格）
- [ ] 元件測試（React Testing Library）同樣未建置——本批刻意不裝 `@vitejs/plugin-react`，
      待真的要測元件互動時再引入

**C2. 檔案大小超過門檻** — ✅ **已清空（2026-08-07）**，規則同日改版
- [x] ~~🚫 超過硬上限的 7 個檔~~ — 依新規則逐案判斷後：**1 拆分 + 6 舉證豁免**
  - **拆分**：`services/quiz/generate.py` 307 → 拆出 `generate_prompts.py`（205 / 110）。
    理由＝prompt 內容與生成流程是兩個獨立變更軸（7-C 期間大量調 prompt 完全不動流程），
    與既有慣例 `variation_prompts.py`、`edf/prompt_blocks.py` 一致
  - **豁免**（檔頭寫 `code-health: allow-large` + 對應三問的理由）：`api/routes/quiz.py`、
    `api/routes/comprehension.py`、`batch_generator.py`、`comprehension/variation.py`、
    `quiz/feedback.py`、`concept-detail-panel.tsx`
  - 現況 🚫 0 個 / ⚠ 0 個 / 已豁免 6 個（跑 `doc_selfcheck.py` 取得，**刻意不手抄**）
  - ✅ 2026-08-06（7-C2a'）先清掉兩個：`edf/feedback.py`、`services/chat.py`
  - 測試檔不計入（性質為條列案例而非邏輯複雜度）

> **規則已於 2026-08-07 改版**（全域 + 專案 CLAUDE.md + `.claude/skills/code-health/`）：
> 門檻 150/250 → **250/400**（原 150 產生 78 個警告＝警告失效），判準改為
> 「AI 能否用檔名預測內容 + 能否一次讀完」，超標須逐案回答三問後三選一，並新增舉證豁免出口。

**C3. OpenAI client lazy-singleton 邏輯重複於 14 個服務模組**（2026-08-06 重數：原記 9 個已低估）
- [ ] `grep -rl "def _get_client" backend/services/` → 14 檔：edf×2 / quiz×5 / comprehension×3 /
      reflection / learning / run_help / chat_kickoff
  - **2026-08-07 起由機械檢查抓得到**：`jscpd --min-lines 5 --min-tokens 30` 命中（跨 ≥3 檔，
    達到 code-health skill 的處理門檻）。實際是兩個變體各複製 7 行——
    `raise AppError(503)` 版與 `return None` 版。**這 14 個檔全部通過行數檢查**，
    正是「AI 看不到既有實作就重寫」這類債完全逃過大小規則的實例
  - **刻意延後**：各模組測試都對自己的 `_client` 做 monkeypatch，抽共用模組需連動改 14 檔 + 大量測試
  - **重評時機**：下次需統一調整 LLM client 行為（retry / timeout）時一併抽取
  - ⚠ 2026-08-06 已見代價：gpt-5.6 reasoning 參數修正雖集中在 `core/llm_params.py`，
    但**空回應的 fail-open 處理散在各模組**，同一個 root cause 要逐處補 log

**C4. `changelog.md` 已近 5000 行**（2026-08-06 實測 4977，本 session 又長了約 200 行）
- [ ] 單檔持續成長，查閱成本高（內容本身沒錯，是時間序日誌）
  - **如何處理**：比照 `roadmap-archive.md`，把 2026-07 以前條目移到 `changelog-archive.md`

**C6. 5-2b 的 chat 事件記錄已失效**（2026-08-07 由 ruff F401 意外揭露）
- [ ] `api/routes/chat.py` 曾 import `CodingEventType` / `log_coding_event`，但**全專案無任何呼叫**
  - 根因：5-2b 當初掛的是「`hint_level > 0` 記 `hint_request` 事件」，
    7-C2a 把 `hint_level` 從前端移除後，該呼叫一併消失，只留下孤兒 import（本次已清）
  - **影響**：`coding_events` 表現在只剩 `/code/execute` 的執行事件，
    chat 端的 hint 行為訊號等於斷線 → **5-3 行為分析的資料來源少一類**
  - **如何處理**：5-3 開工前決定要不要改記新的 chat 訊號（如 `explicit_help` 按鈕點擊，
    那才是 7-C2a 之後的等價物）；不補就要調整 5-3a/5-3c 的指標定義

**C5. 本機 `.venv` 與宣告的依賴脫鉤**
- ✅ 2026-08-07 修掉反向的一例：`ruff` 在 `pyproject.toml` dev 依賴中宣告且已設定，
  但**從未安裝進 venv** → lint 從來沒跑過。已安裝（`VIRTUAL_ENV=.venv uv pip install ruff`；
  該 venv 由 uv 建立、不含 pip，不能用 `.venv/bin/pip`）
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
- ~~🟡 **B3 洩答殘留**~~ — 7-C4 裁決：**不加二次檢查**（七型實測 RULE-1/2 從未被突破，
  沒有程式碼層級洩答；多一次 LLM 呼叫解錯問題）。真正的缺陷是**防線措辭寫錯**——
  已改成「禁止代替學生完成**目標概念**的推理，背景知識可直說」，與教學裁決一致
- ~~🔴 **comprehension 觸發吸收態**（7-C4 量測發現）~~ — 1 筆通過 → 100% → 永久跳過 →
  樣本永遠停在 1 筆，整個 2-6 對每個學生只啟動一次。修＝`MIN_SAMPLES_TO_SKIP = 3`。
  **休眠至今是因為前端不存在**（7-C3 才給它流量）
- ~~🔴 **Phase 2-6 Comprehension 整個前端不存在**（原 A1）~~ — 7-C3：補上 `lib/comprehension.ts` +
  `components/comprehension/` 7 檔，接入 Quiz 結果頁與 Learn 觀念題 tab；變體挑戰的「禁用 AI」
  （2-6d 明列的前端責任）以 AppShell 層級的 AI 鎖實作，不是只把按鈕藏起來。
  後端 8 條路由與 `mastery_hook` 從此有真實流量
- ~~🟡 **NZEC 對教學情境會誤導**（原 B1）~~ — 7-C2b：新增機械判定固定文案（`kind="nzec"`，零 LLM），
  分清 **C++ 標準 / OS 慣例 / 本平台判定**三層並以第一人稱交代本平台行為；
  Feedback 另加 RULE-7 讓對話路徑也照這個層次講。
  ⚠ runner 的狀態字串**刻意不動**（判題／教材健檢依賴該慣例），改的是教學語意不是判定
- ~~🟡 **逾時文案叫學生去填已移除的「輸入」欄位**（原 B2）~~ — 7-C2b：改寫成互動終端的實際操作
  （游標在閃＝在等你打字，直接在終端機輸入再按 Enter）
- ~~🟡 **`base(error_type)` 每輪重判導致 reveal 回退**（原 B8）~~ — 7-C2a''：`stabilize_error_type`
  同證據沿用上輪判定；實測 P3 由 1→1→0→0 變 1→1→1→1
- ~~🔴 **Evidence 單一欄位越界毀掉整次互動**~~ — 7-C2a''：LLM 把 ConceptTag 寫進 `error_type`
  會讓學生收到 502（實測 P5 撞到）。改走 `EvidenceResult.from_llm()` 容錯解析，
  只有 JSON 本身壞掉才 502
- ~~🟡 **persistence 只增不減、唯一歸零是跑成功**（原 B7）~~ — 7-C2a'：選層輸入從「追問次數」
  換成 need 狀態估計（理解 −1／沒理解 +1／失敗的實質嘗試 +1／**追問與施壓 0**），
  歸零改為事實或保守二元判定（跑成功／換卡點／閒置 30 分）。三個症狀一次解掉；
  實測 P3 四輪施壓 need 恆 0、P2 理解訊號自動壓住 need
- ~~🟡 **`decision.py` L5 措辭與 RULE-1 自相矛盾**（原 B6）~~ — 7-C2a：36 格矩陣整份刪除，
  改累積式階梯；RULE-1／RULE-2 明文寫成「階梯之上的不變量」，L5 的「完整」＝解釋完整非程式碼完整。
  附帶消除「反覆失敗 5+ 次才觸發 L5」這條從未被實作的敘述（persistence 搬後端後才真正有門檻）
- ~~🟡 **前端與 harness 的 hint ladder 人工鏡像**（原 C1 附帶）~~ — 7-C2a：`web/lib/hint-escalation.ts`
  與 `backend/scripts/eval_coddy/ladder.py` 同時刪除，persistence 改由 `services/chat_signals.py` 單一來源計算
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
