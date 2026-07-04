# 變更日誌

## [2026-07-04] — feat(K4c)：補救路徑 — 診斷結果重新開放前置單元

### Added
- `services/learning/remedial.py`：`open_remedial_units` — 嫌疑概念在學生 default path 的既有 units 重新開放（completed/locked → available + 清 completed_at；available/in_progress 不動仍列入回傳）；**不新建 row**（62 concept 都已有 unit），不觸碰 (path_id, order_index) 唯一約束；completed → available 為系統級動作（手動 transition 禁止，但診斷已證明概念沒學牢，有教學依據）
- `POST /concepts/{tag}/diagnosis/remediate`：先跑診斷（404 未知 concept / 409 未觸發），觸發後開放全部嫌疑 units，回傳 order_index 升冪的補救清單（= 建議學習順序，最基礎先學）
- `tests/test_remedial.py` 5 tests（service reopen/noop + route 409/404/整合）→ **後端 546 tests 全綠**

### Changed
- `docs/api-spec.md` 補 remediate 端點；roadmap K4c 勾選
- K4 僅剩 K4d 真人驗收（需 OPENAI_API_KEY，建議與 6-4a 實機批次合併執行）

---

## [2026-07-04] — feat(K4a/b)：Coddy 自適應提示 — K-Graph 鷹架 + RAG 相關性觸發

### Added
- **K4a** `services/edf/kgraph_context.py`：學生知識狀態 → prompt block（解析 evidence tags 直接命中 + `edf_parent_tag` group 已曝光成員、弱者優先取 6 筆）+ 鷹架分級指令（以**最弱**相關概念 confidence 決定：<0.4 框架填空/逐行拆解、0.4-0.7 引導式提問、>0.7 只點 edge case）；best-effort 無資料回空字串不擋教學流程
- `chat.py` interact 在 mastery 更新後讀取 kgraph block（鷹架依最新狀態）注入 `generate_feedback`
- 測試 +9（7 kgraph + 2 RAG 分數過濾）→ **後端 541 tests 全綠**

### Changed
- **K4b（原 6-5a）** RAG 觸發改內容相關性：`TeachingStrategy` 移除 `use_rag` 欄位與 `hint>=2 && bloom>=ANALYZE` 寫死規則；`fetch_rag_chunks_safe` 每次互動都檢索、只注入 cosine >= `RAG_MIN_SCORE`（0.40 初始值，K4d 實測調參）的 chunks，全低於門檻回空（該查就查、不相關不硬塞）
- **K4a（原 6-5b）** persona 語氣改寫：Coddy 具名、先肯定再引導、提問具體到程式碼、小事直接回答；RULE-5 從「永遠以提問結尾」放寬為「自然的下一步收尾（提問或行動建議），不必刻意反問」
- `.claude/rules/edf-pipeline.md` 同步：RAG 觸發規範改為相關性分數、prompt 組裝順序加 kgraph 層、persona 描述更新
- 既有 decision / feedback 測試配合 `use_rag` 移除改寫

---

## [2026-07-04] — feat(K3)：根源弱點定位器後端（圖回溯認知診斷）

### Added
- `services/diagnosis/root_cause.py`：**K3a** stateless 觸發判定（該 concept 最近作答連續失敗 streak，遇答對截斷，>= 3 觸發）+ **K3b** closure（max_depth=3）回溯嫌疑排序（已曝光低 confidence 優先 → 未曝光盲區；高 confidence 前置排除；上限 3）+ **K3c** 每個嫌疑附題庫 validated 診斷題 question_id
- **K3d-API** `GET /concepts/{tag}/diagnosis`（獨立 route 檔避免 concepts.py 破 250 行；純 DB 讀取不掛 rate limit；未觸發回 triggered=false 供前端隱藏入口）
- `tests/test_diagnosis.py` 9 tests（streak 截斷 / 嫌疑排序 / 高 conf 排除 / 題庫附題 / route 401+404+整合）→ **後端 533 tests 全綠**
- 新增 K3e（前端入口）追蹤項，建議與 K5 視覺改版一併設計

### Changed
- `docs/api-spec.md` 補 diagnosis 端點；roadmap K3a-d 勾選
- ⚠ `services/diagnosis/root_cause.py` 165 行（>150 提醒門檻）：單一職責完整（觸發+排序+附題），暫不拆分，K4c 補救路徑若復用再評估

---

## [2026-07-04] — feat(K2)：動態知識狀態追蹤 — EDF 對話重新驅動 BKT

### Added
- **K2a** migration `j6e7f8a9b0c1`：`concepts.edf_parent_tag` 欄位 + index + mapping seed（EDF 20 粗 tag 中 10 個對映 59 個影片 concept；課程介紹 3 個 NULL；STL/template/concurrency 等課綱未涵蓋 tag 照舊跳過）
- **K2a** `services/mastery/resolve.py`：三層 fan-out 解析（① tag 直接命中 → ② parent group 只更新該生已曝光組員 → ③ 全未曝光只更新組內 video_order 最小的入門 concept）——讓 Workspace 對話重新驅動 BKT，同時防止粗 tag 對話噪音淹沒 quiz / comprehension 精準信號；消除 tech-debt「EDF Mastery 連動暫時退場」
- **K2b** `GET /concepts/mastery` 加 `last_practiced_at`（K4 Coddy prompt 的時序信號；缺口分析後改為擴充既有端點、不新建 k-state API）
- **K2c 決策記錄**：暫不引入真 AST（tree-sitter/libclang）——LLM Evidence 已輸出等效信號；Phase 5 有行為資料後重評（記 tech-debt）
- 測試 +6（5 fan-out + 1 endpoint 欄位）→ **後端 524 tests 全綠**

### Changed
- `services/mastery/updater.py`：`update_mastery` 改走 resolve 三層解析 + 跨 tag 去重（同 concept 每次 evidence 只更新一次）；移除被取代的 `_get_concept_id_by_tag`
- 實機驗證：alembic upgrade 實跑 + mapping 分布查核（syntax-basic 20 / control-flow 11 / function-design 11 / ...共 59 對映）
- `docs/roadmap.md`：K2/K3 依缺口分析細化（K2b 改擴充既有 API、K3a 改 stateless 查詢設計）並勾選 K2a/b/c；`docs/api-spec.md` Knowledge Graph 段修正為實際路徑 `/concepts/*` + 欄位更新；`docs/tech-debt.md` EDF Mastery 項 ✅ + 新增 AST 決策記錄

---

## [2026-07-04] — feat(K1)：K-Graph 自適應學習引擎啟動 — 跨章多對多依賴 DAG

### Added
- **Phase 6-K 納入 roadmap**（功能規格書五大功能）：K1 跨章多對多圖 / K2 動態知識狀態 / K3 根源弱點定位 / K4 Coddy 自適應（吸收原 6-5 全部）/ K5 視覺改版（吸收原 6-6a/c/d）；執行順序 K1→K2→K3→K4→K5 依技術相依性排定
- **K1a** migration `i5d6e7f8a9b0`：curated 依賴 map（每 concept 1-3 個真實直接前置，依 C++ 教學相依性判斷）取代線性 PREREQUISITE 鏈 61 條 → **90 條多對多邊**；不變量：全邊 source.video_order < target.video_order（無環）、除 video 1 外每節點 ≥1 入邊（連通）；downgrade 可還原線性鏈
- **K1b** `services/graph/traversal.py`：`get_prerequisite_closure(db, tag, max_depth)` — 單查詢載全邊 + 記憶體 BFS 回溯 + 菱形去重，回傳 (concept, depth) 依 (depth, video_order) 排序；供 K3 根源診斷使用；5 個新測試（**後端 518 tests 全綠**）
- **K1c** 實機驗證：alembic upgrade 實跑 dev DB + SQL 驗證（90 prerequisite 邊 / cpp-47-recursion ← 25 if-else + 37 參數 + 38 回傳值 / 0 孤兒節點 / 0 反向邊）

### Changed
- `docs/roadmap.md`：**移除 6-5 / 6-6 段**（內容完整整併至 K4 / K1+K5，留整併說明）；已確認決策更新（知識圖譜重構決議標記完成、新增 Phase 6-K 決策）
- `docs/tech-debt.md`：「跨章節 PREREQUISITE 邊未標」✅ 消除（K1a）；「EDF Mastery 連動退場」cross-ref K2a；「Learn 頁 graph 版」併入 K5
- `docs/modules.md` Module 5 升級為 K-Graph 引擎描述；`docs/db-schema.md` 補邊資料現況注記
- 可行性檢查結論：schema 原生支援多對多（unique triple）、拓撲排序已處理 DAG、quiz select 的出度中心性加權在 DAG 下才真正生效（線性鏈時全部 out_degree=1 無區分度）——K1 為資料工程而非架構重寫

---

## [2026-07-04] — feat(6-R)：健壯性強化（架構審查）+ 移除教授抽查

### Added
- `backend/core/rate_limit.py`：per-user rate limit dependency（Redis INCR+EXPIRE 固定窗口，Redis 掛掉 fail-open 放行）；掛上 12 個 LLM 端點（chat interact / quiz generate+hint / quiz feedback / reflection create / comprehension epl+predict+variation 全系列）+ `/code/execute`；429 回 `RATE_LIMITED` + `detail.retry_after_seconds`
- `core/auth.py`：NextAuth token `exp` claim 驗證，過期回 401 `TOKEN_EXPIRED`（原本被竊 cookie 永久有效）
- `core/errors.py`：`unhandled_error_handler` 補 `logger.exception` traceback（原 500 完全無痕跡）；新增 `validation_error_handler` 把 422 轉統一 `{error, message, detail}` 格式
- `tests/test_rate_limit.py`（5 tests）+ auth exp / errors logging+422 / judge0 網路例外 / evidence schema / chat fail-safe / user 節流 共 14 個新測試 → **後端 513 tests 全綠**
- `docs/api-spec.md` 新增「標準錯誤格式」一節（全部 error code 對照表）

### Changed
- `services/judge0.py`：httpx 網路例外（ConnectError / Timeout）submit 階段轉 503 `JUDGE0_UNAVAILABLE`、polling 階段視同該輪失敗重試（原直接冒泡 500）
- `services/edf/evidence.py`：LLM 回傳合法 JSON 但不符 schema（ValidationError）→ 502 `LLM_PARSE_ERROR`（原冒泡 500）
- `services/chat.py`：**fail-safe 持久化** — user message 於 LLM 呼叫前先 commit，OpenAI 失敗不再連學生輸入一起 rollback；`list_sessions` count 改 `func.count()`（原全表載入）
- `services/user.py`：首登並發 race 防護（IntegrityError → rollback 重查）+ `last_login_at` 1 小時節流（原每個 authenticated request 都寫 DB）；lookup 改用 `google_id or sub`（修 google_id=None 永遠 miss 的邊界）
- `services/quiz/orchestrator.py`：`list_history` count 改 `func.count()`
- 容錯 swallow 全面補 `logger.warning`（chat / orchestrator / mastery_hook / quiz generate RAG fallback）
- `web/lib/api.ts`：401 統一重導 `/login`（原為 TODO；已在 /login 不重導避免迴圈）
- `web/app/api/[...path]/route.ts`：proxy 加 30 秒 `AbortSignal.timeout`，逾時回 504 `BACKEND_TIMEOUT`（原 backend 卡死時前端 request 無限懸掛）
- `.claude/rules/backend.md` 錯誤處理表補「Token 過期 / 網路層例外 / LLM schema」三列 + 容錯 swallow 必須留痕規則
- `docs/roadmap.md`：新增 6-R 段（8 項全勾）；**6-4 移除教授抽查改為自行品管**（實機批次跑 + deferred-ui 驗收保留）；Phase 7 前置條件加註 6-R 完成
- `docs/tech-debt.md`：新增 3 筆刻意延後項（OpenAI client 抽取 / 429 toast UI / LLM 降級快取）+ 教授抽查字樣同步修訂
- 既有 `test_user_service.py` 2 個測試配合節流行為改寫 + 新增節流內不寫 DB 測試

---

## [2026-06-23] — docs：新增 roadmap 6-6 知識圖譜優化（使用者反饋）

### Added
- `docs/roadmap.md` Phase 6 新增 **6-6 知識圖譜優化（視覺 + 核心機制）**：
  - 背景：使用者反饋 `/knowledge` 頁面視覺不佳；現況 62 節點僅線性 PREREQUISITE 鏈（58 條邊），fcose layout 呈現接近一條長鏈，不直觀。呼應既有決議「知識圖譜重構為 Phase 6 後續工作」與 tech-debt「跨章節 PREREQUISITE 邊未標」項目，擴大範圍納入學術研究調研
  - 6-6a：查 `docs/references.md` §5 學術資源尋找知識圖譜輔助學習的實證設計參考（Cytoscape.js 為 Tier 1 鎖定套件，僅調整用法不換套件）
  - 6-6b：跨章關鍵依賴重構多對多 PREREQUISITE 圖
  - 6-6c：依研究結論重新設計 stylesheet/layout，對照 frontend.md R1-R8 規則檢核
  - 6-6d：真人測試驗收（學生是否真能讀懂學習進度，不只是好看）
- `docs/tech-debt.md` 既有「跨章節 PREREQUISITE 邊未標」項目加註 cross-ref 至 roadmap 6-6
- 本次僅新增 roadmap 追蹤項目，未動程式碼

---

## [2026-06-23] — docs：新增 roadmap 6-5 Coddy 對話品質優化（使用者反饋）

### Added
- `docs/roadmap.md` Phase 6 新增 **6-5 Coddy（EDF Chat）對話品質優化**：
  - 背景：使用者實測後反饋 Coddy 反問語氣生硬不自然；且 RAG 是否查影片內容目前綁在 `services/edf/decision.py` 的 `use_rag = clamped_hint >= 2 and bloom >= ANALYZE` 門檻，而非「問題是否真的需要影片內容」
  - 6-5a：RAG 觸發條件改為內容相關性判斷（取代 hint_level 門檻寫死規則）
  - 6-5b：`services/edf/feedback.py` persona/preamble 語氣優化
  - 6-5c：真人測試驗收
- 本次僅新增 roadmap 追蹤項目，未動程式碼（依專案規範：單一最小任務、不擅自實作）

---

## [2026-06-23] — chore：清理未追蹤垂圾檔 + 新增 dev-start.sh

### Removed
- `web/next`、`web/web@0.1.0`：誤建空檔（疑為指令打錯產生），已刪除
- `.claude/scheduled_tasks.lock`：對應 PID 已不存在的過期 lock，已刪除

### Added
- `dev-start.sh`：本機一鍵啟動腳本（Colima → docker-compose → 等 Postgres → alembic current → uvicorn），路徑改用 `$(dirname "$0")` 可攜寫法

### Changed
- `.gitignore`：新增 `.claude/scheduled_tasks.lock`（runtime lock）與 `ScreenShot/`（本機暫存截圖，非專案文件資產）

---

## [2026-05-22] — Phase 6-3b ExercisesTab 題庫優先（GET /quiz/from-bank + 前端分流 fallback）

### Verified (2026-05-22 透過 `pytest -q` + `npx tsc --noEmit` + `npx eslint`)
- 後端 499 passed in 9.27s（原 488 + 新 11：bank 6 + route 5）
- 前端 TypeScript / ESLint 全綠
- Fallback path 直接驗證（DB 無 validated 題 → 預期跳 generate 流程）；命中題庫 path 延至 6-3a-3 / 6-4 實機跑出 grounded validated 題後驗

### Added
- **`backend/services/quiz/bank.py`** (45 行)：`pick_random_validated_question(db, concept_tag, exclude_question_ids?)`
  - 篩 `validated=True` + Python 端 filter `concept_tags` 含 tag（避開 JSON contains 跨方言差異）
  - 隨機抽用 `random.choice`（候選 n 不大）；無題回 `None`
  - `exclude_question_ids` 預留給未來「不重複曝光已答題」加強，本次前端未啟用
- **`GET /quiz/from-bank?concept_tag=...`** endpoint（api/routes/quiz.py）
  - 命中 → 200 + `QuestionForStudentOut`（復用 `from_question` mask 答案）
  - 無題 → 404 `QUESTION_BANK_EMPTY`，前端可 fallback
  - `concept_tag` 必填（FastAPI Query 預設驗證 → 422）
- **`web/lib/quiz.ts`**：`getQuestionFromBank(conceptTag)` helper
- **`web/components/learn/exercises-tab-views.tsx`** (58 行)：`IdleView` + `LoadingView`（純展示元件，由 exercises-tab.tsx 拆出避免主檔超 250 行門檻）
- **`backend/tests/test_quiz_bank.py`** (約 130 行)：6 個 service 單元測試
  - 命中題、無題、validated=False 不被抽中、不同 tag 不串題、exclude_question_ids 過濾、多次抽都符合條件
- **`backend/tests/test_quiz_route.py`** 加 5 個 endpoint integration 測試（test_from_bank_*）

### Changed
- **`web/components/learn/exercises-tab.tsx`**：
  - `Phase` type 加 `loading-bank` / `loading-generate`（取代原單一 `loading`）
  - `startExercise()`：先 `getQuestionFromBank` → catch `ApiRequestError(404, QUESTION_BANK_EMPTY)` → fallback `generateQuestion`；其他錯誤一律 humanize
  - `LoadingView` 改 prop-driven 文案：bank 顯示「查找題庫題目（< 1 秒）」/ generate 顯示「AI 正在生成題目（5-15 秒）」
  - 拆出 IdleView / LoadingView 至 exercises-tab-views.tsx（主檔 261 → 227 行，回到 < 250 健康水位）
- **`backend/services/quiz/__init__.py`**：export `pick_random_validated_question`
- **`backend/api/routes/quiz.py`**：212 → 237 行（< 250），新增 from-bank endpoint + 對應 import

### Implementation note
- **為什麼 endpoint 用 GET 而非 POST**：抽題是冪等讀取操作（每次隨機抽 1 題；非建立資源），語意上 GET 更合適；URL 中 `concept_tag=` 也便於除錯 / 觀察。
- **為什麼 random.choice 在 Python 端而非 SQL `ORDER BY RANDOM()`**：JSON contains（`concept_tags @> [tag]`）跨 SQLite/Postgres 寫法差異大；既然候選量 n ≤ 數十，先撈出再 Python random 是可攜的低成本選擇。未來流量大或 dedup 需要更複雜邏輯時可升級。

### Tech debt
- 已答題排除尚未啟用：service 已支援 `exclude_question_ids`，但前端 ExercisesTab 未維護「使用者已答題清單」；學生重複進同 unit 練習可能抽到同題（中短期可接受，列為 tech-debt）

### Tests
- 後端 499 tests 全綠（pytest -q 9.27s）
- 前端 typecheck + lint 全綠

### Health metrics
- `bank.py` 45 行（健康）
- `quiz.py` (routes) 237 行（< 250 ⚠ 門檻）
- `exercises-tab.tsx` 227 行（< 250；超 150 ⚠ 但與既有 261 同水位）
- `exercises-tab-views.tsx` 58 行（< 150）
- `test_quiz_bank.py` 約 130 行（測試檔）

### Deferred（已錨定）
- 命中題庫 path 真實驗收：延至 6-3a-3 / 6-4 實機跑出 grounded validated 題後 → roadmap 6-4a-deferred-ui 紀錄 / tech-debt 延遲驗收區
- Dedup 「不重複出已答題」：service `exclude_question_ids` 已預留 → 前端維護已答題清單後再啟用

---

## [2026-05-22] — Phase 6-3a-2 批次練習題生成 service + CLI（程式碼 + mock+DB 測試完成；實機跑延 6-4）

### Verified (2026-05-22 透過 `pytest -q`)
- `tests/test_quiz_batch_generator.py` 8 passed
- 全套 488 passed in 9.21s（原 480 + 新 8，無 regression）

### Added
- **`backend/services/quiz/batch_generator.py`** (217 行)：批次層
  - `generate_questions_for_concept(concept, question_types, bloom_level)` — per-concept 跑 N 題、每題 generate（grounded mode：`video_order=concept.video_order`）+ validate（retry max 2）
  - `generate_all(only, skip_existing, question_types, bloom_level)` — 入口；`skip_existing=True` 時跳過已有 ≥ N validated 題的 concept（用 `_count_validated_questions` 掃 `concept_tags` JSON array）
  - `list_target_concepts(only)` — `Concept.video_order IS NOT NULL` + 可選 video_order filter（與 6-2b 同策略，含 1-3 課程介紹）
  - dataclasses `QuestionAttempt`、`ConceptBatchResult`（含 `validated_count` property）
  - 預設 `DEFAULT_QUESTION_TYPES = (MULTIPLE_CHOICE, CODING)`、`DEFAULT_BLOOM_LEVEL = APPLY=3`
- **`backend/scripts/generate_unit_questions.py`** (124 行)：CLI
  - `--only N` 單一 video_order；`--force` 跳 skip_existing；`--dry-run` 只列 concept
  - 輸出 per-concept progress（marker：✅完整 / ⚠ partial / ❌全失敗 / ⏭️ skipped）+ summary（concepts / full success / partial / all-failed / skipped / total validated questions inserted）+ failed details
- **`backend/tests/test_quiz_batch_generator.py`** (約 270 行)：8 個 mock+DB 測試
  - per-concept 2 題全 validated → 入庫
  - validate concept_fits=False 兩次 retry 失敗 → 該題 rollback、不阻擋下一題
  - generate LLM_PARSE_ERROR → 該題直接 abort（不 retry）、不阻擋下一題
  - NO_VIDEO_ORDER concept → 422 防呆
  - `generate_all` `skip_existing=True` 跳過已有足量 validated 題的 concept
  - `--force`（skip_existing=False）強制重生
  - `list_target_concepts` only 過濾 + 排除無 video_order
  - `ConceptBatchResult.validated_count` property

### Fixed / Implementation note
- **ORM attr expire 問題**：rollback / commit 後 SQLAlchemy 預設 `expire_on_commit=True` 會把 ORM 物件 attr 標 expired，下次 access 觸發 async lazy reload；在 retry loop 內每次 IO 後加 `await db.refresh(concept)` 確保下一輪訪問 `concept.video_order / .tag / .difficulty_level` 時不會拋 `MissingGreenlet`。

### Changed
- **`docs/roadmap.md`** 6-3a-2 勾選 + 補執行成本估計（62 × 2 × 2 LLM call ≈ 250-500k token / $5-15 USD）

### Tests
- 後端 488 tests 全綠（pytest -q 9.21s）

### Health metrics
- `batch_generator.py` 217 行（< 250 ⚠ 門檻）
- `generate_unit_questions.py` 124 行（< 150 ⚠ 門檻）
- `test_quiz_batch_generator.py` 約 270 行（測試檔無門檻；逐塊獨立）

### Deferred（已錨定）
- 6-3a-3 實機 LLM 全跑：延至 6-4a 與 6-2b 批次跑合併執行
- 重複避免目前用「已 validated 題數 ≥ requested」判斷；題目雖然 grounded 但語意可能近似，未做相似度 dedupe（如有重複可手動 invalidate）

---

## [2026-05-22] — Phase 6-3a-1 grounded mode 接入 `generate_question`（程式碼 + mock 測試完成；批次 script 與實機跑延 6-3a-2 / 6-4）

### Verified (2026-05-22 透過 `pytest -q`)
- `tests/test_quiz_generate.py` 12 passed（含 4 個新 grounding 測試）
- 全套 480 passed in 9.23s（原 476 + 新 4，無 regression）

### Added
- **`backend/services/quiz/generate.py:_GROUNDING_RULES`** — 3 條 grounding rule（題目情境 / 嚴禁發明 / 字幕不足時降難度）
- **`backend/services/quiz/generate.py:_fetch_grounded_chunks_for_video`** — 包 `get_chunks_by_video_order`，失敗 fallback 空 chunks（同 semantic path 容錯）
- **`backend/tests/test_quiz_generate.py`** 新增 4 測試：
  - `test_grounded_mode_uses_video_chunks_and_skips_semantic_retrieve` — `video_order` 提供時 `get_chunks_by_video_order` 被呼叫、`retrieve_chunks` 不被呼叫；TRANSCRIPT header + chunk 內文進 user prompt
  - `test_grounded_mode_injects_grounding_rules_into_system_prompt` — system prompt 含「Grounding 規則」+「嚴禁發明字幕未提到的程式碼」
  - `test_non_grounded_mode_preserves_legacy_path` — `video_order=None` 走 `retrieve_chunks`、prompt 不含 grounding 規則（backward compat）
  - `test_grounded_retrieve_failure_does_not_block_generation` — `get_chunks_by_video_order` 拋例外仍能出題（fallback 空 chunks）

### Changed
- **`backend/services/quiz/generate.py:generate_question`** 簽名加 `video_order: int | None = None`；提供時 grounded mode（不需改 orchestrator / API；學生現生題路徑不變）
- **`backend/services/quiz/generate.py:_build_system_prompt`** 加 `grounded: bool` 參數，true 時 append `_GROUNDING_RULES`
- **`backend/services/quiz/generate.py:_build_user_prompt`** 加 `grounded: bool` 參數，true 時 user header 改為「以下 TRANSCRIPT 為教授實際 YouTube 影片字幕（依時間順序）」
- **`backend/tests/test_quiz_generate.py:patched_llm`** 擴充：同時 patch `retrieve_chunks` + `get_chunks_by_video_order`；`yield` 回 3 個 mock 供新測試 assert 呼叫行為
- **`docs/roadmap.md`** 6-3a 拆 3 子項：6-3a-1（程式碼，本次完成 ✅）/ 6-3a-2（批次 script，next）/ 6-3a-3（實機跑，延 6-4）

### Tests
- 後端 480 tests 全綠（pytest -q 9.23s）

### Health metrics
- `generate.py` 221 → 248 行（< 250 ⚠ 門檻；曾觸頂 268 行，主動壓縮 docstring + 縮短 grounding rules 字串後回到健康水位）
- `test_quiz_generate.py` 250 → 359 行（測試檔，無 ⚠ 強制門檻；逐塊獨立可讀）

### Deferred（已錨定）
- 6-3a-2 批次 script + 6-3a-3 實機跑：roadmap 6-3 子項已標
- 學生現生題 backward compat：本次未動 `orchestrator.generate_for_student`，學生路徑仍走 semantic RAG；待 6-3b 改造 ExercisesTab 時再決定是否切到題庫優先

---

## [2026-05-22] — Phase 6-2e 程式碼完成：摘要 tab 渲染 grounded key_points + citation 標籤（fallback 已驗證 / grounded 狀態延至 6-4 驗收）

### Verified (2026-05-22 透過 `npx tsc --noEmit` + `npx eslint`)
- TypeScript / ESLint 全綠；既有 lazy-seed empty 形狀仍顯示「重點摘要尚未匯入」placeholder（與 6-2c/d 行為一致）
- grounded 主路徑（`needs_more_source` notice / key_points bullet + citations）：**因 DB 尚無任何 promoted `summary` object 形狀**，延至 Phase 6-4a-deferred-ui 合併驗收

### Added
- **`web/components/learn/summary-tab.tsx`** (約 115 行)：grounded summary 渲染元件
  - 四段狀態：grounded 且 `needs_more_source=true` → reason notice；grounded 且 `key_points` 非空 → bullet list + citation 列表；舊 `summary: string` → legacy fallback；都沒有 → empty placeholder
  - citation 採靜態時間戳 + 節錄文字（不嵌 YT player，提示使用者回概念 tab 點 citation）

### Changed
- **`web/lib/learning.ts`**：新增 `SummaryContent` 介面（與後端 `content_generator.py:Summary` 對齊：`needs_more_source` / `reason` / `key_points` / `citations`）；`UnitContent.summary` 由 `string` 擴為 `string | SummaryContent`，相容舊 lazy seed 與 promote 後形狀
- **`web/components/learn/unit-content.tsx`**：移除 inline `SummaryTab` + `EmptyTab`（共 19 行），改 import `SummaryTab` from `./summary-tab`；保持 ≤ 150 行健康水位
- **`docs/roadmap.md`**：勾選 6-2e；6-4a-deferred-ui 子項「**6-2e grounded path**」補完內容說明（驗收 needs_more_source notice + key_points bullet 渲染）

### Tests
- 後端無新增測試（API 與 schema 未動）；後端 476 tests 全綠
- 前端 TypeScript check 通過 (`npx tsc --noEmit` exit 0) + ESLint 通過

### Health metrics
- `summary-tab.tsx` 約 115 行（< 150 ⚠ 門檻）；`unit-content.tsx` 154 行（仍超 ≤150 警戒線少許，與 6-2d 完成時同水位，本任務未惡化）
- `learning.ts` 新增 7 行 interface + 1 行 union 擴充，未跨 ⚠ 門檻

---

## [2026-05-22] — Phase 6-2d 程式碼完成：範例 tab 渲染 grounded code + 「在 Workspace 開啟」轉場（fallback 已驗證 / 卡片狀態延至 6-4 驗收）

### Verified (2026-05-22)
- 使用者於 Unit 1「什麼是程式語言」範例 tab 看到「程式範例尚未匯入」placeholder — fallback 分支運作正確
- 卡片列表（grounded code_examples）+ 「在 Workspace 開啟」轉場 + 一次性消費 sessionStorage：**因 DB 尚無任何 promoted `code_examples` JSON 而無法本次驗收**；延至 Phase 6-4 教授抽查 + 實機 LLM 批次跑完後合併驗收

### Deferred verification anchored at 3 places (避免被遺忘)
- `docs/roadmap.md` — 6-4a 下新增 `6-4a-deferred-ui` 子 checkbox，明列 6-2c / 6-2d 待補驗的 grounded 主路徑（含 sessionStorage 一次性消費關鍵驗收步驟）
- `docs/tech-debt.md` — 新增「延遲驗收（Phase 6-2 → 6-4 必跑）」段，含失敗排查指引（`pending-workspace-code.ts` removeItem / `workspace/page.tsx` useState lazy initializer）
- `CLAUDE.md` 當前狀態 — 6-2c / 6-2d 標記改為「✅程式碼完成 + fallback 已驗」，下一步段強調「6-4a-deferred-ui 必跑」

### Added
- **`web/components/learn/examples-tab.tsx`** (147 行)：grounded code examples 渲染元件
  - 四段狀態：`needs_more_source=true` → reason notice；有 grounded examples → 卡片列表；舊形狀 `examples: string[]` → legacy fallback；都沒有 → empty placeholder
  - `ExampleCard`：title + code block（mono / bg-inset）+ explanation + optional citation 標籤 + 「在 Workspace 開啟」按鈕
  - citation 採靜態時間戳 + 節錄文字（不嵌 YT player，避免每 tab 各跑一個 IFrame）；要跳影片時間請回概念 tab 點 citation
- **`web/lib/pending-workspace-code.ts`** (53 行)：sessionStorage helper for 跨頁攜帶程式碼
  - `setPendingWorkspaceCode(code)` / `consumePendingWorkspaceCode()`（讀完即清，避免下次重整誤覆蓋）
  - 復用 `active-reflection.ts` pattern（CustomEvent 同 tab 通知 + SSR safe try/catch）

### Changed
- **`web/lib/learning.ts`**：新增 `CodeExample` / `CodeExamples` 介面（與後端 `content_generator.py:CodeExample/CodeExamples` 對齊）；`UnitContent` 加 optional `code_examples?: CodeExamples`
- **`web/components/learn/unit-content.tsx`**：移除 inline `ExamplesTab`（17 行），改 import `ExamplesTab` from `./examples-tab`；檔案 188→173 行（更接近 ≤ 150 健康水位）
- **`web/app/(app)/workspace/page.tsx`**：mount 時用 `useState` lazy initializer 消費 `consumePendingWorkspaceCode()`，作為 `<CodeEditor initialValue={...}>` 一次性 prop；後續 re-render 不重複 consume

### Tests
- 後端無新增測試（API 與 schema 未動）；後端 476 tests 全綠
- 前端 TypeScript check 通過 (`npx tsc --noEmit` exit 0)
- 前端無 component test 基建（沿用 Phase 1-6 既定策略：UI 由使用者驗證）

### Why
6-2d 為 NotebookLM grounded 模式的「程式範例 tab」前端呈現：完成此 task 後使用者進入單元頁範例 tab 即可看到 LLM 從字幕生成的 1-3 個 C++ 程式範例 + 一鍵「在 Workspace 開啟」即時上手實驗。citation 與概念 tab 結構一致，讓學生能回溯字幕出處。配合 6-2c 概念 tab + 後續 6-2e 摘要 tab，三段 grounded 內容呈現基線完成。

### How to verify (使用者待測)
1. 前端 dev 環境（`npm run dev`）登入 → 進 Learn 頁 → 點開任一單元 → 切到「範例程式」tab
2. 若該單元 `learning_units.content.code_examples` 已有 promoted 資料：
   - 應顯示卡片列表，每張卡片含標題 + 程式碼 + 說明 + 出處（時間戳+節錄）+ 「在 Workspace 開啟」按鈕
3. 點任一範例的「在 Workspace 開啟」→ 路由跳 `/workspace` → 編輯器應載入該範例程式碼（取代 default Hello World）
4. 在 Workspace 內手動 navigate 回去再進來，編輯器應**不會**再次被該範例覆蓋（一次性消費）
5. 若該單元尚未 promoted（多數 unit 目前如此）：應顯示 empty placeholder 或舊形狀 fallback

## [2026-05-22] — Quiz cold-start fallback robust 補強（V2 cpp-XX schema 兼容）

### Changed
- **`backend/services/quiz/orchestrator.py:_pick_target_concept`** 改為兩段 fallback：
  1. 先查 `COLD_START_FALLBACK_TAG`（V1 schema 兼容；測試環境直接 seed 此 tag 仍可用）
  2. 若無，動態查 `difficulty_level` ASC + `video_order` ASC 取最低難度且最前序 concept
  3. 兩段都失敗才回 503 `QUIZ_UNAVAILABLE`

### Tests
- **`backend/tests/test_quiz_route.py:test_generate_cold_start_dynamic_fallback_when_no_legacy_tag`** 新增：seed `cpp-04-first-program`（difficulty=1, video_order=1）+ `cpp-05-syntax`（difficulty=1, video_order=2）+ `cpp-25-if-else`（difficulty=2）；不含 `syntax-basic` legacy tag；驗證 cold-start 取到 `cpp-04-first-program`
- 後端 476 tests 全綠

### Why
V1 cold-start 仰賴固定 tag `syntax-basic`，但 V2 cpp-XX 章節制 seed（62 部影片 concept）不含此 tag；無弱項 + 無 legacy tag 時 prod 會直接回 503。動態 fallback 讓部署初期（沒有任何 mastery 紀錄）的學生也能正常觸發出題。

## [2026-05-22] — Phase 6-2c 使用者驗證通過（YT 播放 + citation 跳轉 + grounded markdown 渲染正常）

### Verified
- 使用者於本機 dev 環境登入 → 進 Learn 頁 → 點開已 PATCH `video_youtube_id` 的單元，確認：
  - YT IFrame player 載入並可播放
  - grounded markdown 內容正確渲染（react-markdown + remark-gfm）
  - citation 列表點擊可呼叫 `player.seekTo` 跳到對應 timestamp
- 6-2c 正式 close；`docs/roadmap.md` 該行勾選 `[x]`；`CLAUDE.md` 當前狀態更新「下一步：6-2d 範例 tab」

### Next
- 6-2d 範例 tab：渲染 LLM 生成的程式碼範例 + 「在 Workspace 開啟」按鈕（復用 Phase 2-5d sessionStorage）+ citation 標示

## [2026-05-22] — 設計反轉：video_order 1-3（課程介紹）加回學習路徑

### Changed
- **新 alembic migration `h4c5d6e7f8a9_seed_intro_video_prerequisites.py`**：補 3 條 PREREQUISITE 邊
  - `cpp-01-language-intro` → `cpp-02-cpp-overview`
  - `cpp-02-cpp-overview` → `cpp-03-devcpp-install`
  - `cpp-03-devcpp-install` → `cpp-04-first-program`
  - 完整鏈：1→2→3→4→...→62（共 61 條 prerequisite 邊）
- **`backend/services/learning/generator.py`**：移除 `EXCLUDED_FROM_PATH_CATEGORIES` 常數與 `notin_` 過濾條件；`_fetch_concepts` 改為純 `select(Concept)` + optional category filter
- **`backend/services/learning/batch_generator.py`**：移除 EXCLUDED 過濾；`list_target_concepts` 改為只過濾 `video_order IS NULL`；docstring 更新「涵蓋全部 62 部（含 1-3）」
- **保留 `category="課程介紹"` 不變**：未來知識圖譜頁可用此 category 做 styling 區分（不再做路徑過濾用途）
- **`docs/roadmap.md`**：6-1c 條目 + 「已確認決策」段 1-3 處理方式 + Phase 6 開頭「Concept 範圍」說明 — 三處同步修訂

### Tests
- **`backend/tests/test_learning_generator.py`**：
  - `test_intro_category_concepts_excluded_from_path` → `test_intro_category_concepts_included_in_path`（assert 三筆 concept 全部進路徑）
  - `test_all_intro_category_raises_422` → `test_path_with_only_intro_category_still_succeeds`（assert 不再拋 422，能正常生成）
- **`backend/tests/test_batch_generator.py:test_list_target_concepts_filters_intro_and_no_video_order`** → `test_list_target_concepts_includes_intro_filters_no_video_order`（assert 課程介紹也會被批次生成）
- alembic upgrade head 套用成功；後端 476 tests 全綠

### Why
原 6-1c 把 1-3 列為「選看」類不進路徑；2026-05-22 使用者決定 1-3 教學內容（語言介紹 / C++ 概述 / DevC++ 安裝環境）對線性學習路徑而言是必要前置，應強制要學。加 PREREQUISITE 邊比「移除 filter 讓 1-3 與 4 並列 in_degree=0」更穩定，保證路徑順序固定為 1,2,3,4,...,62。

### Migration
本機 dev 環境：`cd backend && alembic upgrade head`
部署環境（Phase 7）：deployment 流程自動跑 `alembic upgrade head`，無額外動作

## [2026-05-22] — Phase 6-2c 程式碼完成：概念說明 tab 嵌入 YT IFrame player + grounded markdown + citation 跳轉（待使用者 UI 驗證）

### Added
- **`web/components/learn/youtube-player.tsx`** (142 行)：YT IFrame Player API wrapper
  - lazy load `https://www.youtube.com/iframe_api`（全域 script 只 inject 一次，多 player 共用）
  - `forwardRef` + `useImperativeHandle` 暴露 `seekTo(seconds)`；player 尚未 ready 時暫存待 `onReady` 補跳
  - `videoId` 變更時 `cueVideoById` 重置（換單元不重建 iframe）
  - 元件卸載時 `destroy()` 防 leak
- **`web/components/learn/concept-tab.tsx`** (229 行)：grounded 內容渲染元件
  - 三段狀態：無 youtube_id → placeholder；有影片無 grounded → player + 簡介；完整 → player + Markdown + citation 列表
  - `ReactMarkdown` + `remarkGfm` 渲染 LLM 生成的 `concept_explanation.markdown`；自訂 12 個 element class（無 `@tailwindcss/typography` 仍維持可讀性）
  - `parseTimestampStart()` 解析 `mm:ss` / `mm:ss-mm:ss` / `hh:mm:ss` → 秒數；citation 列表按鈕點擊呼叫 `player.seekTo`
- **`web/components/learn/unit-action-bar.tsx`** (85 行)：從 unit-content.tsx 拆出 NavButton + ActionButton（讓 unit-content.tsx 降至 191 行 < 250 行硬上限）

### Changed
- **後端 `backend/api/routes/learning.py:UnitOut`** 新增 `video_youtube_id: str | None` / `video_duration_seconds: int | None`，由 concept JOIN 帶出
- **後端 `backend/services/learning/queries.py:UnitWithConcept`** dataclass 同步擴充兩欄
- **前端 `web/lib/learning.ts`**：`Unit` 加 `video_youtube_id` / `video_duration_seconds`；`UnitContent` 加 optional `concept_explanation`（grounded 形狀，含 markdown + citations）；新增 `Citation` / `ConceptExplanation` 介面
- **前端 `web/components/learn/unit-content.tsx`**：原 inline `ConceptTab` + `VideoPlayerPlaceholder` 移除，改 import `ConceptTab`；NavButton + ActionButton 改 import 自 unit-action-bar
- **新增 npm 套件**：`react-markdown@^10.1.0` + `remark-gfm@^4.0.1`

### Tests
- **`backend/tests/test_learning_route.py:test_get_path_returns_units_in_order`** 補斷言 `video_youtube_id` / `video_duration_seconds` 直通 UnitOut；`_seed_concepts` helper 容許 spec 帶這兩欄
- 後端 476 tests 全綠（無新增測試檔；既有 route 測試擴充即可覆蓋 6-2c 新欄位）

### Why
6-2c 為 NotebookLM grounded 模式的「概念說明 tab」前端呈現：完成此 task 後使用者進入單元頁即可看到實際 YT 影片 + LLM grounded markdown + citation timestamp 跳轉，達成「LLM 生成內容必須引用 transcript 出處 + 學生可立即比對影片真實時間點」的設計目標。6-2b 已完成批次生成 + promote helper，配合本任務後即可端到端跑通 grounded 內容生成 → 前端呈現。

### How to verify (使用者待測)
1. 前端 dev 環境（`npm run dev`）登入 → 進 Learn 頁 → 點任一已 PATCH `video_youtube_id` 的單元（video_order 4-62）
2. 確認概念說明 tab 顯示 YT player 並可播放
3. 若該 unit `content.concept_explanation` 有資料 → 應顯示 markdown + citation 列表；點 citation 按鈕應跳轉至對應時間點
4. 若 unit 仍是空 content → 應顯示 player + 「概念簡介」fallback 文字

## [2026-05-13] — chore(web): middleware → proxy 遷移（Next.js 16 deprecation）

### Changed
- **`web/middleware.ts` → `web/proxy.ts`**：Next.js 16 將 `middleware` 檔案規範改名為 `proxy`，原檔仍可運作但會發 deprecation warning。export 從 `auth as middleware` 改為 `auth as proxy`，`config.matcher` 規格不變。

### Why
`npm run dev` 出現 deprecation 警告 `The "middleware" file convention is deprecated. Please use "proxy" instead.`。Next.js 官方理由：避免與 Express middleware 概念混淆，且明確標示其位於 Edge Runtime 上的 proxy 性質。

## [2026-05-13] — docs: dev-setup.md 新增 Windows (PowerShell) 啟動章節

### Added
- **`docs/dev-setup.md` §1B**：Windows 對應啟動流程
  - 最小啟動（DB + Redis）/ 完整開發（後端 + 前端三 terminal）/ 收工關閉 三段 PowerShell 指令
  - Windows 與 macOS 對照表（路徑、Docker daemon、venv 啟動、shell 語法）
  - 標註 Windows 路徑為 `C:\Users\hao\Desktop\Projects\...`（複數 Projects），與 macOS `Project`（單數）不同
- **`docs/dev-setup.md` §1**：標題加註 `(macOS / 已裝完工具)` + 開頭指引「Windows 環境見 §1B」

### Why
原 §1 僅 macOS / Colima 流程；Windows 環境 session 啟動時無對應指引。

## [2026-05-08] — Phase 6-2b 程式碼完成：grounded 批次生成 + staging table + retry + promote helper（待使用者實機驗證）

### Added
- **`backend/services/rag/retrieve.py`** 擴充：新 `get_chunks_by_video_order(video_order)` 直接 SQL 查 `data_codedge_rag.metadata_->>'video_order'`，依 `start_time_seconds` 排序回傳該 video 完整字幕 chunks（非語意 top-k，避免跨 video 污染與順序錯亂）
- **`backend/services/learning/batch_generator.py`** (251 行)：批次生成核心
  - `generate_for_concept(db, concept) -> GenerationResult`：retrieve → generate_unit_content → UPSERT staging
  - `_generate_with_retry`：transient 錯誤（LLM_UNAVAILABLE / LLM_PARSE_ERROR）退避重試 max 3 次；非 transient 直接拋
  - `_aggregate_needs_more_source` / `_flatten_notes`：3 section 任一 flag → row 標 True；reasons 串接成 `notes` 給 6-4 抽查介面用
  - `list_target_concepts`：自動過濾 `EXCLUDED_FROM_PATH_CATEGORIES=("課程介紹",)` + 缺 `video_order` 的 concept
  - `generate_all(db, only=None, skip_existing=True)`：批次入口；預設跳過已 approved 的 concept 避免覆蓋審查通過內容
  - SELECT-then-INSERT/UPDATE 取代 PG dialect on_conflict（保持 SQLite 測試相容）
- **`backend/services/learning/unit_content_promote.py`** (58 行)：6-4 抽查通過後 `promote_concept(db, concept_id) -> int` 把 staging.content 寫入該 concept 對應的所有 `learning_units.content`；強制 status='approved' 才執行
- **`backend/alembic/versions/g3b4c5d6e7f8_create_unit_content_staging.py`**：staging 表 migration
  - schema：concept_id UNIQUE / content JSON / status CHECK ('pending', 'approved', 'rejected') / needs_more_source / notes / attempt_count / model_used / generated_at / reviewed_at
  - 雙索引：status / needs_more_source（給 6-4 抽查介面 filter）
- **`backend/models/unit_content_staging.py`**：對應 ORM + `StagingStatus` enum
- **`backend/scripts/generate_unit_content.py`** (90 行) CLI：`--only N` / `--force` / `--dry-run`；摘要列印 success / skipped / needs_more_source / failed
- **`backend/tests/test_batch_generator.py`** (~330 行)：18 個新測試
  - pure helpers ×3（aggregate / flatten_notes 兩種情境）
  - retry 機制 ×3（second-attempt 成功 / 連 max retries / 非 retryable 立即拋）
  - generate_for_concept ×4（成功寫 staging / 失敗不寫 / 缺 video_order 422 / partial needs_more 聚合）
  - UPSERT ×1（重生時 reset reviewed_at + status）
  - list_target_concepts / generate_all ×4（過濾 / only filter / skip approved / force regenerate）
  - promote_concept ×3（成功 / pending 422 / 缺 row 404）
- 全套 backend 從 458 → **476 tests 全綠**

### Design 亮點
- **per-concept 不 per-unit**：1 concept N user units 共用 grounded content；staging 用 `concept_id UNIQUE`，promote 時一次更新所有相關 units
- **needs_more_source vs retry 互斥**：retry 處理「LLM 失敗」（網路 / parse），needs_more_source 處理「資料不足」（字幕短 / 偏題）
- **vendor-neutral upsert**：避開 PG dialect `on_conflict_do_update`，用 SELECT-then-INSERT/UPDATE 維持 SQLite 測試相容；UNIQUE(concept_id) 仍由 schema 強制
- **promote 與 generate 拆檔**：6-4 觸發的後段流程獨立，不與 batch generation 耦合；保持單一檔案 ≤ 250 行硬限

### Sync
- migration `g3b4c5d6e7f8` 已 apply 至 dev DB
- `data_codedge_rag` retrieve 對齊 6-1e ingest 時寫入的 `video_order` / `start_time_seconds` metadata
- dry-run 驗證：59 concept(s) would be processed（v04-v62），課程介紹 v01-v03 自動排除

### 待使用者驗證
- ⏳ 實際批次跑 1 部影片（建議 `--only 47` 遞迴）驗證 LLM 生成品質 + staging 寫入
- ⏳ 全 59 部批次跑（成本估 $5-10 USD）後檢查 needs_more_source 比例

### Why
6-2a 完成 prompt + 模型驗證後，6-2b 把它接到實際 RAG infrastructure：對每 concept 用 video_order metadata filter retrieve 該影片字幕 → call generate_unit_content → 落到 staging 供 6-4 教授抽查。staging 表設計為 1 concept 1 row（不依賴用戶），審查通過後 promote 一次更新所有用戶的對應 unit。

---

## [2026-05-08] — Phase 6-2a 完成：grounded prompt template + Pydantic 模型 + 13 mock-LLM 測試

### Added
- **`backend/services/learning/content_generator.py`** (235 行)：3 個 section 生成 function
  - `generate_concept_explanation` / `generate_code_examples` / `generate_summary`：各自獨立呼叫 LLM，回傳對應 Pydantic 模型
  - `generate_unit_content`：orchestrator，依序呼叫 3 個 section
  - `_call_llm_json` 共用 helper：OpenAI `json_object` mode + temperature 0.3 + Pydantic validate + 503/502 分層錯誤
- **Pydantic 輸出模型** 6 個：`Citation` / `ConceptExplanation` / `CodeExample` / `CodeExamples` / `Summary` / `UnitContent`，皆內建 `needs_more_source` + `reason` 欄位作為 graceful degradation
- **`tests/test_content_generator.py`** (~250 行)：13 個 mock-LLM 單元測試
  - 成功路徑 ×3（3 種 section 各自正確解析）
  - needs_more_source 路徑 ×2（transcript 不足時 LLM 回 true，content 留空）
  - 失敗路徑 ×3（503 LLM_UNAVAILABLE / 502 invalid JSON / 502 schema 違反）
  - Grounding 機制 ×3（context_block 真的注入 chunks / 空 chunks 自動引導 / chunks 確實傳到 LLM）
  - Orchestrator ×1（generate_unit_content 確實呼叫 3 次）
  - Pydantic 驗證 ×1（Citation excerpt 字數上限）

### Design 亮點
- **Grounding 雙重把關**：prompt 5 條絕對規則 + Pydantic 嚴格 schema；LLM 回 hallucinate 直接被 502 攔下
- **needs_more_source 機制**：每個 section 獨立判斷（concept ok 但 examples 沒料 → 只 examples needs_more）；不全有全無
- **citation 嵌入 markdown**：LLM 在 markdown 中內嵌 `[mm:ss]`，前端顯示時可解析為跳轉連結
- **caller 解耦**：generate function 只接 pre-fetched chunks，不自己呼叫 retrieve；6-2b 才負責 video_order metadata filter

### Sync
- `docs/roadmap.md` Phase 6-2a 標 [x] 並寫入完成細節
- `CLAUDE.md` 進度更新

### Why
依 Phase 6 NotebookLM 模式設計（2026-05-07 確認），LLM 生成 unit content 必須 grounded 在 Whisper transcript 上、禁止 hallucinate。本次完成的是 prompt 設計 + 模型 + 測試的「設計與驗證」階段；6-2b 將實際呼叫此 service 為 62 個 unit 批次生成 content。

---

## [2026-05-08] — Phase 6-1e 完成：Whisper 全 62 部 transcript + 二次審核 + 861 chunks 入 RAG（NotebookLM 核心就緒）

### Why A 方案改 B1
原計畫 A（yt-dlp 抓 zh-Hant 自動字幕）**徹底失敗**——6/6 樣本影片皆 "no automatic captions, no subtitles"（教授頻道未開或 YT 未生成）。改採 B1（OpenAI Whisper API），實測品質高（教授名「黃國豪」抓對；C++/devc++/Cout 等術語多數正確），唯一系統性錯辨「黃國昊」（同音字 hào），由二次審核 corrections.json 全域替換解決。

### Added — 4 個 script + 配置 + 資料
- **`backend/scripts/transcribe_videos.py`** (~190 lines)：yt-dlp 抓 audio + OpenAI `whisper-1` API；idempotent（skip 已存 transcripts）+ 成本上限保護（COST_CAP_USD=5）+ prompt 注入 title_zh 提升技術術語準度
- **`backend/scripts/apply_corrections.py`** (~120 lines)：corrections.json 兩層替換（global + per_video segment-id）→ transcripts_corrected/；保留 raw 不動
- **`backend/scripts/flag_transcripts.py`** (~140 lines)：GPT-4o-mini 自動掃可疑段落（type=term/semantic/repetition + confidence 0-1）→ issues_proposal.json；不誤報優於不漏報
- **`backend/scripts/ingest_transcripts_rag.py`** (~180 lines)：60 秒時間視窗分組 → LlamaIndex Document（text 含 `[mm:ss]` timestamp markers）→ pipeline.arun → 寫入 data_codedge_rag；--reset 旗標可砍重來
- **`data/teaching_content/corrections.json`**：12 條 global_replacements + per_video（目前空，留給 6-4 教授抽查補）
- **`data/teaching_content/transcripts/`**：62 個 raw Whisper JSON（3.4 MB）
- **`data/teaching_content/transcripts_corrected/`**：62 個套用 corrections 後的 JSON
- **`data/teaching_content/issues_proposal.json`**：209 個 LLM-flagged issues 的完整審核清單（68 KB）

### Results
- **Whisper batch**：62/62 全成功；總時長 7.2 hr → 成本 $2.621 USD
- **Flag scan**：209 issues（term ×152 / semantic ×48 / repetition ×9）；高 confidence ≥0.9 共 41 個
- **採納修正**：12 條 global（黃國昊×31, Double×17, Cout×8, 黃國華×8, ioString×3, Void×2, iostring×1, WCHART×1, objective oriented×1 + 預防性 IOStream / objective-oriented）；per_video 0 條（保留給 6-4 教授抽查）
- **RAG 入庫**：62 documents 行 + **861 chunks** 寫入 data_codedge_rag；每 chunk metadata 含 video_order / youtube_id / title_zh / start_time_seconds / end_time_seconds / source_type
- **Spot retrieve 驗證**：4/4 query 命中 expected video（遞迴→v47 / 指標→v51 / 物件導向→v59 / 階乘→top-3 含 v47）
- 總成本 6-1e: ~$2.69（Whisper $2.621 + Flag $0.07 + Embeddings $0.002）

### 設計亮點
- **不破壞原始**：raw transcripts 永不修改；錯誤定位 + 重跑 apply 都很方便；可重複迭代 corrections
- **Timestamp markers 嵌入 chunk text**：LLM 在 6-2 生成時可直接抽出 `[mm:ss]` 做 citation，不用查 metadata（雖然 metadata 也保留 start/end_time_seconds）
- **二次審核機制**：global 解決系統性錯誤（一條 fix 多影片）；per_video 留給 6-4 抽查階段針對性修
- **Reset & re-ingest 高效**：發現「黃國華」漏網後，加 1 條 global → re-apply → --reset + re-ingest 全程 < 2 min

### Sync
- `docs/roadmap.md` Phase 6-1e/f 標 [x] 並寫入完成細節
- `CLAUDE.md` 進度更新：6-1 整節完成
- `.gitignore` 新增 `data/teaching_content/audio_cache/` 排除（transient）

---

## [2026-05-07] — Phase 6 升級為 NotebookLM grounded 模式 + 6-1a/b 完成

### Changed（roadmap Phase 6 大幅細化）
- **採 NotebookLM grounded 模式**（核心架構決策）：所有 LLM 生成的 unit content / 練習題必須 grounded 在教授實際 YT 影片字幕上，禁止 LLM 自由發揮。Source = YT 自動字幕（A 方案，零成本，`yt-dlp --write-auto-subs`），品質不夠的 unit 在 6-4 抽查階段評估升級到 Whisper 重 transcribe（B 方案）
- **Concept 範圍 59 → 62**：video_order 1-3（課程簡介、環境安裝、語言簡介）加回為 concept；標記 `category="課程介紹"` **不參與 PREREQUISITE 鏈**（learning_path generator 過濾此 category，知識圖譜頁仍顯示但 styling 區分）
- **Phase 6-1 拆細**（原 6-1a/b/c → 6-1a~6-1f 共 6 子任務）：
  - 6-1a 教授交付 playlist URL ✅（2026-05-07 完成，`PLJDZAE4d-ihqvGtBMhgMv8Zp6Tv6D1l-M`，62 部影片完整對齊）
  - 6-1b fetcher script 已寫 + 產 59 列 CSV ✅（`backend/scripts/fetch_playlist_metadata.py`；title_zh 與 DB name_zh 59/59 完全一致）
  - 6-1b+ 待擴充 fetcher EXPECTED 1-62 + 重產 62 列 CSV
  - 6-1c 待加 video 1-3 concept seed migration
  - 6-1d 待開發 PATCH script + 執行寫入 DB
  - 6-1e 待開發字幕 RAG ingest（NotebookLM 核心）
  - 6-1f 待同步 tech-debt
- **Phase 6-2/6-3 升級為 grounded 版本**：prompt template 強制引用 transcript chunks + timestamp citation；禁止引入字幕未出現的概念；不足以生成時回 `needs_more_source=true` 而非 hallucinate

### Added
- `backend/scripts/fetch_playlist_metadata.py`（156 行，yt-dlp wrapper，含對齊驗證 + 缺漏報告）
- `data/teaching_content/videos.csv`（59 列；待擴充 62 列）
- `已確認決策` 加 3 條：NotebookLM 模式、62 個 concept 範圍、知識圖譜重構為後續工作
- `tech-debt.md` 新增「video 1-3 不參與 PREREQUISITE」設計註記
- 系統工具：`brew install yt-dlp`（2026.03.17）

### Why
原 Phase 6-2 計畫只注入「concept 名稱 + 影片標題」給 LLM，會生成「對 C++ 通用課程合理但未必對齊本課程教法」的內容（hallucination 風險）。使用者明確要求採 NotebookLM 模式（grounded on user-provided sources），確保 unit content 真實反映教授實際教法。同時將過去因「DB 04-62 而忽略 1-3」的限制解除，補齊 62 個影片完整對應。

---

## [2026-05-07] — Roadmap 新增 Phase 6 教學內容建構，原上線實測順延 Phase 7

### Added
- **`docs/roadmap.md` 新增 Phase 6：教學內容建構**（4 節 12 子任務，本機可完成 / 部分依賴教授交付資料）
  - **6-1 影片 metadata 整合**：6-1a 教授交付 metadata / 6-1b PATCH script / 6-1c 執行+驗證
  - **6-2 Unit content 批次生成**：6-2a prompt template / 6-2b LLM 批次寫入 / 6-2c 概念說明 YT player / 6-2d 範例 tab / 6-2e 摘要 tab
  - **6-3 練習題庫補充**：6-3a Phase 2-4 batch 模式生成 / 6-3b ExercisesTab 改為優先讀題庫
  - **6-4 內容品管**：6-4a 教授抽查 / 6-4b 修正 prompt 重跑

### Changed
- **原 Phase 6 上線實測 → Phase 7**：6-1/6-2/6-3 整段順延為 7-1/7-2/7-3，所有子任務同步重編號（cross-ref 註解保留歷史軌跡：原 4-3a → 6-1 → 7-1）
- **Phase 5 ⇄ Phase 6 平行關係**：執行策略 / 已確認決策最後一條同步調整為「兩者可平行 / 先後皆可，依教授資料準備進度而定」
- **Phase 7 前置條件加強**：除原 Zeabur + VPS 就緒外，新增「Phase 6 至少 6-1 + 6-2b 完成」（避免部署後 Learn 頁面仍空殼）

### Synced
- `CLAUDE.md` 當前狀態：呈現 Phase 5 ⇄ Phase 6 平行 + Phase 7 收尾的三段結構
- `docs/tech-debt.md` 兩條教學內容相關項目加 cross-ref 至 Phase 6-1 / 6-2~6-4（原內容保留作為背景說明）

### Why
使用者反映「整合教材」未進 roadmap 追蹤；目前只有 tech-debt + 內聯註釋，容易被忘。同時使用者明確指出「教師端 / 教學內容看實際狀況」決定先後，故將 Phase 5 與 Phase 6 設計為可平行關係，避免硬性綁定誰先誰後。

---

## [2026-05-07] — Roadmap 重整 follow-up：修正其他 doc 殘留舊 Phase 標號

### Fixed
- **`docs/design-plan.md` §4.5**：`1-7c 上線驗證` → `Phase 6 上線實測（原 1-7c → 4-3a → 6-1b Golden path）`，保留歷史演進 cross-reference
- **`docs/modules.md` Module 8 / 9**：Phase 4 → **Phase 5**（教師 Dashboard / 學習行為分析屬教師端，非部署）
- **`docs/db-schema.md` chat_messages 擴充欄位註記**：Phase 4-2c → **Phase 5-2c**（dialogue_act 屬行為資料收集，原本就在 5-2c，4-2c 為誤標）
- **`docs/roadmap.md` Phase 1 結尾註記**：「部署原 1-7 已移至 Phase 4」補完為「Phase 4（容器化 / 配置層）+ Phase 6（上線實測）」反映當前兩段切分

### Verified clean（未動）
- `docs/changelog.md` 歷史 entry（line 1670 / 1897 / 1898 / 2221）：屬當時決策的歷史記錄，保留原貌不改
- `docs/dev-setup.md` Phase 4-1b 引用：4-1b 仍在 Phase 4，無誤
- `docs/references.md` Phase 4 / 5-1 / 5-2 / 5-3 引用：全部與重整後結構一致

---

## [2026-05-07] — Roadmap 重整：上線實測類任務集中至 Phase 6

### Changed
- **`docs/roadmap.md` 結構調整**：將「需要實際部署到 Zeabur / VPS 才能驗證」的工作集中到新的 **Phase 6 上線實測**
  - 原 `Phase 4-3 上線驗證`（4-3a/b/c）整段移至 Phase 6
  - 4-3a Golden path → **6-1**（拆成 6-1a 部署 / 6-1b Golden path / 6-1c 教師端 e2e 三步驟）
  - 4-3b 監控 → **6-2**（拆出 6-2a/b/c 程式碼可本機完成 + 6-2d 須實際部署驗證告警鏈路）
  - 4-3c 效能 baseline → **6-3**（拆成 6-3a TTFB/LCP / 6-3b LLM p95 / 6-3c Judge0 / 6-3d 寫入 baseline 文件）
- **Phase 4 改名**：「部署上線」→「部署準備（容器化 + 配置層，本機可完成）」標記 ✅，明確區分本機可完成與須實際部署
- **Phase 5 前置條件放寬**：原「Phase 4 部署完成」→「Phase 4 配置層完成」，加註資料策略：5-1/5-2/5-5 純本機可完成；5-3/5-4 程式碼可先用合成資料寫，部署後以實測資料調校
- **執行策略 / 已確認決策**：頂部與底部同步更新為 Phase 2→3→4→5→6 新順序

### Synced
- `CLAUDE.md` 當前狀態區塊：Phase 4 標記為 ✅（容器化+配置層），下一階段呈現「Phase 5（本機可開發）vs Phase 6（須部署）」二選一供使用者選

### Why
使用者明確表示「還沒準備好部署」，但 Phase 4-3 包在 Phase 4 中容易給人「部署是當前阻塞」的錯覺。重整後，Phase 5 教師端（不需部署）就可獨立推進，Phase 6 維持為部署完成後一次驗收，避免邊開發邊維運耗能。

---

## [2026-05-06] — Phase 4-3a 進行中：Health endpoint Redis import binding 修復

### 修補（4-3a 整合驗證階段抓到的 bug）
- **`backend/api/routes/health.py` Redis 連線檢查 false-negative**：`from core.redis import redis_client` 在 import 當下抓到的是 `None`（因 `init_redis()` 是啟動時才 set global），之後 lifespan 設好的 client 不會反映到 health module 的 reference → `/health` 永遠回 `redis: disconnected` 即使實際 Redis 正常
- **修法**：改用既有 `get_redis()` 函式（每次呼叫都 lookup 當前 module global），並移除已成多餘的 None 檢查（`get_redis()` 內部會 raise，由外層 `except Exception` 接住）
- 修補後 `/health` 回 `{"status":"ok","services":{"database":"connected","redis":"connected"}}`

### 整合驗證階段成果（自動驗證）
- Backend pytest **442 passed** in 1.97s（零 regression）
- Frontend `tsc --noEmit` 無錯
- Frontend `next build` 成功 13 routes
- Alembic migration 在 head（`e1f2a3b4c5d6`）
- Postgres + Redis container healthy（dev compose Up 7 days）

### 設計關鍵
- **Python `from X import Y` 的 binding 陷阱**：對 module 層級 mutable global 應該 `import X` 然後用 `X.Y`，或透過 getter function 包裝；只有不變的常數或型別才能直接 `from X import Y`
- **此 bug 之前 442 tests 沒抓到**：`test_health.py` 用 fixture mock 掉 `redis_client`，沒實測「lifespan 啟動 → ping」整條鏈路（記入 tech-debt 評估是否補 e2e health test）
- **不影響其他端點**：`get_redis()` 走 module global lookup，之前所有 cache / rate limit 端點都正常；只有 health.py 自己誤報

---

## [2026-05-05] — Phase 4-2c：NextAuth callback URL + CORS 設定（Phase 4-2 完成）

### 修補（部署阻擋風險）
- **`zeabur.json` web env 加 `AUTH_TRUST_HOST=true`**：NextAuth v5 在反向代理後（Zeabur）的必要設定；缺此設定 callback URL 會用 container internal hostname 而非公開 domain → Google OAuth `redirect_uri_mismatch`
- **`backend/core/config.py` `cors_origins` 加 `.rstrip("/")` 防呆**：CORSMiddleware 對 origin 嚴格字串比對，若 `NEXTAUTH_URL` 含尾斜線（`https://domain.com/`）會與 browser 送的 `https://domain.com` 不符 → 403

### 新增（測試）
- `backend/tests/test_cors.py` 加 3 個 cors_origins 容錯測試：
  - 帶尾斜線 → 應 strip
  - 無尾斜線 → 不變
  - 多個尾斜線（極端）→ 全清
- 全套 442 backend tests 全綠（439 → 442，+3 個新測試，零 regression）

### 文件
- `docs/deployment.md` 加 §D NextAuth callback URL + CORS 機制章節（56 行）：
  - **Callback URL 怎麼產生**：`/api/auth/callback/{provider}` + `AUTH_TRUST_HOST` 決定主機名來源（X-Forwarded-Host vs internal hostname）
  - **三環境 AUTH_TRUST_HOST 設定一覽**：dev / self-host / Zeabur
  - **後端 CORS 設計說明**：為何單 origin、為何 rstrip
  - **「同 domain 仍要設 CORS」防禦深度說明**：架構上瀏覽器經 Next.js proxy 不直接打 backend，CORS 是萬一架構變動的安全網
  - **NextAuth 疑難排解表**：`redirect_uri_mismatch` / 登入後跳到 internal hostname / `NEXTAUTH_SECRET` mismatch / CORS preflight 401
- `web/.env.example`：補 `AUTH_TRUST_HOST=true` 註釋（dev 不需，prod 必要；含 NextAuth v5 預設不信 X-Forwarded-Host 的說明）

### 設計關鍵
- **`AUTH_TRUST_HOST` 是 Zeabur / 反代必填**：NextAuth v5 安全預設不信 forwarded headers；不設會卡 callback redirect
- **CORS rstrip 防呆而非禁尾斜線**：使用者填 `.env` 時可能習慣帶尾斜線，與其要求紀律不如 server 容錯
- **三環境設定表 vs 開放式描述**：學生 / 教師部署時直接看自己情境那行
- **`NEXTAUTH_SECRET` 同源**：zeabur.json backend / web 都用 `${AUTH_SECRET}` 同 Project variable → 自動一致；自架 `.env.prod` 用同一變數注入兩個 service
- **CORS preflight 401 疑難排解條目**：學生 / 教師最常踩的 trailing slash 坑寫進表格

### Phase 4-2 整體進度
- ✅ 4-2a 環境變數分層配置
- ✅ 4-2b Zeabur service 串接驗證
- ✅ 4-2c NextAuth callback URL + CORS 設定
- 4-2 配置層就緒；4-3 進入實際上線驗證 + 整合測試

---

## [2026-05-05] — Phase 4-2b：Zeabur service 串接驗證 + 部署 checklist

### 修正（zeabur.json 串接漏洞）
- **backend service 加 `BACKEND_HOST` expose**：原 web 引用 `${BACKEND_HOST}` 但 backend 沒 expose 此變數 → 部署會 fail
  - 加 `"BACKEND_HOST": {"default": "${CONTAINER_HOSTNAME}", "expose": true, "readonly": true}`
  - 與 postgres / redis 的 `${CONTAINER_HOSTNAME}` 慣例一致
- **redis 從 marketplace 改為 image-based**：與 postgres 一致，明確 expose `REDIS_HOST` / `REDIS_PORT`
  - 使用 `redis:7-alpine` image（與 dev compose 一致）
  - 加 ports / env / volumes spec

### 文件（deployment.md §A 重寫）
- 80 → 138 行新版 §A，重點變更：
  - **Service 串接架構圖**：postgres/redis → backend → web 變數引用鏈視覺化
  - **Zeabur 變數插值規則說明**：`${POSTGRES_HOST}` / `${CONTAINER_HOSTNAME}` / `${PASSWORD}` / `${WEB_DOMAIN}` 各自意義
  - **Step 1 改用 zeabur template deploy**：一鍵部署 vs 舊「手動建 4 個 service」
  - **Step 2 Project Variables 表**：6 個必設變數 + Secret 標記建議
  - **Step 5 補 Google OAuth redirect URI**：明確順序「先部署拿 domain → 回 Google Console 補 callback」
  - **部署 checklist**：8 項 dry-run 檢查（OAuth Client / API key / AUTH_SECRET / Zeabur 帳號 / commit 狀態）
  - **疑難排解擴增**：加 `${BACKEND_HOST}` 解析失敗 / template schema 拒絕 / OAuth redirect_uri_mismatch

### 設計關鍵
- **expose / readonly 對齊 Zeabur 慣例**：唯讀變數（HOST / PORT / DATABASE / USERNAME）標 `readonly: true` 防止使用者誤改
- **`${CONTAINER_HOSTNAME}` 自動內部 DNS**：每個 service 自己的內部主機名，不需手填
- **Redis 也改 image-based**：避免 marketplace expose 行為猜測 — 與 postgres 統一
- **部署 checklist 在 deploy 文件中**：實際操作前可逐項勾選；用戶不需記順序
- **fallback 仍寫在 Step 1 footnote**：若 Zeabur 拒絕 PREBUILT IMAGE schema，明確兩條備案

### Phase 4-2 進度
- ✅ 4-2a 環境變數分層配置
- ✅ 4-2b Zeabur service 串接驗證（zeabur.json schema + deployment.md 重寫）
- ⬜ 4-2c NextAuth callback URL + CORS 設定

---

## [2026-05-05] — Phase 4-2a：環境變數分層配置 + Zeabur Secret 指引

### 整理（env 範本）
- **刪除**：root `.env.example`（過時且與 backend/.env.example 重疊；誤導 dev 用 root .env）
- **新增**：`.env.prod.example`（72 行）— self-host VPS 完整範本：
  - 6 區段：Application PG / Auth / OpenAI / Judge0（A 自架 / B RapidAPI 二選一）/ Judge0 密碼 / 可選 debug 變數
  - 標明每組密碼的「對應出處」（與 judge0.conf 一致 / 與 docker-compose 服務變數一致）
  - 提示「強隨機密碼，至少 16 字元」
- `.gitignore`：加 `!.env.prod.example` 與 `judge0.conf` ignore 規則（保留 `.example`）

### 文件（環境變數分層）
- `docs/deployment.md` 加「環境變數分層」章節（268 行 → 272 行細）：
  - 三套配置一覽表（dev backend / dev web / self-host prod / Zeabur prod）禁混用
  - 變數分類一覽（敏感 vs 公開；每變數的 dev / self-host / Zeabur 來源）
  - **Zeabur Secret 標記方式**：Project Settings → Environment Variables → 詳情頁 → 開「Hidden / Secret」開關

### 設計關鍵
- **三套配置 vs 全部混用**：dev/self-host/Zeabur 三條獨立路徑；避免一個 .env 跨環境造成密碼洩漏
- **公開 vs 敏感清楚標記**：表格用 🔒 標敏感變數；Zeabur 部署時知道哪些必須設 Secret
- **`POSTGRES_PASSWORD` 在 Zeabur 自動產生**：zeabur.json 用 `${PASSWORD}`，由 Zeabur 注入隨機強密碼，使用者不需手動設
- **`JUDGE0_*_PASSWORD` 不在 Zeabur**：Zeabur 不能跑 Judge0 自架（privileged 限制），所以不適用
- **Self-host 路徑明確**：`.env.prod.example` 內標註「對應 docker-compose 服務」+ Judge0 密碼必須與 judge0.conf **完全一致**

### Phase 4-2 進度
- ✅ 4-2a 環境變數分層配置
- ⬜ 4-2b Zeabur service 串接驗證 / ⬜ 4-2c NextAuth callback + CORS

---

## [2026-05-05] — Phase 4-1c：Judge0 自架 docker-compose（取代 RapidAPI 配額）

### 新增（self-host Judge0 stack）
- `docker-compose.judge0.yml`（87 行）— Judge0 1.13.1 4 服務獨立 stack：
  - `judge0-server`：API 端點（接 submission，丟進 Redis queue）；port 2358
  - `judge0-workers`：實際 sandboxed 執行（讀 queue + cgroups 隔離）；同 image 不同 command
  - `judge0-db`：PostgreSQL 13（Judge0 metadata；獨立於 app PG）
  - `judge0-redis`：Redis 6（job queue；獨立於 app Redis，含密碼）
  - 兩個執行容器 `privileged: true`（cgroups 限制學生程式時間/記憶體/process）
  - healthcheck-gated 依賴鏈
- `judge0.conf.example`：Judge0 配置範本
  - `CPU_TIME_LIMIT=5` / `WALL_TIME_LIMIT=10` / `MEMORY_LIMIT=128000`
  - `ALLOW_ENABLE_NETWORK=false`（防學生程式對外連線）
  - `ENABLE_WAIT_RESULT=true`（同步等結果，簡化 backend）
  - 使用者複製為 `judge0.conf` 並填密碼後**勿 commit**

### 文件
- `docs/deployment.md` 加 §C Judge0 自架（80 行）：
  - **⚠ Zeabur 不支援警告**：privileged container 被禁 → Zeabur 部署仍走 RapidAPI Judge0
  - Step 1-5：準備 conf → 補 .env.prod → 啟動 stack → 驗證 `/about` → 合併 backend 網路（3 種方式）
  - 疑難排解表：`/about` 502 / privileged 被拒 / timeout / status=1 卡住
- `docs/tech-debt.md`：加「Judge0 自架未在生產驗證」條目

### 設計關鍵
- **獨立 compose 而非整合 prod**：Judge0 是可選；4 服務 + privileged 整合進 prod compose 會臃腫
- **Judge0 1.13.1 而非 v6.x**：1.13.1 文件多 + 多家驗證
- **API key 留空表示自架**：backend `judge0.py` 的 `_build_headers` 已支援 — `JUDGE0_API_KEY=""` → 不加 RapidAPI header
- **Zeabur fallback 寫在文件**：明確指引 Zeabur 部署改 RapidAPI

### Phase 4-1 整體進度
- ✅ 4-1a Dockerfile build 驗證
- ✅ 4-1b pgvector 容器配置
- ✅ 4-1c Judge0 自架
- 4-1 容器化階段就緒；4-2 進入實際 Zeabur 部署

---

## [2026-05-05] — Phase 4-1b：pgvector 容器配置驗證 + 生產 compose

### 驗證（dev pgvector 完整就緒）
- `docker-compose.dev.yml` 已用 `pgvector/pgvector:pg16` image，container 跑 6 天 healthy
- `vector` extension 已啟用（v0.8.2）
- `documents` 業務表 + LlamaIndex 自動建的 `data_codedge_rag` 表（含 `embedding vector` column）就緒
- `alembic upgrade head` 含 `CREATE EXTENSION IF NOT EXISTS vector`（migration b2c3d4e5f6a7）

### 修正（zeabur.json 部署風險）
- 原 `zeabur.json` 的 postgres 用 `marketplace.postgresql` — **標準 PG 不含 pgvector** → 部署會 fail 在 alembic
- 改為 `template: PREBUILT` + `source: {type: "IMAGE", image: "pgvector/pgvector:pg16"}`：
  - 加 ports / env / volumes 完整 spec
  - 暴露 `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_DATABASE` / `POSTGRES_USERNAME` 給 backend service 引用（`${POSTGRES_HOST}` 等變數）
- ⚠ Schema 細節未經實際 Zeabur 部署驗證（記入 tech-debt.md）；4-2 部署當下若 Zeabur 拒絕，依 deployment.md §A fallback：marketplace pgvector 或 GIT + 一行 Dockerfile

### 新增（self-host 部署）
- `docker-compose.prod.yml`（84 行）：
  - 完整 4 服務（postgres / redis / backend / web）依賴鏈 healthy gate
  - 密碼從 `.env.prod` env 讀取，**不寫入檔案**
  - PG/Redis 不暴露 host port（內部網路），只 web `3000` 對外（前置 nginx/caddy）
  - backend healthcheck（30s interval + 30s start_period）
  - 與 `docker-compose.dev.yml` 同 pgvector image（dev/prod 一致）

### 文件
- `docs/deployment.md` 大幅擴充（80 → 174 行）：
  - 章節分為 §A Zeabur / §B Self-host VPS
  - 加 ⚠ pgvector 必要性說明（migration 會 CREATE EXTENSION vector）
  - 加 §A Zeabur fallback 指引（schema 被拒時的兩種替代方案）
  - 加 §B 完整 self-host 流程（.env.prod / 啟動 / nginx 反代 / 健康檢查 / 疑難排解）
  - 疑難排解表加 `permission denied / type "vector" does not exist` 條目對應 PG image 錯誤
- `docs/tech-debt.md`：加「Zeabur PREBUILT IMAGE schema 待實測」條目

### 設計關鍵
- **dev / prod 同 image**：兩個 compose 都用 `pgvector/pgvector:pg16`；避免 dev 過 / prod 在 alembic 才 fail 的尷尬
- **prod compose 不暴露 PG/Redis host port**：MVP 安全考量；未來若需 backup/管理可加 `--profile admin` 服務
- **Zeabur schema fallback 文件先寫**：4-2 實測前先把 fallback 路徑寫清楚，部署當下不需重新研究
- **不刪 dev compose**：dev / prod 分檔，dev 仍方便 host port 連線除錯

---

## [2026-05-05] — Phase 4-1a：Dockerfile 驗證 + 依賴 lock 重產

### 修補（依賴）
- `backend/pyproject.toml`：補完 `dependencies` — 加 LlamaIndex 三套件 + `psycopg2-binary`：
  - `llama-index-core>=0.13,<1`
  - `llama-index-embeddings-openai>=0.5,<1`
  - `llama-index-vector-stores-postgres>=0.5,<1`
  - `psycopg2-binary>=2.9,<3`（PGVectorStore 同步初始化用）
- `backend/requirements.lock`：用 `uv pip compile pyproject.toml -o requirements.lock` 重產（38 → 272 行；含全部 transitive deps 鎖定版本）
- 確認 pyBKT **未實際 import**（updater.py 註解保留說明 BKT 數學公式來自 Corbett & Anderson 1995；pyBKT 是 Phase 5 行為分析後可選用）→ 不加入依賴

### 驗證
- `docker build -t prog-edu-backend ./backend` ✅ 成功（667 MB；含 LlamaIndex / pgvector / cryptography 等）
- `docker build -t prog-edu-web ./web` ✅ 成功（285 MB；Next.js standalone output 已啟用）
- 兩個 Dockerfile 結構保持原樣，僅補 lock 內容讓 `pip install -r requirements.lock` 完整

### 設計關鍵
- **lock 重產一次到位**：tech-debt 累積已久（Phase 2-1 / 2-3 加套件後一直未更新）；4-1a 是部署前最後機會修正
- **pyBKT 不加**：純 BKT 公式線上更新無需套件；pyBKT 用於 fit 真實學生資料，Phase 5 才需要
- **Multi-stage build 暫不做**：backend Dockerfile 單階段；後續若要瘦身可改 multi-stage（builder 含編譯 deps，runtime 只裝 runtime deps）— 屬優化非阻塞

### Phase 4-1 整體進度
- ✅ 4-1a Dockerfile 驗證 build
- ⬜ 4-1b pgvector/pgvector:pg16 容器配置
- ⬜ 4-1c Judge0 自架 docker-compose

---

## [2026-05-05] — Phase 3-3c：Dashboard 精熟度詳細總覽（Phase 3 完成 🎉）

### 新增（Backend）
- `backend/services/dashboard/mastery.py`（111 行）：
  - dataclass：`ConceptMasteryDetail` / `CategoryBreakdown` / `MasteryBreakdown`
  - `get_mastery_breakdown(db, user_id)`：一次 outerjoin 取所有 (concept, mastery_for_user)；application 層分群 + 排序
  - 分群：依 `concept.category`
  - 排序：concept 內依 `video_order ASC`（None 排尾）+ tag 穩定 fallback；category 依 earliest video_order ASC
  - `MASTERED_THRESHOLD = 0.8` 與 dashboard.queries / generator 一致
- `backend/api/routes/dashboard.py`：加 `GET /dashboard/mastery-overview`
  - response：`{ categories: [{ name, total, started, mastered, concepts: [{ tag, name_zh, video_order, difficulty, confidence }] }] }`

### 新增（Frontend）
- `web/lib/dashboard.ts`：加 types + `getMasteryOverview()` helper
- `web/components/dashboard/mastery-breakdown.tsx`（130 行）：
  - useEffect async fetch + cancelled flag
  - 4 狀態：loading / error / empty / list
  - 全展開（無摺疊互動）— 8 個 category section 全部顯示
  - Category header：name + 摘要 (mastered/total) + overall progress bar
  - Concept row：video_order + name + difficulty pill + mini progress bar + percent
  - 顏色語意：mastered 用 accent-green / 其他用 accent-blue
- `web/app/(app)/dashboard/page.tsx`：加 `<MasteryBreakdown />` section

### 測試
- `backend/tests/test_dashboard_mastery.py`（8 個 service + HTTP）：
  - 401 / 空狀態 / 多 category 分群 + summary / category 排序 / video_order=None 排尾 / 未練 confidence=0 / threshold 0.8 邊界 / HTTP 完整 payload
- 全套 439 backend tests 全綠（431 → 439，+8 個新測試，零 regression）

### 設計關鍵
- **單次 outerjoin 而非 N+1**：59 concepts 只 1 個 query，不是 60+
- **教學順序排序**：concept video_order ASC / category 依 earliest video_order
- **MASTERED_THRESHOLD = 0.8 共用**：與 generator / dashboard.queries 一致；單一語意
- **全展開 vs 摺疊**：60 rows 一覽比 click ladder 直觀

### Phase 3 整體里程碑（學習體驗 🎉）
- ✅ 3-1 結構化學習路徑（7 個 sub-tasks）
- ✅ 3-2 Quiz 完整版（3 個 sub-tasks）
- ✅ 3-3 Dashboard（3 個 sub-tasks）
- 學生端完整體驗就緒：登入 → Learn → Quiz → Dashboard 全閉環
- 後端測試從 Phase 3 開始時的 320 → 完成時的 439（+119）

---

## [2026-05-05] — Phase 3-3b：Dashboard 最近活動時間線

### 新增（Backend）
- `backend/services/dashboard/timeline.py`（142 行）：
  - dataclass: `ActivityType` Literal["quiz", "reflection", "unit_completed"] + `ActivityItem`
  - 3 個 fetch helper（每類各取 limit 筆）：
    - `_list_quiz`：student_answers join question；標題含對錯與題幹截斷；detail 含題型/難度/提示用量
    - `_list_reflection`：reflections；含 quality_score 百分比 + 步驟數
    - `_list_completed_units`：learning_units WHERE completed_at IS NOT NULL（透過 path.user_id 過濾）
  - `list_recent_activities` 主流程：merge 三類 → sort by timestamp desc → 取 limit
- `backend/api/routes/dashboard.py`：加 `GET /dashboard/timeline?limit=N`
  - 422 if limit out of [1, 100]
  - response: `{ items: [{ type, timestamp(ISO), title, detail, link?, is_correct? }] }`

### 新增（Frontend）
- `web/lib/dashboard.ts`：加 `ActivityType` / `ActivityItem` types + `getRecentActivities(limit)` helper
- `web/components/dashboard/activity-timeline.tsx`（150 行）：
  - useEffect async fetch + cancelled flag 防 race
  - 4 狀態：loading skeleton / error / empty / list
  - `ActivityIcon` 依 type 與 is_correct 顯示對應 lucide icon + 顏色：
    - quiz 對 → CheckCircle2 綠 / quiz 錯 → XCircle 紅
    - reflection → ClipboardList 紫
    - unit_completed → GraduationCap 藍
  - `formatRelative(iso)` 相對時間（剛才 / N 分前 / N 小時前 / N 天前 / 完整日期）
  - 有 link 的 item 整列為 Link；無 link 為純 div
- `web/app/(app)/dashboard/page.tsx`：在 today suggestion 下加 `<ActivityTimeline />` section

### 測試
- `backend/tests/test_dashboard_timeline.py`（9 個 service + HTTP）：
  - 401 / 空狀態 / 三種事件類型完整出現 / quiz 含 is_correct + 提示用量 detail / reflection 品質百分比 / unit 限 completed / limit 截斷 / HTTP ISO timestamp / HTTP 422 limit 範圍
- 全套 431 backend tests 全綠（422 → 431，+9 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠

### 設計關鍵
- **每類各取 limit 後合併**：避免單一事件類型（如 quiz）量大時遮蔽其他類型；merge 後再取最終 limit
- **不含 comprehension 事件**：schema 沒專屬 completed_at；後續加欄位再加（記入 tech-debt）
- **不含 chat 訊息**：量大且不算「學習進度」級別的事件
- **R8 反 AI 感**：4 種 icon 全 lucide（無 emoji）；色彩僅用於語意（綠對 / 紅錯 / 紫反思 / 藍完成）
- **link 可空**：reflection 無對應 detail 頁面 → link=null；前端 row 渲染區分
- **相對時間在前端格式化**：後端只給 ISO；不在 JSON 預處理（避免時區邊界判斷複雜化）
- **限 limit ≤ 100**：避免 SQL 大 query；前端預設 20（dashboard 概覽用）

---

## [2026-05-05] — Phase 3-3a：學生 Dashboard 統計卡片 + 今日建議

### 新增（Backend）
- `backend/services/dashboard/queries.py`（231 行）：
  - dataclass：`PathProgressSummary` / `WeekQuizStats` / `MasteryOverview` / `TodaySuggestion` / `DashboardStats`
  - 4 個 fetch helper 對應 4 統計卡：
    - `_path_progress`：取最早 path（與 `ensure_default_path_exists` 一致）+ 計算 completed/total/percent
    - `_week_quiz_stats`：限近 7 天 student_answers + 答對率
    - `_mastery_overview`：total_concepts / started_count（mastery 表 row 數）/ mastered_count（confidence ≥ 0.8）
    - `_reflection_count`：累計反思次數
  - `_today_suggestion`：規則版（無 LLM）— 依 unit status 推薦下一動作：
    1. 有 `in_progress` unit → 「繼續學習：xxx」
    2. 有 `available` unit → 「開始下一單元：xxx」
    3. 全部 `completed` → 「課程完成，挑戰 Quiz」
    4. 無 path → fallback「進入 Learn 開始」（ensure_default_path 後不該發生）
  - 主入口 `get_dashboard_stats(db, user_id)` 組合所有
- `backend/api/routes/dashboard.py`（91 行）：`GET /dashboard/stats` endpoint
- `backend/main.py`：註冊 `dashboard_router`

### 新增（Frontend）
- `web/lib/dashboard.ts`：types + `getDashboardStats()` helper
- `web/components/dashboard/`：
  - `stats-cards.tsx`（145 行）— 4 張卡片網格（grid 1/2/4 列響應式）：路徑進度（含 progress bar）/ 本週 Quiz / 精熟度概覽 / 反思次數
  - `today-suggestion.tsx`（38 行）— 建議標題 + 描述 + 「立即前往」按鈕
- `web/app/(app)/dashboard/page.tsx`：完全重寫，從 placeholder 升級為功能頁
  - View union（loading / error / ready）
  - 統一 humanizeError（401 等）

### 測試
- `backend/tests/test_dashboard.py`（10 個 service + HTTP）：
  - 401 / 空狀態 / path_progress 計算 / week_quiz 7 天篩選 / mastery 三欄 / reflection 計數
  - today_suggestion 三規則（in_progress 優先 / 只 available / 全 completed）
  - HTTP 完整 payload 結構檢查
- 全套 422 backend tests 全綠（412 → 422，+10 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠

### 設計關鍵
- **規則版 today_suggestion 而非 LLM**：MVP 階段；個人化 LLM 建議留給 3-3b/c 或 Phase 4+；對學生而言「下一個該做什麼」清晰即可
- **Mastered threshold = 0.8**：與 generator 的 `DEFAULT_SKIP_MASTERED_THRESHOLD` 一致；單一語意「熟練」
- **Week 範圍 7 天**：rolling window（不是 ISO 週）；學生看到的是「最近 7 天」
- **path 取最早建立**：與 onboarding 的「ensure default path」一致；學生通常只有 1 條，無爭議
- **Path Progress percent 用整數**：避免顯示 24.5% 這種偽精確；`int((c/t)*100)`
- **空狀態完整可顯示**：cold start 學生 path=None / 全 0 也能正常渲染卡片（顯示「尚未建立」/「本週尚未作答」）
- **R8 反 AI 感**：4 卡片用 lucide icon，無 emoji；色彩僅用於語意（accent-green 進度條 / accent-purple 建議）

---

## [2026-05-05] — Phase 3-2c：作答後 EDF 回饋（Phase 3-2 完成 🎉）

### 重點
作答後的個人化回饋頁，整合 BKT 精熟度 + LLM 建議 + 推薦學習單元連結。
與 `/quiz/submit` 即時對錯分離（async fetch），保持結果頁載入快但內容豐富。

### 新增（Backend）
- `backend/services/quiz/feedback.py`（250 行）：
  - dataclass: `ConceptMasteryItem` / `RecommendedUnit` / `QuizFeedbackResult`
  - `_get_owned_answer` 擁有權檢查（非本人 → 404 STUDENT_ANSWER_NOT_FOUND）
  - `_fetch_concept_mastery`：outerjoin Concept × StudentMastery，未練概念視為 0
  - `_fetch_recommended_units`：限同 user 路徑 + 未完成 + concept 匹配
  - `_llm_suggestion`：依對錯 + mastery 給 1-2 句建議；4 種 fallback 路徑保證不擋學生
  - `generate_quiz_feedback` 主流程
- `backend/api/routes/quiz.py`：`SubmitResponse` 加 `answer_id`（前端要能拿來 fetch feedback）
- `backend/api/routes/quiz_feedback.py`（77 行，獨立檔避免主 quiz.py 超 250）：
  - `GET /quiz/answers/{answer_id}/feedback` endpoint
  - response 含 mastery 列表 + suggestion + suggestion_fallback flag + recommended_units
- `backend/main.py`：註冊 `quiz_feedback_router`

### 新增（Frontend）
- `web/lib/quiz.ts`：
  - `SubmitResponse` 加 `answer_id` 欄位
  - 加 `ConceptMasteryItem` / `RecommendedUnit` / `QuizFeedbackResponse` types
  - 加 `getQuizFeedback(answerId)` helper
- `web/components/quiz/feedback-section.tsx`（172 行）：
  - useEffect async fetch + cancelled flag 防 race
  - SkeletonView（loading）+ SuggestionCard / MasteryCard / RecommendedCard 三段式
  - MasteryRow 進度條（0-100%）對齊 design tokens（accent-green）
  - RecommendedUnit Link 帶 video_order 編號顯示
  - 統一 humanizeError
- `web/components/quiz/result-view.tsx`：在 CorrectAnswerSection 與導航按鈕之間嵌入 `<FeedbackSection answerId={result.answer_id} />`

### 測試
- `backend/tests/test_quiz_feedback.py`（14 個 unit + HTTP）：
  - 6 unit：5 種 _llm_suggestion fallback 路徑（no client / exception / invalid JSON / empty / 對錯各一）+ success
  - 4 service integration：擁有權 404 / mastery 0 補位 / 推薦 unit 過濾（已完成 / 不匹配 concept）/ 推薦 unit 正向案例
  - 4 HTTP：401 / 跨使用者 404 / success 完整 payload / submit response 含 answer_id（3-2c 新增欄位）
- 全套 412 backend tests 全綠（398 → 412，+14 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠

### 設計關鍵
- **submit 與 feedback 分離**：submit 立即回對錯（快）；feedback async fetch（LLM 慢，UI loading state 不擋畫面）
- **不重做 EDF Evidence**：quiz answer 結構化已知（is_correct + concept_tags），不需 LLM 拆解錯誤類型；EDF Evidence Pipeline 仍服務 chat 場景（學生提問時用）
- **未練概念視為 0**：`outerjoin` + 預設 0.0 — 顯示完整 concept_tags 不留空白，cold start 學生看到 0% 也比看到「無資料」直覺
- **推薦過濾三層**：同 user 的 path × 未完成 × concept_tag 匹配；避免推已學完的 unit 或他人路徑的 unit
- **獨立 route 檔**：`quiz_feedback.py` 拆出避免主 quiz.py 超 250 行（schema 定義較長）
- **LLM 失敗 fallback 對稱**：與 hint / EPL / Comprehension 設計一致；`suggestion_fallback` flag 讓前端顯示「離線」狀態
- **RecommendedUnit 連結到 /learn**：MVP 直接導向學習路徑首頁；未來可加深 deep-link 直跳特定 unit

### Phase 3-2 整體里程碑
- ✅ 3-2a Quiz 頁面：選擇題 + 程式撰寫題 UI
- ✅ 3-2b 計時器 + 提示系統（5 級 hint ladder）
- ✅ 3-2c 作答結果頁 + EDF 回饋顯示
- 全套 412 backend tests 全綠；學生 Quiz 完整閉環：選題型 → 取題 → 作答（含計時 + 提示）→ 對錯 + 解釋 + EDF 個人化回饋

---

## [2026-05-05] — Phase 3-2b：Quiz 計時器 + 5 級提示系統

### 新增（Backend）
- `backend/services/quiz/hint.py`（164 行）：
  - `HintResult` dataclass（level + hint + fallback flag）
  - `_FALLBACK_HINTS` dict — 對應 1-5 level 各一句固定鼓勵句（LLM 不可用時用）
  - `_ladder_description(level)` — 對應 .claude/rules/edf-pipeline.md 的 Hint Ladder 規則文字
  - `_format_question_for_prompt` — 題型 dispatcher（MC 含選項 / coding 含 starter）
  - `generate_hint(question, hint_level, student_attempt?)` async LLM；失敗回 fallback
- `backend/api/routes/quiz.py`（209 行）：加 `POST /quiz/hint` endpoint
  - body: `{ question_id, hint_level (1-5), student_attempt? }`
  - 404 QUESTION_NOT_FOUND / 400 QUESTION_NOT_VALIDATED / 422 invalid level
  - response 含 `fallback` flag 讓前端顯示「離線 fallback」標籤

### 新增（Frontend）
- `web/lib/quiz.ts`：加 `requestHint(payload)` helper + `HintResponse` type
- `web/components/quiz/timer.tsx`（39 行）：
  - 純 prop-driven，caller 傳 `startedAt: number`（Date.now() 時戳）
  - useEffect 每秒 setState tick；mm:ss 格式
- `web/components/quiz/hint-panel.tsx`（57 行）：
  - 累計顯示已取得 hints（依 level 排）+ 「取得第 N 個提示」遞增按鈕
  - **強制遞增**：學生不能跳級看 level 5（避免直接看答案）
  - 達到 max=5 後按鈕 disabled
  - fallback 提示加「（離線 fallback）」標示
- `web/components/quiz/quiz-runner.tsx`：
  - 加 `hints: HintResponse[]` + `hintBusy` state
  - `handleRequestHint` 永遠請 next level（current count + 1）
  - submit 時帶 `hint_level_used = hints.length`（持久化）
  - 換題時清空 hints
  - 顯示 Timer（question 模式）+ HintPanel（始終顯示）

### 測試
- `backend/tests/test_quiz_hint.py`（13 個 unit + HTTP）：
  - 6 unit：prompt ladder 描述 / MC prompt 含 options / LLM 成功 / no client fallback / exception fallback / invalid JSON fallback / empty hint fallback
  - 7 HTTP：401 / 422 (4 種 invalid level) / 404 / 400 / 200 success / 200 fallback
- 全套 398 backend tests 全綠（385 → 398，+13 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠

### 設計關鍵
- **Hint Ladder 對齊 EDF Pipeline 規則**：`_ladder_description` 直接引用 `.claude/rules/edf-pipeline.md` 5 級定義；保證 hint 風格與 chat 評估的「直接給答案」防護一致
- **LLM 失敗 fallback 不擋學生**：類似 EPL/Comprehension 設計；fallback 句子分 5 個 level 預先寫好，前端用 `fallback` flag 提示「離線」狀態
- **強制遞增不可跳級**：教學原則防止學生直接看 level 5；後端不限制（接收 1-5 任何值），由前端 UX 控制
- **Hint 不寫入 DB**：純即時生成；`hint_level_used` 已透過 `/quiz/submit` 持久化（quiz history 可分析學生提示依賴度）
- **Timer 純前端**：不影響 submit 流程；submit 時 caller 仍從 startedAt 計算 time_spent_seconds（與 3-2a 邏輯一致）
- **MC 也支援 hint**：UI 統一；雖然 MC hint 教學意義較弱，但保留選擇權

---

## [2026-05-05] — Phase 3-2a：Quiz 頁面 — 選擇題 + 程式撰寫題正式版

### 新增（Frontend）
- `web/lib/quiz.ts`（+30 行）：
  - `SubmitAnswer` discriminated union（依題型不同）：`{selected_index}` / `{code}` / `{answers}`
  - `SubmitQuestionPayload` / `SubmitResponse` types
  - `submitAnswer(payload)` helper → POST `/quiz/submit`
- `web/components/quiz/`（4 新元件）：
  - `quiz-runner.tsx`（200 行）— 主流程容器；五狀態 union（idle / loading / question / submitting / result）；題型 dropdown（選擇題 / 程式撰寫題）；計時 startedAt → time_spent_seconds 提交時帶入；統一 humanizeError
  - `mc-question.tsx`（68 行）— radio-style options + Lucide CheckCircle2/Circle 圖示；提交按鈕 disabled until 選中
  - `coding-question.tsx`（68 行）— 復用 `CodeEditor`（CodeMirror 6 + cpp + oneDark）；提示「Judge0 自動判分屬 Phase 4」；切題自動 reset content
  - `result-view.tsx`（115 行）— 對錯 banner（綠勾 ✓ / 紅叉 ✗ + Lucide）；feedback + explanation；MC/fill_blank 揭露正確答案；coding 不揭露（待 Judge0）；下一題 / 結束按鈕
- `web/app/(app)/quiz/page.tsx`：完全重寫，從 Phase 2-5c demo 升級為正式 Quiz 頁面；純包裝 `<QuizRunner />`

### Backend
- 無變動（既有 `/quiz/generate` + `/quiz/submit` API 已支援整個 3-2a 流程）
- 後端 385 tests 仍全綠（純前端任務）

### 設計關鍵
- **設計分工釐清**：Quiz 頁面 = 純測驗（取題 → 作答 → 結果），無反思流程；Learn 練習 tab（3-1e）= 學習場景含 Pre-Coding Reflection。避免在 Quiz 頁面強制反思打斷測驗節奏
- **Coding 題目前 is_correct=False**：`backend/services/quiz/grade.py` 的 coding 分支永遠回 False（Judge0 整合屬 Phase 4）；UI 提示這點，避免使用者困惑
- **Discriminated union for SubmitAnswer**：對應後端 `answer: dict` 但 TS 端用 union 強制型別 — 防止 caller 對 MC 傳 code 等錯誤
- **time_spent_seconds 自動計**：runner 在 question 模式記錄 `startedAt`，submit 時計算秒差送 server（為 3-2b 計時器顯示鋪路）
- **hint_level_used = 0 hardcoded**：3-2b 提示系統未實作前一律 0；submit API 已支援 0-5 範圍
- **coding 不揭露答案**：Phase 4 Judge0 整合後改用實際執行結果判分；3-2a 階段保留學生再思考空間
- **fill_blank UI 未做**：roadmap 明列 3-2a 為「選擇題 + 程式撰寫題」；fill_blank 在 result-view 已支援揭露答案邏輯，UI 待後續任務（顯示 `UnsupportedTypeNote` placeholder）
- **CodeEditor 復用**：直接 import 現有元件（守則 #7 不重複造輪子）；CodeMirror 6 + cpp + oneDark 已調整為 GitHub Dark token 對齊

### 待驗證（手動）
- 進 `/quiz` → 選題型 → 點開始 Quiz
- 選擇題：點選項 → 提交 → 看到對錯 + 解釋 + 正確答案揭露 → 下一題 or 結束
- 程式撰寫題：在 CodeMirror 寫 code → 提交 → 看到「答錯了」（因 coding 未接 Judge0）+ 解釋 → 下一題

---

## [2026-05-05] — Phase 3-1e：練習 tab 嵌入 Pre-Coding Reflection 觸發點（Phase 3-1 完成 🎉）

### 新增（Backend）
- `backend/services/quiz/orchestrator.py`：
  - 新增 `_resolve_concept_by_tag(db, tag)` helper（404 CONCEPT_NOT_FOUND if missing）
  - `generate_for_student` 加 optional `concept_tag` 參數：指定時直接針對該 concept 出題（跳過弱項邏輯）；省略則維持原弱項補強行為（向後相容）
- `backend/api/routes/quiz.py`：`GenerateRequest` 加 `concept_tag: str | None`，透傳到 service

### 新增（Frontend）
- `web/lib/quiz.ts`（55 行）：Question / Content type union + `generateQuestion(payload)` helper
- `web/components/learn/exercises-tab.tsx`（206 行）：
  - 三狀態流程：idle（「開始練習」按鈕）→ loading → question（顯示題目 + 「開始反思」）→ reflecting（彈 ReflectionFlow modal）→ done（反思摘要 + 後續導引）
  - 取題：`generateQuestion({ type: "coding", bloom_level: 3, concept_tag: unit.concept_tag })`
  - 復用 `ReflectionFlow` 元件（Phase 2-5）：`sourceType="quiz"` + `sourceId=question.id`
  - 反思 approve → 顯示反思摘要（含 quality_score 百分比 + followup question 若有）+ 提示「在 Workspace 作答」連結 + 「回上方點完成單元」
  - 「重新出題」按鈕（reset 狀態）
  - humanizeError 處理 CONCEPT_NOT_FOUND / QUIZ_VALIDATION_RETRY_EXHAUSTED / QUIZ_UNAVAILABLE / 401
- `web/components/learn/unit-content.tsx`：把原 `ExercisesTab` placeholder 改用新元件，傳入 `unit.concept_tag` + `unit.concept_name_zh`

### 測試
- `backend/tests/test_quiz_route.py` 加 2 個 HTTP 測試：concept_tag 指定 → 該 concept 出題；不存在 tag → 404 CONCEPT_NOT_FOUND
- 全套 385 backend tests 全綠（383 → 385，+2 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠

### 設計關鍵
- **「觸發點」非「完整作答」**：3-1e 範圍嚴格限於「在練習 tab 內取題 + 觸發反思」；完整 coding 作答 UI（編輯器 + Judge0 提交 + 判分回饋）屬 Phase 3-2 Quiz 完整版
- **向後相容的 quiz/generate**：新增 `concept_tag` 為 optional，原 cold-start fallback / 弱項補強邏輯不變
- **復用 ReflectionFlow 而非重寫**：對齊「不重複造輪子」（CLAUDE.md 守則 #7）；reflection 元件已成熟，直接 import 即可
- **Workspace 導引**：反思 approve 後的「在 Workspace 作答」連結會配合 Phase 2-5d 的 `setActiveReflectionId`（reflection_id 寫 sessionStorage）— 學生跳到 /workspace 寫程式時 AI Tutor 自動帶入此反思（EDF Pipeline 注入），完整閉環
- **題型固定 coding**：教學影片內容多為 coding 練習；MC/fill_blank 對「練習」概念意義較弱，3-1e 不暴露選擇

### Phase 3-1 整體里程碑
- ✅ 3-1a Schema + ORM
- ✅ 3-1b 路徑生成 service（priority Kahn's）
- ✅ 3-1c Learn 頁面 + 4 endpoints
- ✅ 3-1c+ Concept Graph 重建（59 影片）
- ✅ 3-1c++ Learn UX 簡化（lazy seed + 移除生成 UI）
- ✅ 3-1d 學習單元內容頁（4 tab + status transition）
- ✅ 3-1e 練習 tab 嵌入 Reflection 觸發點
- 全套 385 backend tests 全綠；學生 onboarding → 學習 → 練習 → 反思 → 完成單元的完整閉環就緒

---

## [2026-05-05] — Phase 3-1c+ 簡化：onboarding 自動 seed 預設路徑（移除無意義的「生成路徑」UX）

### 重新評估
- 3-1c 原設計含「+ 生成新路徑」按鈕 + EmptyState + 多路徑列表，預期學生會手動建立多條路徑
- 但 3-1c+ concept graph 重建為固定 59 影片線性鏈後，每位學生「生成」結果完全相同
  → category filter 是唯一變數但 99% 學生會學完整課程
  → 「生成」變無意義儀式，違反「不為不存在的需求設計」原則（YAGNI / CLAUDE.md 守則 #7）
- 結論：移除手動生成 UI，改為 onboarding 自動 seed

### Backend
- `backend/services/learning/queries.py`：
  - 加 `DEFAULT_PATH_TITLE = "C++ 完整課程"` + `DEFAULT_PATH_DESCRIPTION` 常數
  - 加 `ensure_default_path_exists(db, user_id) -> LearningPath`：學生有任何路徑 → 回最早建立的；無 → 呼叫 generate_learning_path 用預設 title/description
- `backend/api/routes/learning.py`：
  - 加 `GET /learning/paths/default` endpoint — Learn 頁面唯一入口
  - 抽 `_build_path_detail` helper 共用於 GET /paths/{id} / POST /paths / GET /paths/default 三處
  - **保留** POST/DELETE/GET list endpoints 供未來教師端 / 自訂路徑使用，前端不暴露

### Frontend
- `web/lib/learning.ts`：精簡 — 加 `getDefaultPath()`；**刪除** `listPaths` / `generatePath` / `deletePath` / `progressPercent` / `GeneratePathPayload` / `PathSummary`（前端不再需要）
- `web/components/learn/path-card.tsx`：**整檔刪除**
- `web/components/learn/generate-path-dialog.tsx`：**整檔刪除**
- `web/components/learn/path-detail.tsx`：移除 `onBack` prop + 「返回路徑列表」按鈕（無 list 可返）
- `web/app/(app)/learn/page.tsx`：**完全重寫**
  - 兩模式：detail（預設視圖）/ unit（內容頁）— 移除原 list / loading-detail
  - 進入 → 自動 fetch `/learning/paths/default`（後端 lazy seed）→ 直接顯示 detail
  - 移除：EmptyState / 「+ 生成新路徑」按鈕 / 刪除按鈕 / dialog 整套
  - 學生 onboarding 體驗：登入 → Learn → 立刻看到「C++ 完整課程」59 個 unit

### 測試
- `backend/tests/test_learning_route.py` 加 4 個 HTTP 測試：401 / lazy seed 首次 / 已有路徑回最早建立 / 422 無 concepts
- 全套 383 backend tests 全綠（379 → 383，+4 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠（Route summary 含 `/learn` ○ static prerender）

### 設計關鍵
- **「ensure 而非 default-named」語意**：`ensure_default_path_exists` 回任何已存在路徑（不檢驗 title），避免使用者手動建立非預設 title 後又被自動建一條重複的
- **Backend endpoints 完全保留**：POST/DELETE/GET list 仍在；schema 完全保留；前端不暴露但 schema 仍支援多 path（為未來教師端 / 複習路徑預留）
- **無 list 視圖反而更簡潔**：原 path-card.tsx 在只有 1 條路徑時是視覺噪音；直接顯示 detail 更直覺
- **path-detail 移除 onBack**：detail 變主畫面，無「返回」目的地；unit-content 內仍有「返回路徑：xxx」按鈕（unit → detail 的返回有意義）
- **不刪除 schema/migration**：方案 A 純 UX 簡化，零 schema 變動；未來真有教師端再 git revert 復活 path-card / generate-dialog 即可

---

## [2026-05-05] — Phase 3-1d：學習單元內容頁（4 tab + status transition + 自動解鎖）

### 新增（Backend）
- `backend/services/learning/units.py`（129 行）：
  - `update_unit_status(db, user_id, unit_id, new_status)` — status transition + 解鎖下一單元
  - 合法 transition：available → in_progress、in_progress → completed、in_progress → available（revisit）
  - 非法 transition 一律 422 LEARNING_UNIT_INVALID_TRANSITION（locked 不可手動設、completed 不可重置）
  - completed 自動連動：同 path 內 order_index = current+1 的 unit（若 locked）→ available
  - 擁有權檢查透過 unit.path_id → path.user_id；非本人 → 404
- `backend/api/routes/learning_units.py`（85 行，獨立檔避免主 learning.py 超 250）：
  - `PATCH /learning/units/{unit_id}` body `{ status: "available" | "in_progress" | "completed" }`
  - `_parse_status` 422：非合法 enum / locked
  - `UnitTransitionOut` 含 `unit` + `next_unlocked_unit`（若有）

### 新增（Frontend）
- `web/lib/learning.ts`：加 `updateUnitStatus(unitId, status)` + types `WritableUnitStatus` / `UnitBasic` / `UnitTransitionResult`
- `web/components/learn/unit-content.tsx`（230 行）：
  - 4 tab：概念說明 / 範例程式 / 練習題 / 摘要
  - 概念說明 tab：YT player placeholder（待教授補 video_id）+ concept 簡介
  - 範例程式 / 摘要：unit.content 為空時顯示 EmptyTab placeholder
  - 練習題：3-1e 整合 placeholder
  - 上一/下一單元導航（locked unit 不可導航）
  - ActionButton 依 status 顯示「開始學習」/「完成單元」/「已完成 ✓」/「尚未解鎖」
- `web/components/learn/path-detail.tsx`：unit 變可點，locked 用 opacity-60 + cursor-default
- `web/app/(app)/learn/page.tsx`：
  - View union 加 `unit` 模式（持 detail + unitIndex）
  - 新增 `UnitView` 包裝 — status transition 後重 fetch path detail + 維持當前 unitIndex
  - 解鎖的下一 unit 經 path detail 同步刷新自動可見

### 測試
- `backend/tests/test_learning_units.py`（13 個 service + HTTP）：
  - Service：合法 transition / completed 解鎖 / last unit no next / locked rejected / completed→available rejected / revisit 清 completed_at / 跨使用者 404
  - HTTP：401 / 422 invalid status string / 422 locked / 200 + next_unlocked / 422 invalid transition / 跨使用者 404
- 全套 379 backend tests 全綠（366 → 379，+13 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠

### 設計關鍵
- **status transition 用查表** (`_VALID_TRANSITIONS: dict[str, set[str]]`)：宣告式比 if/else 易擴充與檢驗
- **completed → 任何狀態都拒絕**：避免精熟度反覆波動造成 BKT 信心度震盪（現實中重學的學生應該再走 quiz/comprehension 重新評估，不是直接 reset unit）
- **revisit 路徑（in_progress → available）**：學生想重看不算完成，清空 `completed_at`；不影響後續解鎖（解鎖只發生在 completed transition）
- **解鎖只往前推一個**：unit N 完成 → unit N+1 解鎖；不會跨章節同時解鎖（教學節奏控制）
- **route 拆獨立檔**：`learning_units.py` 與 `learning.py` 分檔避免單檔超 250 行；前綴都用 `/learning` 路由 namespace
- **`_basic` response 不含 concept join**：transition response 給前端最小欄位（id/order_index/status/completed_at），需要完整 unit 資料時前端重 fetch path detail
- **前端切換 view 用 union state**：相比 nested route 簡化，不需設計 layout 共用 / breadcrumb；學生在 unit 頁完成 transition 後直接看到下一 unit 解鎖
- **YT player placeholder + content 空骨架 placeholder**：3-1d 範圍只做 UI 容器，內容（video_id / examples / summary）等教授補資料或 LLM 生成（見 tech-debt.md）

---

## [2026-05-05] — Phase 3-1c+：Concept Graph 重建（教授 C++ 課程 59 影片整合）

### 重大決策
- **完全替換 V1 20 個 EDF concept** → 改為 62 部 YT 影片中排除 01-03 介紹後的 **59 個影片 concept**（每影片 = 1 concept node）
- EDF 的 20 個 ConceptTag enum **保留**在 `services/edf/models.py` 純粹做 LLM 錯誤分類提示用，**不再寫入 concepts 表**
- chat-driven mastery 暫時退場（EDF 評估 LLM 回的粗 tag 在 concepts 表找不到 → 既有 fallback 跳過更新）；mastery 改由 quiz 答題 + comprehension 驅動（這些用 question.concept_tags = 影片 tag）

### Schema
- `backend/alembic/versions/d0e1f2a3b4c5_add_video_metadata_to_concepts.py`（67 行）：
  - `concepts` 加 3 nullable 欄位：`video_youtube_id` (VARCHAR 20) / `video_duration_seconds` (INT) / `video_order` (INT)
  - 2 個 CHECK constraints + 1 個 index on `video_order`
- `backend/models/concept.py`：對應 ORM 加 3 欄位

### 內容（destructive seed）
- `backend/alembic/versions/e1f2a3b4c5d6_seed_cpp_video_concepts.py`（180 行）：
  - ⚠ 清空 `learning_units` / `learning_paths` / `concept_edges` / `student_mastery` / `concepts`
  - Seed **59 個影片 concept**，依教授課程順序 04-62
  - tag 命名：`cpp-NN-keyword`（NN 兩位編號 + 簡短英文）
  - 8 個 category：入門 / 變數與型別 / 運算子 / 流程控制 / 迴圈 / 函式 / 陣列 / 指標與記憶體 / 物件導向
  - difficulty_level 1-5 依教學順序漸進
  - Seed **58 條 PREREQUISITE 線性鏈**（04→05→...→61→62）
  - YT video_id / duration 暫 NULL，等教授補後 PATCH
- 修正：`concept_edges.edge_type` 是 PG ENUM `concept_edge_type` 不能從 VARCHAR 隱式轉型 → 用 `sa.Enum(..., create_type=False)` 顯式宣告

### 驗證
- PG 上 alembic upgrade head 成功；`SELECT COUNT(*) FROM concepts` = 59；`prerequisite` edges = 58
- 全套 366 backend tests 全綠，零 regression（ORM 加 nullable 欄位無破壞性）

### 設計關鍵
- **方案 B（完全替換）vs A（共存）/ C（替換+對應）**：選 B 因為 chat-driven mastery 本來噪音多，真正可信信號來自 quiz/comprehension；簡化 99% 複雜度，符合 YAGNI 原則
- **線性 PREREQUISITE 鏈為主**：跨章節依賴（如 47 遞迴 ← 29 for）等教授後續標註；MVP 先簡單可用
- **Migration 不可重跑（destructive）**：alembic 只跑一次此 revision，OK；dev/prod 都會清掉舊 concept；目前未上線無真實學生資料風險
- **學習路徑生成可立即運作**：拓撲排序在 59 個 concept + 58 條線性邊上產生有意義路徑；弱項補強仍能依 BKT 信心度排序
- **YT player 整合延後**：`video_youtube_id` 已在 schema，等教授補資料後 3-1d 學習單元頁實作

### 待辦（教授提供資料後）
- [ ] PATCH script 一次更新 59 影片的 `video_youtube_id` + `video_duration_seconds`
- [ ] 跨章節 PREREQUISITE 邊補強（如 47 遞迴 ← 29 for；65 條左右）
- [ ] Learn 頁面影片 thumbnail / duration 顯示（需 youtube_id）

---

## [2026-05-05] — Phase 3-1c：Learn 頁面 — 路徑視覺化 + 進度條

### 新增（Backend）
- `backend/services/learning/queries.py`（135 行）：
  - `PathProgress` / `UnitWithConcept` dataclass
  - `list_paths_for_user`（一次取所有 units 算進度，避免 N+1）
  - `get_path_with_units`（join concepts 取 tag/name_zh/difficulty，避免前端再 join）
  - `delete_path`（CASCADE 連動 units）
  - `_get_owned_path` 擁有權檢查 → 404（避免列舉攻擊）
- `backend/api/routes/learning.py`（186 行）— 4 endpoints：
  - `POST /learning/paths`（201）→ 完整 detail
  - `GET /learning/paths` → list + 進度概覽
  - `GET /learning/paths/{id}` → detail + units
  - `DELETE /learning/paths/{id}`（204）

### 新增（Frontend）
- `web/lib/learning.ts`（76 行）：types + 4 API helpers + `progressPercent` utility
- `web/components/learn/`：
  - `path-card.tsx`（83 行）— 卡片含進度條 + hover 顯示刪除按鈕
  - `unit-status-icon.tsx`（37 行）— 4 種 status icon（CheckCircle2/PlayCircle/Circle/Lock）+ 中文 label
  - `path-detail.tsx`（76 行）— 路徑詳細頁含 unit ordered list
  - `generate-path-dialog.tsx`（132 行）— 表單 modal（title/description/category）
- `web/app/(app)/learn/page.tsx`（重寫，180 行）：
  - 三模式：list / detail / loading-detail
  - 整合：listPaths / getPath / generatePath / deletePath
  - 統一 error handling 翻譯成中文（LEARNING_PATH_EMPTY / LEARNING_PATH_NOT_FOUND / 401）
  - EmptyState（無路徑時引導生成）

### 測試
- `backend/tests/test_learning_route.py`（13 個 HTTP 整合）：4 endpoint × 401 / POST 完整流程 / POST 422 / list 空 + 含進度 / GET 排序 / GET 跨使用者 404 / GET 不存在 404 / DELETE 移除 / DELETE 跨使用者 404
- 全套後端 366 tests 全綠（353 → 366，+13 個新測試，零 regression）
- TypeScript / ESLint / next build 全綠

### 設計關鍵
- **單元擁有權檢查走 path**：unit 沒獨立 user_id；過 path.user_id 過濾即可（DB schema 設計就如此）
- **list 一次撈避免 N+1**：`list_paths_for_user` 先撈所有 paths 後一次 IN 撈所有 units，application 層分群算進度
- **detail join concepts**：`get_path_with_units` server-side join，避免前端再 fetch concept 資訊
- **GET 路徑不存在 vs 跨使用者**：兩者都回 LEARNING_PATH_NOT_FOUND（避免列舉攻擊揭露存在性）
- **R8 反 AI 感**：UI 全用 lucide icon（無 emoji），status 顏色僅 4 種語意化（綠=完成 / 藍=進行 / 白=可學 / 灰=鎖定）
- **元件控制反向**：page.tsx 持狀態，子元件純 prop-driven（path-card / path-detail / dialog 全 stateless）
- **生成 dialog 預填 title**：「C++ 基礎學習路徑」減少使用者打字成本（cold start 友善）

---

## [2026-05-05] — Phase 3-1b：學習路徑生成 service（拓撲排序 + 弱項補強）

### 新增（Service）
- `backend/services/learning/topology.py`（73 行）：
  - `topological_sort_with_priority(nodes, edges, priority, default_priority)` — priority Kahn's algorithm
  - 純函式無 DB 依賴；O((N+E) log N)
  - 同層內按 priority 升序（弱項優先）；priority tie 用插入順序穩定破除
  - Cycle 容錯：殘留節點按 priority 附加到尾端，不擲錯
  - 邊指向 nodes 集合外的節點 → 忽略不擲錯（filter 後常見）
- `backend/services/learning/generator.py`（160 行）：
  - `generate_learning_path(db, user_id, title, description, category, skip_mastered_threshold)`
  - 流程：fetch concepts → fetch PREREQUISITE edges → fetch user mastery → 篩除已熟練 → priority Kahn's 拓撲 → 寫入 LearningPath + LearningUnits
  - 第一個 unit 設 `available`，其餘 `locked`（漸進解鎖機制）
  - 預設 `DEFAULT_SKIP_MASTERED_THRESHOLD = 0.8`
  - `content` 預留空骨架 `{"summary": "", "examples": [], "exercise_question_ids": []}`，由後續 service 填入
  - 422 LEARNING_PATH_EMPTY：無概念 / 全部已熟練 / category filter 無匹配
- `backend/services/learning/__init__.py`：export

### 測試
- `backend/tests/test_learning_topology.py`（12 個 unit）：空圖 / 單節點 / 線性鏈 / 弱項優先 / 拓撲約束維持 / cold start default / 穩定性 / diamond / cycle 容錯 / 外部邊忽略 / 多獨立鏈
- `backend/tests/test_learning_generator.py`（9 個 DB 整合）：3 種 422 / 線性鏈生成 / 跳過已熟練 / 同層弱項優先 / content 骨架 / category filter / 邊指向已熟練節點不破壞拓撲
- 全套 353 tests 全綠（332 → 353，+21 個新測試，零 regression）

### 設計關鍵
- **不採 RL**（守則 #7）：純拓撲 + 弱項補強已足夠；OATutor RL 屬過度工程，明確排除
- **priority Kahn's**：在 in-degree=0 候選中用 min-heap 選 confidence 最低 → 同時保證拓撲安全 + 弱項優先
- **Cold start = 弱項**：未練概念 confidence=0 → 自動排前面，符合「先學最不會的」直覺
- **跳過已熟練 (≥ 0.8)**：避免重複學；篩除後重算 edges 集合，剔除指向已熟練節點的邊（不破壞剩餘拓撲）
- **content 空骨架**：`{summary, examples, exercise_question_ids}` 預留 shape，後續 LLM 生成或編輯介面填入；不一次到位避免綁死
- **Cycle 容錯不擲錯**：PREREQUISITE 理論上 DAG，但程式不假設；殘留節點附加比硬報錯實用
- **演算法 vs DB 拆分**：topology.py 純函式無 DB 依賴 → 12 unit test 直接覆蓋演算法；generator.py 整合 DB → 9 integration test

---

## [2026-05-05] — Phase 3-1a：學習路徑基礎 schema（Module 7 啟動）

### 新增（Schema / Migration）
- `backend/alembic/versions/c9d0e1f2a3b4_create_learning_paths_and_units.py`（114 行）：
  - `learning_paths`：id / user_id (FK CASCADE) / title (VARCHAR 200) / description / created_at / updated_at + index user_id
  - `learning_units`：id / path_id (FK CASCADE) / concept_id (FK RESTRICT) / order_index / content (JSON) / status (VARCHAR 20 + CHECK enum) / completed_at + UNIQUE(path_id, order_index) + CHECK order_index >= 0 + index path_id, concept_id
  - status enum 4 值：`locked` (預設) / `available` / `in_progress` / `completed`

### ORM
- `backend/models/learning.py`（109 行）：
  - `LearningUnitStatus(str, Enum)` — locked/available/in_progress/completed
  - `LearningPath` + `LearningUnit` model（與 alembic 對齊）
- `backend/models/__init__.py`：export `LearningPath` / `LearningUnit` / `LearningUnitStatus`

### 測試
- `backend/tests/test_learning_models.py`（12 個）：metadata / 欄位 / status enum 值 / 預設 status=locked / UNIQUE(path, order) 衝突 / status CHECK 阻擋非法值 / order_index < 0 阻擋 / FK ondelete CASCADE 宣告
- 全套 332 tests 全綠（320 → 332，+12 個新測試，零 regression）

### 設計關鍵
- **status 用 String + CHECK**：與 quiz/concept/reflection/comprehension 慣例一致；避開 PG ENUM 雙寫法 + SQLite 測試相容
- **`(path_id, order_index)` UNIQUE**：強制同路徑內位置唯一，禁止碰撞
- **`concept_id` ON DELETE RESTRICT**：概念被刪需先處理路徑（避免遺孤學習單元）
- **`path.user_id` ON DELETE CASCADE**：使用者刪除帳號連動刪除路徑與單元
- **預設 status='locked'**：路徑生成（3-1b）後由 service 解鎖第一單元，後續漸進解鎖
- **`content` 用 JSON dict 不強制 shape**：unit 內容（summary / examples / exercise_question_ids）依教學需求演進，application 層驗證
- **不加 `is_active` / `archived_at`**：MVP 不支援軟刪除，避免不必要欄位（精準修改不擴散）
- **預留 polymorphic target**：reflections.source_type='learning_unit' 已預留指向 learning_units.id（無 FK，application 層驗證）

---

## [2026-05-05] — Phase 2-6e：動態觸發頻率 + 驗證結果驅動 BKT（Phase 2-6 完成 🎉）

### 新增（Service）
- `backend/services/comprehension/mastery_hook.py`（51 行）：
  - `apply_comprehension_mastery(db, user_id, question, passed)` — comprehension 通過/不通過 → BKT
  - `passed=True` → Evidence(NONE) 上調 confidence；`passed=False` → Evidence(LOGIC) 下調
  - `passed=None`（EPL fallback）→ no-op（無有效信號避免噪音）
  - `update_mastery` 異常 swallow（best-effort，與 quiz/submit 容錯一致）
- `backend/services/comprehension/trigger.py`（120 行）：
  - `TriggerDecision` dataclass + `decide_trigger(db, user_id, student_answer_id)`
  - 純規則 `_decide(pass_rate, is_coding)`（獨立函式方便 unit test）
  - 取近 5 筆有 `comprehension_passed` 的紀錄算 pass_rate；無紀錄 = cold start
  - 規則表：cold start → EPL；≥0.8 → 不觸發；[0.6, 0.8) → VARIATION；[0.3, 0.6) → PREDICT_OUTPUT；<0.3 → EPL
  - 非 coding 題 → PREDICT_OUTPUT/VARIATION 自動 fallback EPL（reason 補上 `（題型非 coding，fallback EPL）`）

### Workflow 整合
- `services/comprehension/orchestrator.py`：`submit_epl_for_answer` + `submit_predict_for_answer` 在 commit 前呼叫 `apply_comprehension_mastery(...)`
- `services/comprehension/variation.py`：`submit_variation_for_answer` 同樣串接 mastery hook
- 三條 grade pipeline 通過後皆驅動 BKT；EPL passed=None 跳過

### API
- `backend/api/routes/comprehension_trigger.py`（57 行）：
  - `GET /comprehension/trigger-suggestion/{student_answer_id}` → `TriggerDecisionOut`（should_trigger / suggested_type / pass_rate / sample_size / reason）
- `backend/main.py`：註冊 `comprehension_trigger_router`

### 測試
- `backend/tests/test_comprehension_trigger.py`（12 個 unit）：cold start / 高 / 中高 coding+非 coding / 中等 coding+非 coding / 低；threshold 邊界值
- `backend/tests/test_comprehension_mastery_hook.py`（4 個 unit）：passed=True/False/None / update_mastery 異常 swallow
- `backend/tests/test_comprehension_trigger_route.py`（6 個 HTTP）：401 / 跨使用者 404 / cold start / 高 skip / 中等 predict / 中高非 coding fallback / 低 EPL
- `backend/tests/test_comprehension_mastery_integration.py`（4 個整合）：EPL grade 通過 → mastery confidence > 0；EPL passed=None → mastery row 不存在；Predict / Variation grade 通過 → mastery 上調
- 全套 320 tests 全綠（293 → 320，+27 個新測試，零 regression）

### 設計關鍵
- **passed=None 不觸碰 mastery**：BKT 演算法對「答錯」與「未評分」應有差別 — fallback 不該被當作扣分，否則 LLM 偶發失敗會誤傷學生信心度
- **trigger 純規則 + DB 查詢**：可預測、易測；不引入隨機性 / RL（避免過度工程，符合守則 #7「不過度設計」）
- **threshold 集中常數**：`HIGH_PASS_THRESHOLD` / `MID_HIGH_PASS_THRESHOLD` / `MID_LOW_PASS_THRESHOLD` 提到 module 頂端，方便未來 A/B test 調參
- **`_decide` 獨立函式**：12 個 unit test 直接覆蓋規則矩陣，不需 DB；`decide_trigger` 只負責 fetch + dispatch
- **route 拆獨立檔**：trigger endpoint 放 `comprehension_trigger.py`，主 `comprehension.py` 維持 242 行不超 250

### Phase 2-6 整體里程碑
- ✅ 2-6a Schema 擴充 + Comprehension API
- ✅ 2-6b EPL 驗證
- ✅ 2-6c 預測輸出驗證
- ✅ 2-6d 變體挑戰
- ✅ 2-6e 動態觸發 + BKT 串接
- 全套後端 320 tests 全綠，準備迎接 Phase 3 學習體驗（Learn / Quiz / Dashboard 頁面）

---

## [2026-05-05] — Phase 2-6d：變體挑戰（LLM 生變體題 + 評分學生新解）

### 新增（Service）
- `backend/services/comprehension/variation.py`（242 行）：
  - `VariationGenerationResult` / `VariationGradeResult` dataclass
  - `_call_llm_json` 共用 helper（dedupe 兩 LLM 呼叫的 boilerplate；換取行數壓在 250 限制內）
  - `generate_variation(question, student_code)` / `grade_variation(...)` LLM 函式
  - `start_variation_for_answer` / `submit_variation_for_answer` workflow（DB + LLM 整合）
  - **StrictBool**：`_GradeResponse.passed` 拒絕 `"yes"` / `"true"` / `1` 等 LLM 文字噪音的隱式轉型
- `backend/services/comprehension/variation_prompts.py`（90 行）：
  - `build_generate_prompt`：強調「同核心概念、變更非本質特徵」（情境 / 數值 / 邏輯方向）
  - `build_grade_prompt`：LLM 心智模擬執行學生 code 對 test_cases；binary passed + feedback

### API
- `backend/api/routes/comprehension_variation.py`（99 行，獨立檔避免 comprehension.py 超 250 限制）：
  - `POST /comprehension/{id}/variation/generate` — 露 stem/starter/test_cases/concept_focus
  - `POST /comprehension/{id}/variation/grade` — body `{student_code: str}`
- `backend/main.py`：註冊 `comprehension_variation_router`

### 測試
- `backend/tests/test_comprehension_variation.py`（13 個 unit）：prompt 組裝 / generate 5 種 fallback / grade 通過 + 不通過 + LLM 不可用 + StrictBool ValidationError + 空 feedback 正規化
- `backend/tests/test_comprehension_variation_route.py`（10 個 HTTP 整合）：401 / generate 持久化 + 清空舊 / 422 非 coding / 503 LLM 失敗 / 跨使用者 404 / 400 未先 generate / grade 通過 / grade LLM 失敗 fallback / 跨使用者 grade 404
- 全套 293 tests 全綠（270 → 293，+23 個新測試，零 regression）

### 設計關鍵
- **題型限制**：variation 僅對 coding 有效（其他 → 422 VARIATION_NOT_APPLICABLE）；MC/fill_blank 的「變體」概念意義有限
- **Storage**：完整題目 payload（stem + starter_code + test_cases + concept_focus）JSON 編碼存 `comprehension_prompt`
- **test_cases 公開**：學生需看 test_cases 才知道目標 I/O，與 predict_output 的「藏 expected」不同
- **「禁用 AI」屬前端責任**：variation 流程不串接 chat / EDF / hint，純 LLM 出題 + 評分閉環；前端 UI 應隱藏 chat panel（後續 UI task 處理；docstring 註明 design intent）
- **保守 fallback**：grade LLM 失敗 → `passed=False`（避免錯給通過拉高 mastery 信心度，與 EPL 的 `passed=None` 不同 — Variation 是「最後一關」更謹慎）
- **StrictBool**：拒絕 LLM 文字噪音 `"yes"` 被隱式轉為 True；保證 passed 真實反映 LLM 判斷
- **拆檔**：variation.py 原 269 行 → 抽 `_call_llm_json` helper 後 242 行；route 拆獨立檔避免 comprehension.py 超 250

---

## [2026-05-05] — Phase 2-6c：預測輸出驗證（自動生新測資 + 兩階段比對）

### 新增（Service）
- `backend/services/comprehension/predict_output.py`（199 行）：
  - `PredictGenerationResult` / `PredictGradeResult` dataclass（frozen）
  - `normalize_output(text)` — trim + 折疊內部空白 + 去空行（Stage 1 嚴格比對前置）
  - `generate_predict_test(question, student_code)` — LLM 生新測資 + expected
  - `grade_predict_answer(...)` — 兩階段：嚴格 → LLM 語意 → fallback mismatch
  - `match_method` ∈ {exact, semantic, mismatch}
- `backend/services/comprehension/predict_output_prompts.py`（86 行）：
  - `build_generate_prompt`：強調「不重複 test_cases」+「對學生實際程式」推理 expected（含 bug 行為）
  - `build_semantic_grade_prompt`：判斷「語意一致」（允許格式差異 / 拒絕邏輯錯誤）
- `backend/services/comprehension/orchestrator.py`（+108 行）：
  - `start_predict_for_answer` — 拒非 coding（422）→ LLM → JSON 寫入 prompt（input + expected）+ 清空舊 answer/passed
  - `submit_predict_for_answer` — 從 prompt 解 JSON → 比對 → 寫 answer/passed

### API
- `backend/api/routes/comprehension.py`（242 行，+68）：
  - `POST /comprehension/{id}/predict_output/generate` — 回 input；不洩漏 expected
  - `POST /comprehension/{id}/predict_output/grade` — body `{predicted_output: str}`；回 passed + match_method + expected_output（學生已答完可對照）
  - `PredictGenerateOut` / `PredictGradeOut` response schemas

### 測試
- `backend/tests/test_comprehension_predict.py`（16 個 unit）：normalize 5 案 / generate 成功 + 4 種 fallback / grade exact / normalize match / semantic 通過 / semantic 不通過 / LLM unavailable + exception fallback
- `backend/tests/test_comprehension_predict_route.py`（11 個 HTTP 整合）：401 / generate 持久化 + hide expected / 清空舊 / 422 非 coding / 503 LLM 失敗 / 跨使用者 404 / 400 未先 generate / exact 通過 / mismatch fallback / 跨使用者 grade 404
- 全套 270 tests 全綠（243 → 270，+27 個新測試，零 regression）

### 設計關鍵
- **題型限制**：predict_output 只對 coding 有意義（其他 → 422 PREDICT_OUTPUT_NOT_APPLICABLE），避免「對 MC 預測輸出」這種無意義操作
- **expected 不洩漏**：generate response 只回 `test_input`；server 把 `{"input", "expected"}` 用 JSON 編碼存入 `comprehension_prompt`，grade 時解出比對
- **expected 對學生實際程式**：LLM 推理時被告知「對學生這份程式（含可能的 bug）」的輸出，而非題目正解 — 教學目標是「能否預測自己程式行為」
- **兩階段比對**：先嚴格 normalize（trim + 折疊空白）→ 不通過再 LLM 語意 → 任一通過即 passed=True；學生友善（容忍 `1, 2, 3` vs `1 2 3`）但保留精確性（順序 / 數值錯誤一律不過）
- **LLM 失敗對稱**：generate → 503；grade Stage 2 失敗 → fallback 用 Stage 1 結果（mismatch passed=False，不擋學生流程）
- **expected 即時回前端**：grade response 帶 `expected_output`，學生答完可自我對照學習

---

## [2026-05-05] — Phase 2-6b：EPL 驗證（LLM 出題 + 評分學生回答）

### 新增（Service）
- `backend/services/comprehension/epl.py`（159 行）— LLM 客戶端 + dataclass + async 流程：
  - `EplGenerationResult` / `EplGradeResult` dataclass（frozen）
  - `generate_epl_prompt(question, student_answer)` — 出 EPL 題；失敗回 prompt=None
  - `grade_epl_answer(question, student_answer, epl_prompt, epl_answer)` — 評分；失敗回 fallback
  - 評分 3 面向：conceptual_correctness / specificity / causality；passed = (avg ≥ 0.6)
- `backend/services/comprehension/epl_prompts.py`（111 行）— 純 prompt 模板獨立檔（避免 epl.py 超過 250 行硬性限制）：
  - `format_student_answer` — 題型決定格式（coding 出 code block / MC 解析選項文字 / fill_blank 列出填空）
  - `build_generate_prompt` — 生成 EPL 題的 system prompt
  - `build_grade_prompt` — 評分學生 EPL 回答的 system prompt
- `backend/services/comprehension/orchestrator.py`（106 行）— 整合 LLM + DB：
  - `start_epl_for_answer` — 取作答 + 題目 → LLM → 寫 type/prompt + 清空舊 answer/passed
  - `submit_epl_for_answer` — 校驗已 generate → LLM → 寫 answer/passed
  - LLM 失敗：generate → 503；grade → 200 但 passed=None（不擋學生）

### API
- `backend/api/routes/comprehension.py`（174 行）：
  - `POST /comprehension/{student_answer_id}/epl/generate` — 出題（重置語意）
  - `POST /comprehension/{student_answer_id}/epl/grade` — 評分，body `{epl_answer: str}`
  - `EplGenerateOut` / `EplGradeOut` response schemas（細項分數即時回傳，不入庫）

### 測試
- `backend/tests/test_comprehension_epl.py`（16 個 unit）：format / prompt building / LLM 成功 / fallback (no client / exception / invalid JSON / empty prompt / ValidationError) / 通過閾值 / 不通過 / feedback 空字串正規化
- `backend/tests/test_comprehension_epl_route.py`（9 個 HTTP 整合）：401 / generate 持久化 + 清空舊 / generate LLM 失敗 503 / generate 跨使用者 404 / grade 未先 generate 400 / grade 成功 / grade LLM 失敗 200 但 passed=None / grade 跨使用者 404
- 全套 243 tests 全綠（218 → 243，+25 個新測試，零 regression）

### 設計關鍵
- **重置語意**：generate 每次都清空 `comprehension_answer/passed`，避免新 prompt 搭配舊回答的資料錯亂
- **順序強制**：grade 必須先 generate（無 prompt → 400 EPL_NOT_STARTED），確保 LLM 評分時有完整脈絡
- **失敗策略不對稱**：generate 失敗 503（前端可重試）；grade 失敗 200 + passed=None（學生回答仍持久化方便重試評分，不擋流程）
- **細項分數不入庫**：schema 只有 `comprehension_passed: bool`；conceptual/specificity/causality 屬即時回饋，前端顯示一次即可，不需歷史追蹤
- **拆檔對齊 250 行限制**：epl.py 原 264 行 → 拆出 epl_prompts.py（純字串模板）後 159 行，符合 CLAUDE.md 硬性門檻

---

## [2026-05-05] — Phase 2-6a：Post-Solution Comprehension Check 持久化基礎

### 新增（Schema / Migration）
- `backend/alembic/versions/b8c9d0e1f2a3_add_comprehension_to_student_answers.py`（66 行）— `student_answers` 表加 4 個 nullable 欄位：
  - `comprehension_type` (varchar 20, nullable) — `epl` / `predict_output` / `variation`
  - `comprehension_prompt` (text, nullable) — 系統出的驗證題目
  - `comprehension_answer` (text, nullable) — 學生回答
  - `comprehension_passed` (boolean, nullable) — 是否通過驗證
  - CHECK constraint：`comprehension_type IS NULL OR ∈ enum`

### ORM
- `backend/models/quiz.py`：`StudentAnswer` 加 4 欄位 + `ComprehensionType(str, Enum)`（EPL / PREDICT_OUTPUT / VARIATION）
- `backend/models/__init__.py`：export `ComprehensionType`

### Service
- `backend/services/comprehension/__init__.py` + `crud.py`（79 行）：
  - `get_comprehension(db, student_answer_id, user_id)` — 擁有權檢查（非本人 → 404）
  - `upsert_comprehension(db, student_answer_id, user_id, payload)` — partial upsert，未提供欄位保留原值
  - `ComprehensionUpdate` dataclass

### API
- `backend/api/routes/comprehension.py`（108 行）：
  - `GET /comprehension/{student_answer_id}` — 讀取 4 欄位狀態
  - `PUT /comprehension/{student_answer_id}` — partial upsert
  - 422 type 非法 / 404 跨使用者或不存在
- `backend/main.py`：註冊 `comprehension_router`

### 測試
- `backend/tests/test_comprehension_route.py`（10 個整合測試）：401 未登入 / GET 初始狀態 null / 完整 PUT / partial PUT 保留欄位 / 422 type 非法 / 404 跨使用者 / 404 不存在
- 全套 218 tests 全綠（208 → 218，+10 個新測試，零 regression）

### 設計關鍵
- **nullable + 同表擴充**：comprehension 為「解題後選擇性驗證」，多數作答不觸發；nullable 欄位比 1:1 副表省一個 join
- **404 而非 403**：跨使用者一律回 STUDENT_ANSWER_NOT_FOUND，避免列舉攻擊揭露存在性（與 reflection / chat 服務一致）
- **partial PUT**：未提供欄位保留原值，方便分階段寫入（例：先存 prompt，學生答完再寫 answer + passed）
- **Service 不做 LLM**：本層僅持久化；EPL / 預測輸出 / 變體題的 LLM 生成與評分屬 2-6b/c/d
- **不加 `comprehension_completed_at`**：嚴格對齊 db-schema.md 4 欄位規格；2-6e 動態觸發頻率需要時再 migrate

---

## [2026-05-04] — Phase 2-5e：反思內容注入 EDF Pipeline（AI Tutor 可引用學生計畫）

### 新增（Service 層）
- `backend/services/edf/reflection_context.py`（66 行）— 純函式格式化 helper：
  - `format_reflection_for_evidence`：簡短版（步驟 + 預期概念），給 Evidence LLM 判斷學生意圖
  - `format_reflection_for_feedback`：詳細版（含理解/步驟/概念/補充回答/品質分數），給 Feedback LLM 引用做蘇格拉底式提問
  - 空輸入 / None / 無有效內容 → 回 `""`，caller 直接 `if block: ...`
  - 引導建議內建「嚴禁直接幫學生補完計畫」規則，避免 LLM 變成代寫工具

### 整合（EDF Pipeline）
- `services/edf/evidence.py`：`analyze_evidence()` 加 `reflection_summary: str = ""`，注入 user prompt 結尾（避免稀釋程式碼分析）
- `services/edf/feedback.py`：`build_system_prompt()` 加 `reflection_block: str = ""`，順序 `preamble → persona → strategy → context → reflection → rag`（對齊 `.claude/rules/edf-pipeline.md`）；`generate_feedback()` 透傳
- `services/chat.py`：`interact()` 加 `reflection_id: UUID | None`；`_load_reflection_safely` 做 best-effort 載入 + **權限隔離**（user_id 不符視為不存在）；找不到/異常都回 None 不擋流程
- `api/routes/chat.py`：`InteractRequest` 加 `reflection_id` 欄位，透傳到 service

### 前端整合
- `web/hooks/use-chat.ts`：`sendMessage` 自動讀 sessionStorage 中 active reflection_id 並帶入 `/chat/interact` body — 學生在 Workspace 開始反思後，整個對話 session 內 AI 都能引用其計畫

### 測試
- `tests/test_reflection_context.py`（11 個 unit）：None / 空輸入 / steps trim 重編號 / Evidence 簡短不含 followup / Feedback 詳細含品質分數 / quality_score=None 不顯示 % / quality_score=0 顯示 0%
- `tests/test_feedback_prompt.py`（+3）：無 reflection 不出現 block / 有 reflection 注入內容 / **順序檢查 reflection 在 RAG 之前**
- `tests/test_chat.py`（+4）：注入 evidence/feedback 兩層 / 未傳 id 兩層收空字串 / **權限隔離（他人 reflection_id 被忽略）** / 不存在的 id fallback 為空
- 全套 208 tests 全綠（190 → 208，+18 個新測試，零 regression）

### 設計關鍵
- **Evidence vs Feedback 分版**：Evidence 收簡短版（避免反思內容稀釋程式碼分析），Feedback 收詳細版（讓 AI 能直接引用學生計畫做提問）
- **權限隔離在 service 層**：`_load_reflection_safely` 檢查 `row.user_id != user_id`，避免 ID 嗅探攻擊
- **永遠 best-effort**：reflection 載入失敗（DB 異常 / 不存在 / 非本人）都不擋教學流程，與 mastery / RAG 容錯哲學一致
- **prompt 順序明確**：`build_system_prompt` 把 reflection_block 放在 context 之後、rag 之前，由測試 `test_reflection_block_appears_before_rag_block` 強制保證

### 驗證
- ESLint / TypeScript / pytest 全綠
- next build：見後續驗證

## [2026-05-04] — Phase 2-5d：Workspace 反思計畫側邊欄

### 新增（持久化 + API helper）
- `web/lib/active-reflection.ts`（48 行）— sessionStorage helper：`getActiveReflectionId` / `setActiveReflectionId` / `clearActiveReflectionId`；同 tab 變更透過 `active-reflection-change` custom event，跨 tab 透過 storage event
- `web/lib/reflection.ts` 補 `getReflection(id)`

### 新增（Sidebar 元件）
- `web/components/reflection/use-active-reflection.ts`（85 行）— hook：訂閱 sessionStorage / event → 呼叫 GET /reflection；404 自動清過期 ID 顯示空狀態
- `web/components/reflection/reflection-sidebar.tsx`（114 行）— 主元件：載入/錯誤/空狀態/顯示模式/編輯模式 5 種狀態切換
- `web/components/reflection/reflection-sidebar-view.tsx`（109 行）— 顯示模式：QualityChip + 三 Section（理解/步驟/概念）+ AI 教練建議區塊 + 編輯/清除按鈕
- `web/components/reflection/reflection-sidebar-edit.tsx`（95 行）— 編輯模式：復用 `ReflectionForm`；存檔呼叫 PATCH /reflection/{id}（後端會自動重新評分）

### Workspace 整合
- `web/components/workspace/toolbar.tsx`（55 → 80 行）— 最左加入 ListChecks toggle 按鈕；有 active reflection 時顯示綠色 dot 提示
- `web/app/(app)/workspace/page.tsx`（103 → 153 行）— 反思側邊欄為左側 Panel（resizable，default 28% / min 20% / max 40%）；進入頁面若有 active reflection 自動展開；訂閱 sessionStorage 變化更新 Toolbar dot
- `web/components/quiz-demo/question-display.tsx` — ReflectionSummary 加「前往 Workspace 作答」`<Link>` 按鈕，點擊時 `setActiveReflectionId` 寫 sessionStorage

### 設計關鍵
- **不擴後端**：純前端持久化（sessionStorage），不需新增 list/latest endpoint
- **同 tab 通知**：`storage` event 預設只在「其他」tab 觸發；用 `CustomEvent('active-reflection-change')` 補上同 tab 場景
- **404 自動清過期**：反思被刪除時清掉 sessionStorage，UI 退回空狀態而非顯示錯誤
- **元件邊界**：Sidebar 全部 prop-driven + hook 化，方便 3-1e 練習 tab 直接復用
- **R8.1 / R8.2 合規**：error UI 用 `border-l-2 + bg-surface-2`；toggle dot 用實心 `bg-accent-green` 純功能性，無半透明色填充；icon 全 lucide-react 無 emoji 符號字
- **檔案大小**：所有檔案 ≤ 153 行，遠低於 250 硬性線

### 驗證
- ESLint / TypeScript / next build：全綠

## [2026-05-04] — Phase 2-5c 修正：先讀題再反思（PRIMM 對齊）

### 問題
原 demo 流程「拿題目 → 立即彈反思 modal」，學生在沒看到題目的狀態下被要求反思，違反 PRIMM 對「反思必須針對具體題目」的要求。

### 修正
- 新增 `preview` phase：拿到題目後先進入 preview 階段，題目持續顯示供讀題
- preview footer 顯示「讀完題目了嗎？」+ 醒目「開始反思」按鈕，學生主動點才彈 modal
- reflecting phase：modal 開啟，題目仍在背景；新增提示「請完成反思後再回到題目作答」
- ready phase：題目持續顯示 + 反思摘要（顯示「反思已完成 — 你可以開始作答了」）
- 取消反思 modal → 回到 preview（不丟棄已生成的題目）

### 拆檔
- `web/components/quiz-demo/question-display.tsx`（162 行）— 新檔，phase-aware 題目顯示元件，三 phase 共用 Header / Stem / StarterCode，footer 依 phase 切換
- `web/app/(app)/quiz/page.tsx`（226 → 153 行）— 流程簡化，題目展示交給 QuestionDisplay

### 驗證
- ESLint / TypeScript 無錯誤；所有檔案 < 250 行

## [2026-05-04] — Phase 2-5c：Pre-Coding Reflection 表單 UI + Quiz demo 觸發點

### 新增（Reflection 元件）
- `web/lib/reflection.ts`（63 行）— types + API helper：`Reflection` / `CreateReflectionPayload` / `PatchReflectionPayload` + `createReflection` / `patchReflection`
- `web/components/reflection/reflection-form.tsx`（211 行）— 受控三欄位表單：
  - `problem_understanding`（textarea，重述題目）
  - `planned_steps`（動態列表，逐步增刪步驟）
  - `expected_concepts`（input，預期會用到的概念）
  - `isReflectionFormValid()` / `toBackendPayload()` 工具函式統一驗證與序列化
- `web/components/reflection/reflection-followup.tsx`（84 行）— LLM 追問 + 補答 UI；含 `QualityBar`（紅 < 0.4 / 橘 < 0.6 / 綠 >= 0.6）
- `web/components/reflection/reflection-flow.tsx`（161 行）— Modal 容器 + 狀態機：
  - `form → submitting → (approved | followup) → submitting → ...`
  - `MAX_FOLLOWUP_ROUNDS=2`：第二輪後提供「已盡力，直接看題」放行（避免無限 loop）
  - LLM 失敗（quality_score=null）視為通過 → 不擋學生
  - 內容 `ReflectionFlowContent` 條件 mount，open 切換時 state 自然重置（避開 React 19 `react-hooks/set-state-in-effect`）
- `web/components/reflection/reflection-flow-parts.tsx`（151 行）— 拆出 `FlowHeader` / `FlowBody` / `FlowFooter` / `humanizeReflectionError`，主檔控制在 250 行硬性線下

### Quiz demo 觸發點
- `web/app/(app)/quiz/page.tsx`（226 行）— Quiz 占位頁改造為反思流程 demo：
  - 「開始示範」→ `POST /quiz/generate type=coding bloom_level=3` → 立刻彈出 ReflectionFlow modal
  - 反思放行後顯示題目本體（題幹 / starter_code / 反思摘要）
  - 錯誤訊息友善處理：`QUIZ_VALIDATION_RETRY_EXHAUSTED` / `QUIZ_UNAVAILABLE` / 401 / 一般錯誤
  - 完整 Quiz UI 仍屬 Phase 3-2；本頁僅為 2-5c 觸發點驗證

### 設計關鍵
- **R8.1 合規**：所有 error / 強調 UI 一律用 `border-l-2 border-accent-X bg-surface-2`（與 Toast 規格一致），不用 `bg-accent-X/N` 半透明色填充
- **265 行 → 拆檔**：`reflection-flow.tsx` 一度寫到 328 行違反 250 行硬性線，依 CLAUDE.md 規則拆出 `reflection-flow-parts.tsx`；所有檔案都壓在 230 行內
- **純受控元件設計**：每個元件 prop-driven，無內建 store / context — 為 2-5d 側邊欄與 3-1e 練習 tab 復用做準備
- **狀態機與 React 19 lint**：Dialog 內容用 `{open && <Content />}` 條件 mount 取代 `useEffect` 重置 — 通過 `react-hooks/set-state-in-effect`

### 驗證
- ESLint：無錯誤
- TypeScript：無錯誤
- next build：exit 0（warnings 為 Google Fonts 離線抓取，與本次改動無關）

## [2026-05-04] — Phase 2-5b：反思品質評估 service（LLM 評分 + 蘇格拉底式追問）

### 新增（Service 層）
- `backend/services/reflection/evaluate.py`（170 行）— LLM 評分服務：
  - 三面向獨立評分（0–1）：`understanding_score` / `plan_quality_score` / `concept_recall_score`
  - `quality_score` = 三者平均（簡單可解釋；非加權）
  - `QUALITY_THRESHOLD = 0.6`：低於門檻才回 `followup_question`（蘇格拉底式追問，針對最弱面向）；高於門檻 LLM 多嘴的 followup 一律清成 None
  - **無 API key / LLM 異常 / parse error / schema 違反** → 回 fallback `ReflectionEvaluation(None, None, None, None, None)`，不丟例外（不擋反思寫入）
  - Pydantic `_EvaluatorResponse` 對 LLM 輸出做 ge=0/le=1 校驗，超範圍直接 fallback
  - learning_unit 來源不需題目脈絡也能評分（question 可傳 None）

### 整合（CRUD flow）
- `services/reflection/crud.py`：
  - `create_reflection`：INSERT 後 flush 取 id → 跑 LLM → 寫回 quality_score / followup_question → commit；單一 transaction
  - `update_reflection`：任一內容欄位變動 → 重新評分（PRIMM Modify 階段）；no-op PATCH 不呼叫 LLM
  - 拆分 `_validate_source_for_create`（404 守門）vs `_load_question_best_effort`（update 找不到題目仍能更新）

### 測試
- `backend/tests/test_reflection_evaluate.py`（9 個 unit）— 高分清空 followup / 低分保留 followup / 空白 followup 標準化 / 無 API key fallback / LLM 異常 fallback / JSON parse error / Pydantic schema 違反 / 分數超範圍 / learning_unit 無題目脈絡
- `tests/test_reflection_service.py` 加 `_mock_evaluate` autouse fixture（避免測試打 OpenAI），新增 5 個 evaluate-aware 測試（高分 / 低分含 followup / LLM unavailable / PATCH 補答後再評分 / no-op 不呼叫 LLM）
- `tests/test_reflection_route.py` 加 `_mock_evaluate` autouse fixture，新增 2 個 HTTP 整合測試（POST 回 quality_score+followup / PATCH 補答後清空 followup）
- 全套 190 tests 全綠（174 → 190，+16 個新測試）

### 設計關鍵
- **三面向獨立評分而非單一 score**：可解釋性 + 為 2-5b 追問選最弱面向提供依據；UI 將來可顯示三個 sub-score 條
- **LLM 失敗永遠 fallback 不阻擋寫入**：與 chat/quiz 容錯哲學一致；學生反思流程不能因 OpenAI 抖動中斷
- **followup 高分強制清空**：避免 LLM 在合格反思上多嘴干擾學生（threshold 行為由本層保證，不靠 prompt 約束）
- **PATCH 重評分時 question best-effort**：題目即使被刪反思仍可更新（不造成 reflection 孤兒）

## [2026-05-04] — Phase 2-5a：Pre-Coding Reflection schema + API（建立 / 取得 / 更新）

### 新增（DB / Model 層）
- `backend/alembic/versions/a7b8c9d0e1f2_create_reflections_table.py` — 新增 `reflections` 表：
  - 欄位對齊 db-schema.md 跨模組區塊（problem_understanding / planned_steps JSON / expected_concepts / quality_score / followup_question / followup_answer / is_modified / created_at / updated_at）
  - `source_type` 用 `String + CHECK`（quiz / learning_unit），延續 quiz 表慣例避開 PG ENUM 雙重寫法
  - `(user_id, source_type, source_id)` UNIQUE → 同一學生對同一題只允許一份反思
  - `quality_score` CHECK 0.0–1.0、index：`ix_reflections_user_id` + `ix_reflections_source`
- `backend/models/reflection.py`（83 行）— `Reflection` ORM + `ReflectionSourceType` 列舉
- `backend/models/__init__.py` — 註冊 `Reflection` 至 `Base.metadata`

### 新增（Service 層）
- `backend/services/reflection/__init__.py` + `crud.py`（118 行）— 純 CRUD：
  - `create_reflection`：quiz 來源驗證 `Question.id` 存在（404 `REFLECTION_SOURCE_NOT_FOUND`）；learning_unit 暫不驗證（表尚未建立）；UNIQUE 衝突回 409 `REFLECTION_ALREADY_EXISTS`
  - `get_reflection`：權限隔離 — 非本人擁有回 404（避免列舉攻擊揭露存在性）
  - `update_reflection`：任一欄位變動即標 `is_modified=True` + 刷新 `updated_at`；payload 全空時不標 modified
  - **LLM 品質評分留給 2-5b** — 本層不打 LLM

### 新增（API 層）
- `backend/api/routes/reflection.py`（131 行）— 三個端點（對齊 api-spec.md）：
  - `POST /reflection`（201）— 建立反思
  - `GET /reflection/{id}` — 取得反思（owner-only）
  - `PATCH /reflection/{id}` — 更新反思（補充 followup_answer / 修改 planned_steps）
  - `_parse_source_type` 對非法 source_type 回 422 `INVALID_SOURCE_TYPE`
- `backend/main.py` — 註冊 `reflection_router`

### 測試
- `backend/tests/test_reflection_service.py`（9 個 unit）— create / get / update 三組路徑：成功、404 source、duplicate 409、權限 404、no-op 更新、LEARNING_UNIT 略過驗證
- `backend/tests/test_reflection_route.py`（9 個 HTTP）— 401 / 201 / 422 / 404 / 409 / GET / PATCH / 跨 user 權限隔離
- 全套 174 tests 全綠（新增 18 個）；alembic upgrade 在 dev PG 落地，schema/index/CHECK/UNIQUE/FK 對齊

### 設計關鍵
- **source_id polymorphic UUID**：指向 questions.id 或 learning_units.id（Phase 3-1a 才建），不建 FK，靠 service 層在 quiz 來源驗證
- **權限隔離不洩漏存在性**：他人反思一律回 404 而非 403，避免 ID 列舉攻擊
- **LLM 評分解耦**：`quality_score` / `followup_question` 保持 nullable，2-5b 注入時不需 schema 變動
- **2-5a 範圍嚴守**：純 CRUD + schema，不含 UI / EDF 注入（後者在 2-5c~e）

## [2026-05-04] — Phase 2-4e：Quiz API 端點（Phase 2-4 完成）

### 新增（service 層）
- `backend/services/quiz/grade.py`（56 行）— 純判分：
  - MC：比 `selected_index == content.answer_index`
  - Fill：trim + casefold 後逐項比對 answers list
  - Coding：MVP 不自動判分（is_correct=False，feedback 提示「待 Judge0 整合」）
- `backend/services/quiz/orchestrator.py`（171 行）— 串接 Select/Generate/Validate/Grade/Mastery：
  - `generate_for_student(db, user_id, type, bloom)`：弱項 fallback 到 syntax-basic；validate 失敗 retry up to 2；retry 全敗 → 503 `QUIZ_VALIDATION_RETRY_EXHAUSTED`
  - `submit_answer(db, user_id, question_id, answer, ...)`：判分 → 寫 StudentAnswer → 餵 EvidenceResult 給 `update_mastery` → 404/400 錯誤
  - `list_history(db, user_id, page, limit)`：分頁查詢

### 新增（API 層）
- `backend/api/routes/quiz.py`（161 行）— 三個端點：
  - `POST /quiz/generate`：mask 答案欄位後回傳；MC 不回 `answer_index`、Fill 不回 `answers`、Coding 只給 `starter_code`
  - `POST /quiz/submit`：作答後才回完整 `correct_content` + `explanation`
  - `GET /quiz/history`：分頁列出該 user 的 StudentAnswer

### 變更
- `backend/main.py` — 註冊 `quiz_router`
- `backend/services/quiz/__init__.py` — 增加 `grade_answer` / `generate_for_student` / `submit_answer` / `list_history` 匯出

### 設計關鍵
- **答案 mask**：`_mask_content_for_student()` 在 GET 端點移除答案欄位，避免 DOM 內洩漏；submit 後才把完整 content 回給前端做反饋
- **validate retry**：generate 失敗（LLM 出爛題）就 rollback 重試；連續 3 次都壞才回 503，避免無限呼叫 LLM
- **submit 同時更新 mastery**：把 `is_correct` 包成 `EvidenceResult` 餵 `update_mastery`，讓 BKT confidence 累積；mastery 失敗不阻擋 student_answer 寫入
- **grade.py 與 orchestrator.py 拆檔**：純判分邏輯（無 DB / LLM）獨立，方便單元測試

### 驗證（自動）
- 8 grade 測試（MC/Fill/Coding 各邊界） + 7 route HTTP 整合測試（auth / mask / submit / history / 404 / 400）
- 全套 **156 passed** ✓

### Phase 2-4 完整收尾
- ✅ 2-4a Schema
- ✅ 2-4b Select（弱項 + 中心度加權）
- ✅ 2-4c Generate（LLM + RAG 注入）
- ✅ 2-4d Validate（三面向 LLM 自審）
- ✅ 2-4e API 端點

## [2026-05-04] — Phase 2-4d：LLM 自我審查題目品質

### 新增
- `backend/services/quiz/validate.py`（167 行）— `validate_question(db, question) -> ValidationReport`：
  - 對 generate 出來的題目做第二次 LLM call，三面向審查：
    1. **answer_correct**：題目宣稱的答案在 C++ 語法/邏輯上是否真的對
    2. **concept_fits**：題目實際測試的概念是否吻合 `intended_concept_tags`
    3. **bloom_appropriate**：題目要求的認知層級是否 ≤ 目標 Bloom（避免進階題給初學者）
  - 三項全 pass → `question.validated=True`（caller commit）；任一 fail → 不動 validated，回 issues
  - 沿用 `response_format json_object` + Pydantic `_ValidatorResponse` 二次驗證 + 分層錯誤
  - 與 generate 共用同一 transaction（service 不 commit）
- `backend/tests/test_quiz_validate.py`（208 行）— 8 個測試：
  - Pass / 三面向各自 fail / 多面向同時 fail（issues 列出全部）
  - LLM 錯誤分層：例外 / 非 JSON / 缺欄位

### 設計決策
- **回傳 `ValidationReport` 而非 raise on fail**：失敗是正常情境（LLM 也會生出爛題），caller（2-4e API）需要看 issues 決定 retry 還是丟棄；只有「LLM 不可用」才 raise
- **三面向 AND**：三題都對才算 pass；任一不對都回 issues 各別說明，方便 caller log + 改進 prompt
- **不重新 fetch question**：caller 已 db.add 並把物件交來，直接 mutate `question.validated`；transaction 一致性靠 caller 統一 commit

### 驗證（自動）
- 8 個新測試 + 133 既有 = **141 passed** ✓

## [2026-05-04] — Phase 2-4c：LLM 出題 + RAG 教材注入

### 新增
- `backend/services/quiz/generate.py`（221 行）— `generate_question(db, concept, question_type, difficulty, bloom_level)`：
  - 三種題型各自 Pydantic content 模型（`_MCContent` / `_FillContent` / `_CodingContent`）做二次驗證
  - System prompt 含 concept 完整 metadata（tag/zh/en/category/description）+ 題型 schema hint + 撰寫規則
  - User prompt 注入 `services.rag.retrieve_chunks` 抓回的 top-3 教材片段；RAG 失敗（DB / embedding API down）靜默 fallback 空 list 仍能出題
  - 沿用 `evidence.py` 的 `response_format json_object` + JSON 二次解析 pattern；錯誤分層（LLM_ERROR / LLM_PARSE_ERROR / LLM_VALIDATION_ERROR）
  - 寫入 `questions.source='generated'`、`validated=False`，等 2-4d Validate 過審
- `backend/tests/test_quiz_generate.py`（249 行）— 8 個測試：
  - 三種 type 各自 success path（解析正確、Question 欄位齊全）
  - 錯誤分層：非 JSON / schema 不符（缺 answer_index）/ LLM 例外
  - RAG 失敗仍能出題
  - DB 寫入欄位完整驗證

### 設計決策
- **content shape 二次驗證**：LLM 即使遵循 prompt 仍可能漏欄位，每個 type 用 Pydantic 模型驗證後才寫 DB；`_MCContent` 還有 `field_validator` 確保 `answer_index < len(options)`
- **沿用 json_object 而非 json_schema strict**：與 evidence.py 一致；strict 模式對 model output 限制較嚴可能誤拒合理題目
- **RAG 容錯**：`_fetch_rag_chunks_for_concept` 包 try/except，與 EDF Feedback 的 `fetch_rag_chunks_safe` 同款設計（增強而非必要）
- **不 commit**：caller 負責 transaction（讓 2-4d Validate 可以在同 transaction 補標 validated=True 後再 commit）
- **`patched_llm` contextmanager**：tests/test_quiz_generate.py 改用 `contextlib.contextmanager` 合併兩個 patch，避免原本 `_patch_llm(x)[0], _patch_llm(x)[1]` 重複呼叫的 anti-pattern

### 驗證（自動）
- 8 個新測試 + 125 既有 = **133 passed** ✓

## [2026-05-04] — Phase 2-4b：弱項概念選取 + 知識圖譜中心度加權

### 新增
- `backend/services/quiz/select.py`（83 行）— `select_weak_concepts(db, user_id, top_k=5)`：
  - 弱項定義：`confidence < WEAK_THRESHOLD (0.4) AND exposure_count >= 1`（未互動不算弱）
  - 圖譜中心度加權：score = `(1 - confidence) × (1 + CENTRALITY_BONUS × out_degree)`，被多個概念依賴的弱項排前面
  - Cold-start（無 mastery rows）回 []，由 2-4c Generate 自行決定（例如挑入門 concept）
- `backend/services/quiz/__init__.py` — 公開 API
- `backend/tests/test_quiz_select.py`（180 行）— 7 個測試：
  - 邊界：no mastery / 只有強項 / unexposed low-confidence 不入選
  - 排序：純弱項 confidence 升冪、中心度加權促 hub 概念到前
  - 限制：top_k 截斷、constant sanity

### 設計決策
- **中心度加權**：foundation 概念（如 syntax-basic 有 5 個後續依賴）若是弱項，補強的價值高於孤立弱項；公式 `1 + 0.2 × out_degree` 每多一個依賴 +20% 優先度
- **不擴展未追蹤的鄰居**：只在「已有 student_mastery row 且 confidence < 0.4」中挑；前置概念若沒 row 表示學生沒接觸，不該主動測試（避免擾亂學生）
- **Cold-start 回空 list**：本層只負責「弱項」語意；2-4c 自己處理「怎麼開始」

### 驗證（自動）
- 7 個新測試 + 118 既有 = **125 passed** ✓

## [2026-05-04] — Phase 2-4a：questions + student_answers schema

### 新增
- `backend/alembic/versions/f6a7b8c9d0e1_create_questions_and_answers.py` — 智慧出題基礎表：
  - **questions**：id / type (CHECK in 3 values) / concept_tags JSON / bloom_level smallint (CHECK 1-6) / difficulty smallint (CHECK 1-5) / content JSON / explanation / source (CHECK in 3 values) / validated bool / created_at；3 個 secondary index (type / bloom_level / difficulty)
  - **student_answers**：id / user_id FK CASCADE / question_id FK CASCADE / answer JSON / is_correct / time_spent_seconds (nullable, CHECK ≥0) / hint_level_used smallint (CHECK 0-5) / feedback / answered_at；composite index (user_id, answered_at) 供歷史查詢
- `backend/models/quiz.py` — `Question` + `StudentAnswer` ORM + `QuestionType` / `QuestionSource` 字串列舉
- 註冊至 `models/__init__.py`

### 設計取捨
- **enum 改 `String + CHECK`**：先前 user_role / message_role / concept_edge_type 三次踩過 PG ENUM enum.value/.name 同款坑，新欄位（type / source）改用字串 + CHECK 約束從根本避免；ORM 提供 `QuestionType` / `QuestionSource` 字串列舉維持型別語意
- **bloom_level / difficulty / hint_level 用 SmallInteger + CHECK**：與 student_mastery 同款，避開 PG ENUM；CHECK 保證範圍
- **`concept_tags` 用 JSON 不用 PG `text[]`**：避免 PG-only 型別讓 SQLite 測試壞；題庫規模 < 1000 全表掃可接受，未來若需 GIN index 再 migrate
- **content / answer 用 JSON**：題幹/選項/答案形狀依 type 不同（multiple_choice / fill_blank / coding），JSON 容納所有形狀；shape 驗證留給 application 層（2-4d Validate stage）
- **comprehension_* 擴充欄位**留給 Phase 2-6 自己的 migration，本次不加

### 驗證（自動）
- `alembic current` → `f6a7b8c9d0e1 (head)` ✓
- 118 個測試全綠（zero regression）✓
- DB schema：questions 10 欄 / 4 indexes / 4 checks；student_answers 9 欄 / 3 indexes / 2 checks / 2 FK CASCADE ✓

## [2026-05-04] — Phase 2-3c：圖譜節點精熟度著色（Phase 2-3 完成）

### 新增（後端）
- `backend/services/mastery/queries.py` — `get_user_mastery_summary(db, user_id)` JOIN concepts，回傳 `MasterySummaryEntry` 列表（tag + confidence + counts + bloom_level）
- `backend/api/routes/concepts.py` 新增 `GET /concepts/mastery` 端點（auth-gated），回傳 `MasteryEntryOut[]`；無互動的 concept 不在回應中
- 3 個測試（401 未授權 / 空 mastery 回 [] / 含資料時 tag/confidence 正確對位）

### 新增（前端）
- `web/components/knowledge/knowledge-graph-types.ts` 加 `MasteryEntry` + `MasteryBand` + `getMasteryBand(confidence)`：`mastered (≥0.8) / learning (0.4-0.8) / struggling (<0.4) / unseen (no row)`
- `web/components/knowledge/concept-detail-panel.tsx` 新增 `MasterySection` — 顯示「已掌握 / 學習中 / 需加強 / 尚未互動」+ confidence% + 互動次數

### 變更（前端）
- `web/components/knowledge/knowledge-graph-style.ts` — `toElements` 加 masteryMap 參數；新增 3 條 underlay 規則（綠/黃/紅）對應 mastery_band；unseen 不畫
- `web/components/knowledge/knowledge-graph.tsx` — 改 presentational：移除內部 fetch，改接 `data` + `masteryMap` props（120→100 行）
- `web/app/(app)/knowledge/page.tsx` — 升為 container：Promise.all 平行 fetch graph + mastery，loading/error 集中管理，下傳 mastery 給 graph 與 panel（41→95 行）

### 設計取捨
- **用 `underlay-*` 而非 `outline-*`**：Cytoscape underlay 能畫在節點底層產生「光暈」感，與我們的 ellipse + Obsidian 風格更協調；outline 邊緣較硬
- **顏色語意衝突**：mastery 用的綠/紅 也是 category 色（物件導向/記憶體）— 視為兩個獨立視覺通道（fill = subject area，underlay = proficiency），實測不會誤讀
- **無互動概念不畫圈**：避免一張全紅圖嚇到新使用者；首次互動才會出現顏色
- **fetch 上提至 page**：mastery 同時要餵給 graph（節點圈）與 panel（顯示百分比），page 層管 state 是唯一合理位置；graph 元件變 presentational 也更好測

### 已知警告
- `concept-detail-panel.tsx` 248 行（停止線 250 邊緣）— 5 個 sub-component 緊密耦合，下次再加功能必須拆檔（建議：MasterySection / NeighborSection 各獨立）

### 驗證（自動）
- 118 個測試全綠（115 既有 + 3 新增 mastery route 測試）
- TS clean ✓

### Phase 2-3 完整收尾
- ✅ 2-3a `student_mastery` schema
- ✅ 2-3b BKT 線上更新串入 chat 流程
- ✅ 2-3c 圖譜精熟度視覺化 + Detail Panel 精熟度區塊

## [2026-05-04] — Phase 2-3b：BKT 線上精熟度更新

### 新增
- `backend/services/mastery/updater.py`（148 行）：
  - `BKTParams` dataclass（prior/learn/slip/guess 四參數）+ `BKT_DEFAULT_PARAMS = (0.3, 0.3, 0.1, 0.2)` 預設值
  - `bkt_online_update(prior, correct, params)` — 標準 BKT Bayes 後驗 + learning transition，clamp 0-1
  - `update_mastery(db, user_id, evidence)` — 對 evidence.concept_tags 每個 tag lazy fetch/create `StudentMastery` row、套 BKT 更新、累計計數、bloom_level 取最大、更新 last_practiced_at；caller 負責 commit
- `backend/services/mastery/__init__.py`（15 行）— 公開 API
- `backend/tests/test_mastery_updater.py`（198 行）— 10 個測試（5 BKT 數學 + 5 整合）

### 變更
- `backend/services/chat.py` `interact()`：在 Decision 層之前呼叫 `update_mastery`；try/except 容錯（mastery 失敗不阻擋教學回應，與 RAG 同款）

### 修復 / 安裝
- `backend/.venv` 新增依賴：`pyBKT==1.4.1` + scientific stack（scipy/scikit-learn<1.7/pandas/numpy/joblib 等）— ⚠ scikit-learn 必須 `<1.7`，pyBKT 1.4.1 與 1.7+ 的 `_log_loss` API 不相容（記於 tech-debt）

### 設計決策（OSS 守則 #7）
- **pyBKT 使用策略**：套件已裝為宣告依賴；但 `Model.fit()` / `Roster` 需歷史資料才能用，cold-start 階段（無學生資料）改用標準 BKT Bayes 公式（Corbett & Anderson 1995，公開教科書數學，**非移植 OATutor JS 版**，符合 OSS 規則精神）
- **未來 Phase 5 升級路徑**：有真實互動資料後跑 `pyBKT.Model.fit(df)` 學 per-concept 參數，把 `BKTParams` 從預設值改為 fitted values 即可，**演算法本身不需改**

### 容錯設計
- update_mastery 失敗不阻擋 chat 回應（與 RAG fetch_rag_chunks_safe 同款 try/except）
- evidence.concept_tags 中不存在的 tag（LLM 產 hallucinated tag）→ skip 不擲錯

### 驗證（自動）
- 10 個新測試 + 105 既有測試 = **115 passed** ✓
- 數學正確性測試：correct 提升、incorrect 降低、邊界 [0,1] clamp、no-slip-no-guess 答對接近 1
- 整合測試：lazy create / 累計計數 / bloom 取最大 / unknown tag skip / 多 concept 同時更新 / 空 tags

## [2026-05-04] — Phase 2-3a：student_mastery 表 schema

### 新增
- `backend/alembic/versions/e5f6a7b8c9d0_create_student_mastery_table.py` — 精熟度追蹤基礎表：
  - `id` UUID PK / `user_id` FK CASCADE / `concept_id` FK CASCADE
  - `confidence` float (CHECK 0-1) — pyBKT 在 2-3b 維護
  - `exposure_count` / `success_count` / `error_count` int (CHECK ≥ 0) — EDF Pipeline 累加
  - `bloom_level` smallint nullable (CHECK 1-6 or null) — 對齊 `services/edf/models.py` BloomLevel(IntEnum)，避開 PG ENUM 同款 bug
  - `last_practiced_at` timestamptz nullable
  - `UNIQUE(user_id, concept_id)` + 2 個 FK 索引
- `backend/models/mastery.py` — `StudentMastery` ORM model，註冊至 `models/__init__.py`

### 設計重點
- **bloom_level 用 SmallInteger 不用 PG ENUM**：避開先前已踩三次的 enum.value/.name bug（UserRole / MessageRole / EdgeType），且與 EDF 既有 IntEnum 一致
- **Lazy 建列**：rows 在學生實際互動時建立，不批量初始化（避免 user × concept 笛卡兒積空白列）
- **無 created_at**：`last_practiced_at` 已涵蓋意圖；db-schema.md 也未指定

### 驗證（自動）
- `alembic current` → `e5f6a7b8c9d0 (head)` ✓
- 105 個測試全綠（zero regression）✓
- DB schema：9 欄 / 3 indexes / 3 checks / 2 FKs ✓

## [2026-05-04] — Phase 2-2e：Knowledge Graph 視覺精修 + edges seed（Obsidian Graph View 風）

### 新增
- `backend/alembic/versions/d4e5f6a7b8c9_seed_concept_edges.py` — 種 23 條邊：
  - 20 prerequisite：5 條基礎放射（syntax-basic 樞紐）+ 控制流支線 / 函式支線 / 記憶體支線（5 條）/ OOP 線（3 條）/ STL 線（2 條）
  - 3 related：recursion↔complexity、references↔pointer-arithmetic、template-meta↔stl-algorithms
  - 寫法：`INSERT ... SELECT FROM (VALUES) JOIN concepts ON tag` 用 tag 對位查 UUID

### 變更
- `web/components/knowledge/knowledge-graph-style.ts`（121→158 行）：
  - 節點 `round-rectangle` → `ellipse`；尺寸 36-60px → 22-38px（18 + difficulty × 4）
  - Label 從節點內 → 節點外下方（`text-valign: bottom` + `text-margin-y: 6`）
  - Label 預設 `text-secondary`，hover 鄰居時提亮為 `text-primary`
  - 邊：bezier 曲線、箭頭縮 0.75x、預設 opacity 0.55、related 邊更細
  - 新增 `.faded` (opacity 0.18) + `.highlighted` (border-emphasis) class
- `web/components/knowledge/knowledge-graph.tsx`（120→131 行）— 加 `mouseover` / `mouseout` 處理：取 `closedNeighborhood()` 加 `.highlighted`，其他元素加 `.faded`；fcose 參數放大（nodeRepulsion 8000→12000、idealEdgeLength 100→130、padding 24→32）以容納外置 label

### 修復
- `backend/models/concept.py` `EdgeType` 加 `values_callable=lambda x: [e.value for e in x]`：與先前 UserRole / MessageRole 同款 bug（第三處）。先前 `concept_edges` 表為空從未讀取，2-2e 種了 23 筆才暴露 → 500 LookupError on enum 讀取

### 視覺成效
- 從「色塊網格」改為「Obsidian 風知識網絡」：圓點 + 細曲線 + 外置標籤 + hover 鄰居高亮
- syntax-basic 自然形成中央放射樞紐；高難度節點（template-meta / undefined-behavior / concurrency）位於圖譜邊緣

### 已知技術債
- 23 條邊內容為 AI 暫定（記於 `tech-debt.md`），實際使用後依教師回饋調整

## [2026-05-04] — Phase 2-2d：Concept Detail Panel（Phase 2-2 完成）

### 新增
- `web/components/knowledge/concept-detail-panel.tsx`（206 行）— 點節點顯示的右側詳情面板：
  - 串 `GET /concepts/{tag}`，loading / error / 內容三態
  - 顯示 `name_zh` + `tag` + category pill badge（同節點配色）+ 5 點難度 + `name_en` + description
  - 先修概念（incoming neighbors）+ 進階概念（outgoing neighbors）兩個 section，每筆 neighbor 含 edge_type 標籤
  - 點鄰居切到該 concept；點 X 關閉

### 變更
- `web/components/knowledge/knowledge-graph-types.ts` — 加 `NeighborRecord` + `ConceptDetailData` type，與後端 `ConceptDetailOut` 對齊
- `web/components/knowledge/knowledge-graph-style.ts` — `CATEGORY_COLOR` / `DEFAULT_CATEGORY_COLOR` 改 export，給 panel 共用
- `web/app/(app)/knowledge/page.tsx` — 在圖譜右側條件渲染 panel（320px），點節點開、X 關，狀態升至 page 層

### 視覺規格遵循（frontend.md）
- Panel 用 `bg-surface-1`、左邊框 `border-default`，避免跟 AppShell 的 chat panel 撞（chat 在更外層）
- Category badge 實色填充（功能性，符合 R8.1）；Difficulty dots 用純黑白灰（符合 R8.4 例外白名單）
- Neighbor 卡片 hover 用 surface 升階 + border-emphasis（不用色背景，符合 R8.5/R6）

### 設計取捨
- 5 個 sub-component（PanelHeader / PanelBody / DifficultyDots / NeighborSection / 主元件）放同檔，緊密耦合無重用，三行重複優於過早抽象
- 點 panel 內鄰居只切 panel 內容，不同步 Cytoscape 內部選取狀態（簡化；後續若要 polish 再加 prop 雙向同步）

### 驗證
- TS clean (`npx tsc --noEmit`) ✓
- 使用者瀏覽器確認：點節點開 panel、切換鄰居、X 關閉皆正常 ✓
- Phase 2-2 知識圖譜（2-2a/b/c/d）全部完成

## [2026-05-04] — Phase 2-2c：Knowledge 頁面 Cytoscape 渲染 + 兩個阻塞 bug 修復

### 新增（前端 2-2c）
- `web/components/knowledge/knowledge-graph.tsx`（120 行）— Cytoscape React 元件，串 `GET /concepts/graph`、fcose 佈局、點擊回呼
- `web/components/knowledge/knowledge-graph-style.ts`（121 行）— Stylesheet + 色票 + `toElements` 轉換
- `web/components/knowledge/knowledge-graph-types.ts`（24 行）— 與後端對齊的 type
- `web/types/cytoscape-fcose.d.ts`（5 行）— `cytoscape-fcose` 套件型別 stub
- npm: `cytoscape ^3.33.3` + `cytoscape-fcose ^2.2.0` + `@types/cytoscape ^3.21.9`

### 變更（前端 2-2c）
- `web/app/(app)/knowledge/page.tsx` — 從 placeholder 換成圖譜 + 選取狀態 header

### 修復（兩個既有 bug，連帶於 2-2c 端到端驗證時暴露）
- **Auth.js v5 HKDF info 對不上 → 401 INVALID_TOKEN**：`backend/core/auth.py` 把 info 從舊版 `"NextAuth.js Generated Encryption Key"` 改為 v5 GA 格式 `"Auth.js Generated Encryption Key (cookie_name)"`，cookie_name 與 salt 從 request 動態傳入，dev/prod 各自衍生 key；`tests/helpers.py` `encrypt_test_token` 加 `cookie_name` 參數對齊；`tests/conftest.py` cache 清空改為 dict
- **Postgres ENUM 接 enum.value 但 SQLAlchemy 預設送 enum.name → 500 InvalidTextRepresentation**：`models/user.py` 與 `models/chat.py` 的 `Enum(...)` 加 `values_callable=lambda x: [e.value for e in x]`；之前因測試走 SQLite（無 ENUM）一直沒抓到

### 視覺規格
- 節點顏色：基礎語法 blue / 記憶體 red / 物件導向 green / STL purple / 演算法 orange / 進階 muted（皆 GitHub Dark token，符合 R8 反 AI 感）
- 節點大小：30 + difficulty × 6 px（36-60 px）
- 邊樣式：實線箭頭 prerequisite / 虛線 contains / 點線箭頭 specialization / 細線 related（目前無 seed 邊資料）
- 選取：邊框由 `border-default` → `border-emphasis` 變粗，不用色背景（符合 R8.5）

### 設計取捨
- 拆檔：`knowledge-graph.tsx` 原 261 行（超 250 停止線）拆為 component / style / types 三檔，最大 121 行
- 範圍守則 #1：2-2c 只做圖譜本身，Detail Panel 留 2-2d；點擊目前僅在 header 顯示選取 tag

### 驗證
- TS clean (`npx tsc --noEmit`) ✓
- 後端 105 測試全綠（含修 enum 後 SQLite 仍相容）✓
- 使用者瀏覽器確認 20 節點正確渲染 ✓

## [2026-05-04] — Phase 2-2b：知識圖譜查詢 service + API

### 新增
- `backend/models/concept.py`（94 行）— `Concept` / `ConceptEdge` / `EdgeType` ORM models（schema 對齊 migration `c3d4e5f6a7b8`）
- `backend/services/graph/queries.py`（89 行）—
  - `get_full_graph(db) -> GraphSnapshot`：全圖一次回傳（concepts + edges）
  - `get_concept_neighborhood(db, tag) -> ConceptNeighborhood | None`：單節點 + depth-1 鄰居（雙向掃描）
- `backend/api/routes/concepts.py`（150 行）— REST 端點：
  - `GET /concepts/graph` → Cytoscape 慣例格式 `{nodes, edges}`（`source`/`target` 而非 `source_id`）
  - `GET /concepts/{tag}` → `{concept, neighbors: [{direction, edge, concept}]}`，不存在 → `404 CONCEPT_NOT_FOUND`
  - 兩端點皆需 `get_current_db_user` 認證
- `backend/tests/test_concept_graph.py`（162 行）— 9 個測試（5 service + 4 API）

### 變更
- `backend/models/__init__.py` — 註冊 Concept / ConceptEdge / EdgeType
- `backend/main.py` — 註冊 `concepts_router`

### 設計重點
- **以 `tag` 為 URL 識別**（非 UUID）— `/concepts/pointer-arithmetic` 比 `/concepts/{uuid}` 穩定、URL 友善
- **方向標記**：API 明確區分 `incoming` vs `outgoing`，給前端 Detail Panel 顯示「先修」vs「進階」
- **service 回傳 ORM**，route 層做 Pydantic serialization — 兩層邊界乾淨

### 驗證
- 105 個測試全綠（96 既有 + 9 新增），zero regression

## [2026-05-04] — Phase 2-2a：知識圖譜 schema + 20 ConceptTag seed

### 新增
- `backend/alembic/versions/c3d4e5f6a7b8_create_concept_tables.py`（170 行，含 seed 資料）：
  - `concepts` 表：id (UUID PK) / tag (unique) / name_zh / name_en / description / difficulty_level (1-5 check) / category / created_at；index(category)
  - `concept_edges` 表：source_id, target_id (CASCADE FK to concepts) / edge_type (4-value PG ENUM `concept_edge_type`：prerequisite/contains/specialization/related) / weight / created_at；unique(source/target/type) + check(無自環)
  - 20 筆 ConceptTag seed（來源：`.claude/rules/edf-pipeline.md`），分 6 個 category

### 設計重點
- **schema 完全對齊 `db-schema.md` Module 5**（concepts + concept_edges + 預留給後續 student_mastery 的 concept_id FK）
- **資料完整性 constraints**：`difficulty_level BETWEEN 1 AND 5`、`source_id <> target_id`（無自環）、`UNIQUE(source/target/edge_type)`（無重複邊）
- **遇到的陷阱**：`sa.Enum` 在 PG 上由 `op.create_table` 自動 `CREATE TYPE`，不可預先 `enum.create()`，否則 `DuplicateObjectError`；已在 migration 註解中記錄

### 已知技術債
- `concepts.category` / `difficulty_level` / `name_zh` 為 AI 暫定值；20 個 `tag` 本身是 authoritative。等 2-2c 圖譜可視化後校準（記於 `docs/tech-debt.md`）

### 驗證
- `alembic current` → `c3d4e5f6a7b8 (head)` ✓
- `SELECT count(*) FROM concepts` = 20，6 個 category 分布合理 ✓
- 使用者已確認 schema + seed（暫定值接受）

## [2026-05-04] — Phase 2-1d：RAG 注入 EDF Feedback（Phase 2-1 完成）

### 新增
- `backend/services/edf/rag_integration.py`（44 行）— EDF ↔ RAG 整合 helper：
  - `build_rag_query(evidence)` — 把 `error_message` + `concept_tags` + `code_analysis` 串成檢索 query
  - `fetch_rag_chunks_safe(evidence)` — 安全包裝 `retrieve_chunks`，吞所有異常回傳 `[]`，**不阻擋教學回應**
- `backend/tests/test_rag_integration.py`（88 行）— 5 個單元測試（query 組裝 / 異常吞食保證）

### 變更
- `backend/services/edf/feedback.py` — `build_system_prompt` 增加 `rag_chunks` 參數；`generate_feedback` 在 `strategy.use_rag=True` 時呼叫 `fetch_rag_chunks_safe`
- `backend/tests/test_feedback.py` — 新增 6 個 RAG 注入測試（含 use_rag 開/關、空 list 不出 RAG block、失敗仍出回覆）

### 設計重點
- **失敗安全**：RAG 失敗（DB / OpenAI / 空索引）→ Feedback 層仍能正常回覆，只是少了教材引用
- **觸發條件**：完全沿用 Decision 層 `strategy.use_rag`（`hint_level >= 2 AND bloom >= ANALYZE`）— Feedback 層不重複判斷
- **prompt 注入位置**：`context_block` 之後加 `rag_block`，附明確指示「請以教材為依據，避免自編未驗證細節」

### 驗證
- 40 個測試全綠（test_evidence + test_decision + test_feedback + test_rag_integration）
- 既有 8 個 feedback 測試零 regression

### 已知技術債（下個 commit 處理）
- `tests/test_feedback.py` 273 行，超過 250 行停止線 — 將拆為 `test_feedback_prompt.py` / `test_feedback_validate.py` / `test_feedback_generate.py`
- `services/edf/feedback.py` 158 行（警告線 +8）— 暫不處理，等之後新增 streaming 等功能時再考慮把 `PREAMBLE/PERSONA` 拆到 `prompts.py`

## [2026-05-04] — Phase 2-1c：RAG 檢索 service

### 新增
- `backend/services/rag/retrieve.py`（55 行）— `retrieve_chunks(query, top_k=5)` async 介面：query → OpenAI embedding → `VectorStoreIndex` 包現有 pgvector 表 → cosine 相似度 top-k
- `backend/services/rag/retrieve.py` 同檔暴露 `RetrievedChunk` Pydantic model（text/score/doc_id/metadata），避免 LlamaIndex 型別擴散到 EDF Feedback 上層
- `backend/scripts/verify_rag_retrieve.py`（39 行）— 端到端檢索驗證腳本（query：「對 nullptr 解引用會發生什麼？」）

### 變更
- `backend/services/rag/pipeline.py` — `_build_vector_store` → `build_vector_store`（改 public，ingest/retrieve 兩端共用同一連線參數來源）
- `backend/services/rag/__init__.py` — 新增匯出：`retrieve_chunks`、`RetrievedChunk`、`build_vector_store`

### 設計取捨（CLAUDE.md「最小可用」）
- 暫不實作 BM25 reranking（roadmap 標註「可選」），等 2-1d 整合 EDF Feedback 後若召回品質不足再補

### 驗證
- 對範例 query 回傳 2 筆 chunks（向量庫目前資料量），cosine score 0.5265 / 0.5207 依序遞減 ✅

## [2026-05-04] — Phase 2-1b：LlamaIndex 索引管線

### 新增
- `backend/services/rag/` 模組（共 122 行，遠低於門檻）：
  - `pipeline.py` — `get_ingestion_pipeline()` 工廠：`SentenceSplitter` (chunk 512/overlap 64) → `OpenAIEmbedding` (text-embedding-3-small, 1536d) → `PGVectorStore` (table `data_codedge_rag`)
  - `ingest.py` — `ingest_document(db, doc_id, text, metadata)` async 介面，餵入 pipeline 並更新 `documents.indexed_at`
  - `__init__.py` — 公開 API re-export
- `backend/scripts/verify_rag_ingest.py` — 端到端驗證腳本（C++ 指標教材範例 → ingest → 檢查向量表 count）

### 變更
- `backend/.venv` 新增依賴：`llama-index 0.14.21`、`llama-index-vector-stores-postgres 0.8.1`、`llama-index-embeddings-openai 0.6.0`、`psycopg2-binary 2.9.12`、`tiktoken 0.12.0`（含相依套件 28 個）
- `backend/pyproject.toml` 暫未列入新依賴（依 tech-debt 規劃，待 Phase 4-1a 容器化前一次重產 `requirements.lock`）

### 驗證
- `data_codedge_rag` 表由 LlamaIndex 自動建立（含 `embedding vector(1536)` + `ref_doc_id` btree index）
- 範例教材 ingest 後 `SELECT count(*) FROM data_codedge_rag` = 1 ✅

### OSS 守則合規（CLAUDE.md #7）
- ✅ Tier 1 LlamaIndex `IngestionPipeline` + `PGVectorStore`（無自寫 chunking/embedding）
- ✅ MIT license（無 AGPL/GPL 風險）

## [2026-04-29] — dev-setup.md §1 補上一鍵啟動指令

### 變更
- `docs/dev-setup.md` §1 重組為三段：🟢 最小啟動（含一鍵 chained 指令 + 逐步版）/ 🟡 完整開發（後端 + 前端）/ 🔴 收工關閉
- 補上 📊 狀態檢查指令區塊（docker ps / colima status / docker info）

## [2026-04-29] — 文檔同步：本機 dev SOP + 下次 session 接續指引

### 新增
- `docs/dev-setup.md` — **本機環境啟動 SOP**（每次 session 必讀）：
  - §1 啟動流程（Colima + docker-compose + alembic 檢查）
  - §2 已安裝工具版本
  - §3 後端 venv 操作（uv pip）
  - §4 服務連線資訊
  - §5 與 Zeabur 部署對照
  - §6 首次安裝完整指令
  - §7 疑難排解（常見錯誤 + 解法）

### 變更
- `CLAUDE.md`「當前狀態」明確標出 **下一任務 2-1b** + 動工前置條件（測試通過 + OPENAI_API_KEY）
- `CLAUDE.md` 文件索引補上 dev-setup.md（標 ★ 必讀）
- `docs/roadmap.md` 2-1b 補上前置條件 / 動作 / 驗證三段提示，避免下次 session 走偏
- `docs/tech-debt.md` 新增 4 項待辦：OPENAI_API_KEY 未填、git config 未設、requirements.lock 過時、pyproject.toml 缺 hatchling packages 設定

## [2026-04-29] — Phase 2-1a 完成：pgvector 啟用 + documents 表 + 本機 dev 環境

### 新增
- `docker-compose.dev.yml`（專案根目錄）— 本機開發環境：
  - Postgres：`pgvector/pgvector:pg16`（與 Phase 4-1b 部署目標 image 對齊）
  - Redis：`redis:7-alpine`
  - 兩服務皆配 healthcheck + 持久化 volume
  - 預設帳密 `postgres/postgres`、DB 名 `programing_education`，與 `backend/.env.example` 對齊
- `backend/alembic/versions/b2c3d4e5f6a7_enable_pgvector_and_create_documents.py`（roadmap 2-1a-i）：
  - `CREATE EXTENSION IF NOT EXISTS vector`（pgvector 0.8.2 由 image 自帶）
  - `documents` 業務表：id / source / title / uri / uploader_id (FK→users) / version / doc_metadata / created_at / indexed_at
  - chunks 與向量資料交給 LlamaIndex `IngestionPipeline` 於 2-1b 自動建表
- `backend/.env`（不進 git）— 從 `.env.example` 複製，指向本機 Docker 服務

### 變更
- `backend/pyproject.toml`（roadmap 2-1a-ii）：
  - 新增 `pgvector>=0.3,<1`（SQLAlchemy `Vector` 型別綁定）
  - 補上漏掉的 `alembic>=1.13,<2`（先前僅在 `requirements.lock`）

### 開發環境基礎建設（首次本機跑通）
- 安裝 Colima 0.10.1（取代 Docker Desktop，避免 brew cask 需要 sudo TTY 的問題）
- 安裝 docker CLI 29.4.1 + docker-compose
- 安裝 uv 0.11.8（繞過 brew Python 3.12 在 macOS Tahoe 上的 expat 動態連結 bug）
- 建立 `backend/.venv`（uv 自帶 portable CPython 3.12.13）
- 安裝後端依賴：fastapi 0.136.1 / sqlalchemy 2.0.49 / alembic 1.18.4 / pgvector / openai 等

### 驗證
- `alembic upgrade head` 全 3 份 migration 成功（users → chat → documents+vector）
- `\dx vector` 顯示 vector 0.8.2 已啟用
- `\dt` 列出 4 張業務表 + alembic_version

### 與 Zeabur 部署相容性
- 本機 docker-compose.dev.yml **不進部署路徑**，Zeabur 走 `zeabur.json`
- Phase 4-1b 部署前需把 `zeabur.json` 的 marketplace `postgresql` 替換為 pgvector spec（已記錄於 roadmap）
- migration 一份共用，部署時 `alembic upgrade head` 同指令

## [2026-04-29] — OSS 重用策略落地 + Roadmap 重排（功能優先、部署延後）

### 新增
- `docs/references.md` §1 **OSS 重用決策矩陣**（4 Tier 分級）：
  - **Tier 1 立即依賴**：pyBKT、LlamaIndex、Cytoscape.js、Vercel AI SDK、prefixspan
  - **Tier 2 Schema 採用**：ProgSnap2 EventType、StudyChat dialogue act
  - **Tier 3 Clone 研讀**：DeepTutor、Mr. Ranedeer、JetBrains Edu Plugin
  - **Tier 4 不採用**：PM4Py（AGPL 風險）、OATutor BKT port、EduAdapt-AI RL、BloomBERT、Socratic-LLM
- `docs/references.md` §2 **授權白名單／黑名單**：嚴禁 AGPL-3.0 / GPL-3.0；MIT / Apache-2.0 / BSD-3 / ISC 直接採用
- `CLAUDE.md` 執行守則 #7 **避免重複造輪子（OSS 優先）**：開發前必查決策矩陣，新增 dependency 必須 PR 列出 license

### 變更
- `docs/roadmap.md` **重排執行順序**：
  - 移除原 Phase 1-7（部署）→ 新增 **Phase 4：部署上線**（4-1 容器化 / 4-2 Zeabur / 4-3 上線驗證）
  - 原 Phase 4 教師端 → **Phase 5**（5-1 ~ 5-5 全數重編）
  - 執行順序：Phase 2 智慧功能 → Phase 3 學習體驗 → Phase 4 部署 → Phase 5 教師端
  - **理由**：API 串接 + Zeabur 反覆卡關，先把學生端做完一次性處理部署
- `docs/roadmap.md` 各 Phase 任務加註 **OSS 標記**：
  - 2-1 RAG → LlamaIndex `PGVectorStore`
  - 2-2 知識圖譜 → Cytoscape.js + fcose
  - 2-3 精熟度 → **pyBKT，禁止 port OATutor**
  - 3-1 學習路徑 → 拓撲排序，**不採用 EduAdapt-AI RL**
  - 5-2 行為事件 → ProgSnap2 + StudyChat schema
  - 5-3 行為分析 → pyBKT + prefixspan，**禁止用 PM4Py**
- `CLAUDE.md` 當前狀態區塊壓縮為摘要（Phase 1 全完成 + 下一步 Phase 2 任務清單）

### 已確認決策（roadmap.md）
- 新增「OSS 重用」與「執行順序」兩條長期決策

## [2026-04-29] — Login hero 移除主標 `Code with Edge`，避免與 h1 `Codedge` 重複

### Changed
- `web/app/login/page.tsx` — 移除中間的「Code with Edge」副 slogan 行：h1 `Codedge` 已等同於拆解後的字面，再放等於重複。保留唯一副標「會思考的學習，從會提問的 AI 開始」（mt-2 text-sm secondary）

### Kept
- `web/app/layout.tsx` `<title>` 仍保留「Codedge — Code with Edge」：browser tab / SEO 場景單獨出現，「Code with Edge」首次接觸者揭示品牌雙關，無視覺重複

## [2026-04-29] — Slogan 改版：雙標題式 hero（Code with Edge）

### 命名邏輯
- **主標 `Code with Edge`** — 直接拆解 `Codedge` 字母，三層意義同步：cutting-edge / edge case / have the edge
- **副標「會思考的學習，從會提問的 AI 開始」** — 點出 EDF Pipeline 蘇格拉底式提問教學差異化（vs ChatGPT 直接給答案）
- 取代原 slogan「Coddy 陪你寫 C++，磨穿每個 edge case」（受苦感、未體現品牌雙關）

### Changed
- `web/app/login/page.tsx` — login hero 由單行改為雙標題：`Code with Edge`（text-base font-medium）+「會思考的學習，從會提問的 AI 開始」（text-sm secondary）
- `web/app/layout.tsx` — `<title>` "Codedge" → "Codedge — Code with Edge"；description 更新為中文價值主張，強調蘇格拉底式提問與不直接給答案

## [2026-04-29] — 品牌命名：**Codedge** 平台 + **Coddy** AI 助教

### 命名邏輯
- **Codedge** = `Code` + `Edge` 字母融合（共享 `e`）。三層意義：(1) Cutting-edge 程式前沿、(2) Edge case 邊界案例（CS 核心術語）、(3) "have the edge" 取得競爭優勢
- **Coddy** = AI 助教名，承襲 `Cod-` 字頭與品牌 `Codedge` 兄妹呼應

### Changed — 全站 rename
- `web/components/layout/global-nav.tsx` — Logo "C++ Tutor" → **Codedge**；chat toggle title/aria "AI 導師" → "Coddy"
- `web/components/layout/chat-panel.tsx` — header "AI 導師" → "Coddy"
- `web/components/layout/tablet-header.tsx` — "C++ Tutor" → "Codedge"
- `web/components/chat/message-list.tsx` — "AI 導師隨時為你解答" → "Coddy 隨時為你解答"；"AI 導師思考中…" → "Coddy 思考中…"
- `web/components/chat/run-result-card.tsx` — "AI 導師已取得..." → "Coddy 已取得..."（含註解）
- `web/components/workspace/run-block.tsx` — 「💬 詢問 AI 導師」按鈕 title/aria → "詢問 Coddy"
- `web/app/login/page.tsx` — `<h1>` "C++ Tutor" → "Codedge"；副標 "AI 驅動的 C++ 程式教學平台" → "Coddy 陪你寫 C++，磨穿每個 edge case"
- `web/app/layout.tsx` — `<title>` "ProgramingEducation" → "Codedge"；description 更新為「Codedge — AI-powered C++ programming education with Coddy」
- `backend/core/config.py` — `APP_NAME` "ProgramingEducation API" → "Codedge API"
- `docs/ui-ux-spec.md` + `docs/ui-wireframes.md` — wireframe ASCII / 文案同步更新

### Verified
- `grep` 全 `web/` `backend/` 殘留 "C++ Tutor" 0 處、"AI 導師" 0 處（生產代碼）
- TypeScript `tsc --noEmit` exit 0
- changelog 歷史紀錄保留「C++ Tutor」原貌不修改

## [2026-04-29] — Chat toggle 改為「僅收合時顯示」

### Changed
- `web/components/layout/global-nav.tsx` — chat toggle 按鈕從「總是顯示」改為「`!chatOpen` 時才渲染」：chat 開啟時隱藏（避免與 ChatPanel 內收合按鈕重複），chat 收合時顯示 `MessageSquare` icon 提供視覺 affordance 重新開啟
- `web/components/layout/app-shell.tsx` — 恢復傳遞 `chatOpen` / `toggleChat` props 至 `<GlobalNav />`

### UX
- Chat 開啟：右上只見 Avatar 下拉（極簡）
- Chat 收合：右上出現訊息 icon（一鍵展開）+ Avatar 下拉
- Ctrl+B 仍可全狀態切換

## [2026-04-29] — 移除 GlobalNav chat toggle 與 ChatPanel header 訊息 icon

### Removed
- `web/components/layout/global-nav.tsx` — 移除右上角 chat toggle 按鈕（`MessageSquare` / `PanelRightOpen` icon）；連帶移除已 orphan 的 `chatOpen` / `onToggleChat` props
- `web/components/layout/chat-panel.tsx` — 移除 ChatPanel header「AI 導師」文字左側的 `MessageSquare` icon，header 僅保留純文字 + 右側 SessionList + 收合按鈕

### Changed
- `web/components/layout/app-shell.tsx` — `<GlobalNav />` 不再傳 props（簽名簡化）

### Notes
- Chat 開關現只能透過 **Ctrl+B 全域快捷鍵** 或 **ChatPanel 內收合按鈕** 觸發
- Chat 關閉時無視覺按鈕重新開啟（依使用者要求保持極簡）；若日後需要視覺後備可加回浮動按鈕
- TypeScript `tsc --noEmit` exit 0；其他用到 `MessageSquare` 的場景保留（session-list / message-list 空狀態 / run-block 詢問 AI 按鈕）

## [2026-04-29] — R8 反 AI 感視覺修正（Phase 1-6 follow-up）

> 觸發：使用者指出截圖中右上 chat icon 半透明 halo + 紫色圓 bot 頭像 + `⚠` emoji = 廉價 AI 感。專業工具（Linear/Stripe/Vercel）皆無此風格。

### Added — R8 規則
- `.claude/rules/frontend.md` — 新增 R8 反 AI 感規則（5 條）：禁半透明色背景 / 禁 emoji 符號字 / 禁圓形彩色 halo 頭像 / 禁裝飾性彩色 / active 狀態用 border 不用色背景
- `docs/design-plan.md` §0.3 違和感檢核表新增 R8.1-R8.5
- 例外白名單：`text-text-muted/N` 灰階淡化、`shadcn/ui` 基礎元件、`lucide-react` 線條 icon、實線 border-accent-X

### Changed — 9 處違規修正
- `web/components/chat/message-bubble.tsx` — Avatar 從圓形彩色 halo（`rounded-full + bg-accent-X/20`）改為圓角方型 + border（`rounded-md + bg-surface-1 + border-border-default`），icon 顏色改為 `text-text-secondary` 去除彩色填充
- `web/components/layout/global-nav.tsx` — Logo 從 `◇ C++ Tutor`（Unicode 幾何字 + 藍色 hover）改為純文字「C++ Tutor」；chat toggle active 從 `bg-accent-blue/15 text-accent-blue` 改為 `bg-surface-2 text-text-primary`
- `web/components/workspace/run-block.tsx` — `STATUS_META` 重構：加入 `Icon: LucideIcon` 欄位（Check/AlertOctagon/X/Clock/Minus）；移除標籤中的 `✓`；badge 從半透明色填充（`bg-accent-X/10`）改為實線 border + 純文字色（`border-accent-X text-accent-X`）；export STATUS_META 供 output-panel 復用
- `web/components/workspace/output-panel.tsx` — 將 `collapsedStatusText()` 字串函式改為 `<CollapsedStatusContent />` React 元件，用 lucide icon 取代 `✓` `✗` 符號字
- `web/hooks/use-chat.ts` — 錯誤訊息 `⚠ 無法取得 AI 回應` → `無法取得 AI 回應`
- `web/components/layout/tablet-header.tsx` — hamburger `☰` 字符 → lucide `<Menu />` icon；avatar 占位由 `rounded-full` 改 `rounded-md`
- `web/app/login/page.tsx` — Logo 容器 `bg-accent-blue/10 text-accent-blue` → `bg-bg-canvas border-border-default text-text-secondary`

### Verified
- `grep -rE 'bg-(accent|btn|primary|destructive)[a-z-]*/[0-9]+'` 全程式碼 0 命中（排除 shadcn ui/button.tsx 白名單）
- `grep -rE '✓|✗|⚠|◇|☰|✕'` 全程式碼 0 命中
- TypeScript `tsc --noEmit` exit 0

## [2026-04-29] — Phase 1-6f EDF Pipeline mini timeline + Phase 1-6 全部完成 ✅

### Added
- `web/components/chat/edf-timeline.tsx` — 新建 EDF Pipeline mini timeline：4 步（Evidence orange / Decision purple / Feedback green / RAG blue）8px 圓點 + 連接線；每步附 hint tooltip 解說；前 3 步永遠 active（Phase 1 必經）；RAG 在 Phase 2-1 啟用後才會 active

### Changed
- `web/components/chat/message-bubble.tsx` — AI 訊息有 `evidence` 時，於氣泡上方渲染 `<EdfTimeline />`；max-w-[80%] 容器內排列：timeline + bubble（Bloom badge 仍在 bubble 底部）

### 🎉 Phase 1-6「介面精修」全部完成
- 1-6a Surface / Shadow / Border / Radius token ✅
- 1-6b Inter OpenType + 三權重檢核 ✅
- 1-6c Output Panel Run Block 化 ✅
- 1-6d Chat 訊息氣泡 ring + Bloom badge ✅
- 1-6e GlobalNav 取代 ActivityBar ✅
- 1-6f EDF Pipeline mini timeline ✅

### Verified
- TypeScript `tsc --noEmit` exit 0
- design-plan §0.3 七條視覺統一規則皆遵守（R1 顏色 / R2 字體 / R3 邊框 / R4 陰影 / R5 Radius / R6 Hover / R7 字距）
- 兩處唯一視覺例外：AI 訊息氣泡 ring（border-ai purple alpha）、`.kbd` 鍵帽（待 Phase 2-5 Cmd+K 實作時建立）

## [2026-04-29] — Phase 1-6e GlobalNav 取代 ActivityBar（VSCode sidebar → GitHub top nav）

### Added
- `web/components/layout/global-nav.tsx` — 新建頂部全域導覽（48px 高 / `bg-canvas` / `border-muted` 底）：Logo + 5 頁籤（Workspace / Learn / Quiz / Knowledge / Dashboard）+ Chat Toggle + Avatar 下拉選單（學習總覽 / 通知 / 設定 / 登出）；Tab active 採 `border-bottom: 2px solid #F78166`；click-outside + Escape 關閉下拉

### Changed
- `web/components/layout/app-shell.tsx` — laptop / desktop 將 `ActivityBar` 換為 `GlobalNav` 置於頂部；移除 floating `ChatToggle`（GlobalNav 已含 toggle，避免重複）；laptop chat overlay shadow 改用 `shadow-modal` token
- `web/components/workspace/toolbar.tsx` — 移除 AI 切換按鈕（已上移至 GlobalNav）；新增「未執行版本」橘色 dot（`isDirty` prop）；改用 `border-muted` 底線、`body-ui` 行高、`rounded-pill` 語言 badge
- `web/app/(app)/workspace/page.tsx` — 新增 `isDirty` state：editor 變更時 true、Run 成功後 false；傳給 Toolbar

### Removed
- `web/components/layout/activity-bar.tsx` — 完全刪除（GlobalNav 取代所有功能）

### Layout 哲學變更
- 從 VSCode 風 left sidebar（180px）改為 GitHub 風 top horizontal nav（48px）
- 釋出更多水平空間給 Editor + Chat
- Tablet/Mobile 維持原本 TabletHeader / MobileNav，未來再統一

### Notes
- `global-nav.tsx` 203 行（介於 150 警告與 250 停止之間，可選擇性拆出 AvatarMenu 至獨立檔）
- TypeScript `tsc --noEmit` exit 0

## [2026-04-29] — Phase 1-6d Chat 訊息氣泡 ring + Bloom badge

### Added
- `web/components/chat/bloom-badge.tsx` — 新建 Bloom 6 級 pill badge：6 色取自 GitHub Dark accent token（L1 muted / L2 blue / L3 green / L4 orange / L5 purple / L6 red）+ `extractBloomLevel(evidence)` 防禦性 parse helper

### Changed
- `web/components/chat/message-bubble.tsx` — User / AI 訊息同 `bg-surface-1` 背景；以 border 顏色區分角色（User: `border-default`、AI: `border-ai` GitHub Dark purple 25% alpha ring，符合 R3 邊框唯一例外）；radius 12px (`rounded-xl`)；line-height 1.6 (`body-reading`)；AI 訊息底部顯示 BloomBadge（讀 `evidence.bloom_level`）；Avatar 從 green 改為 purple（與 ring 色呼應）
- `web/lib/chat-types.ts` — `MessageItem` 新增 `evidence?: Record<string, unknown>` 選用欄位
- `web/hooks/use-chat.ts` — `toMessageItem` 將 `msg.evidence` 透傳至 MessageItem，使 BloomBadge 可讀取
- `web/components/chat/message-list.tsx` — 訊息間距從 `space-y-4` (16px) 改為 `space-y-3` (12px) 符合 design-plan §2.4

### Verified
- TypeScript `tsc --noEmit` exit 0
- 5 個檔案皆 ≤ 150 行（bloom-badge 48 / message-bubble 59 / message-list 66 / chat-types 46 / use-chat 122）

## [2026-04-29] — Phase 1-6c Output Panel Run Block 化

### Added
- `web/components/workspace/run-block.tsx` — 新建單一 Run Block 元件：32px header（折疊 chevron / Run #N / 時間 / status badge / runtime / 記憶體 / 📋 複製 / 💬 詢問 AI）+ 可折疊 body（compile / stdout / stderr 分區）+ 5 種狀態分類（accepted / compile-error / runtime-error / limit-exceeded / unknown）

### Changed
- `web/components/workspace/output-panel.tsx` 重寫 — 從單次輸出 tab UI 改為 block list：訂閱 `onExecutionComplete`、新 block 置頂自動收合舊 block（仿 Warp）、panel header 含「清空」按鈕與 block 計數、保留收合單行 status bar 顯示最新 block 摘要
- `web/components/workspace/workspace-context.tsx` — `ExecutionResult` 新增 `time / memory` 選用欄位；新增 `requestChatInjection` + `onChatInjectionRequest` queued listener pattern（chat 收合時點擊 block 「💬」會 queue，等 chat 掛載時 drain）
- `web/components/layout/chat-panel.tsx` — 新增訂閱 `onChatInjectionRequest`，與 auto-inject 共用 `injectExecutionResult`
- `web/app/(app)/workspace/page.tsx` — 移除本地 `output` state（OutputPanel 自管理）、`setExecutionResult` 補傳 `time / memory`、移除 `statusText` 由 OutputPanel 內部生成

### Verified
- TypeScript `tsc --noEmit` exit 0，無錯誤
- `RunResultCard`（chat 內既有執行結果卡片）保持不變，與 RunBlock 各司其職

## [2026-04-29] — Phase 1-6b Inter OpenType + 三權重檢核

### Added
- `web/app/globals.css` — `body` 套用 `font-feature-settings: "cv01", "ss03"`（Inter 單層 'a' + 幾何字形，全站生效）
- `web/app/globals.css` — Typography helper classes：`.display`（≥40px 字級用，-0.02em 字距 + 1.1 行高）、`.body-reading`（chat/段落用，1.6 行高）、`.body-ui`（按鈕/nav 用，1.4 行高）

### Changed
- `web/components/layout/activity-bar.tsx` — Logo `◇` 從 `font-bold` (700) 改為 `font-semibold` (600)，遵守 R7 三權重系統

### Verified
- `grep` 全 `web/` 確認無剩餘 `font-bold` / `font-extrabold` / `font-black` / `font-weight: 700+`
- 既有元件已使用 `font-medium` (500) / `font-semibold` (600) / 預設 (400)，全數符合 R7

## [2026-04-29] — Phase 1-6a Surface/Shadow/Border/Radius token 增補

### Added
- `web/app/globals.css` — `:root` 新增 8 個 token：
  - Surface 語義別名 4 個（`--surface-0/1/2/inset`）疊加既有 `--bg-*`，不破壞 backward compatibility
  - Shadow stack 2 個（`--shadow-card`、`--shadow-modal`）
  - Border AI ring 例外 1 個（`--border-ai`）
  - Pill radius 1 個（`--radius-pill: 9999px`）
- `web/app/globals.css` — `@theme inline` 對應新增 9 條 Tailwind utility 映射，解鎖 `bg-surface-1` / `shadow-card` / `shadow-modal` / `border-ai` / `rounded-pill`
- `.claude/rules/frontend.md` — Design Tokens 區塊新增「Phase 1-6 統一協議 token」說明列；移除底部 placeholder 註記

### Notes
- 純 additive 變更，所有既有元件與 `--bg-*` 引用 0 影響
- 為 1-6c (Output Run Block) / 1-6d (Chat ring + Bloom badge) / 1-6e (Toolbar + .kbd) 鋪設 token 基礎

## [2026-04-29] — Phase 1-2 Google OAuth 本機端到端驗證通過

### Verified
- `web/.env.local` 建立完成（`AUTH_SECRET` 由 `openssl rand -base64 33` 產生；`AUTH_GOOGLE_ID` / `AUTH_GOOGLE_SECRET` 已填入 Google Cloud Console 取得的憑證）
- Google OAuth 登入流程實測通過：`/login` → Google 同意畫面 → 重導 `/workspace`
- NextAuth v5 `MissingSecret` 錯誤已排除，`/api/auth/session` 不再回 500

### Notes
- Google Cloud Console OAuth 用戶端設定：Authorized redirect URI = `http://localhost:3000/api/auth/callback/google`；測試使用者已加入 `abbyabby41@gmail.com`
- `.env.local` 受 `web/.gitignore` 保護（`.env*` 規則），不會被 commit
- Phase 1-2 Auth 模組 4 子任務（1-2a~d）roadmap 早已勾選，本次為首次完整本機 dev 環境驗證

## [2026-04-29] — Phase 1-6 介面精修計畫產出 + Roadmap 重排

### Added
- `docs/design-plan.md` — 統一視覺協議與 6 份借鑑來源映射計畫；§0.3 七條違和感檢核硬規則；§2 各區塊借鑑細節（含 EDF Pipeline timeline、Output Run Block、Chat ring、Bloom badge）；§3 Token 增補規格
- `docs/design-references/` — 6 份原版 DESIGN.md 收錄（cursor / warp / linear.app / claude / vercel / raycast，共 1819 行原文，自 voltagent/awesome-design-md repo 首次 commit 提取）
- `.claude/rules/frontend.md` — 新增「統一視覺協議」章節，含 R1-R7 違和感檢核 7 條 + 兩處唯一視覺例外

### Changed
- `docs/roadmap.md` — **新增 Phase 1-6「介面精修」**（6 子任務 a-f），對應 design-plan §2-3；**原 Phase 1-6 部署改為 Phase 1-7**，3 子任務全部回退為未完成（上次卡關於 API 串接，1-7c golden path 未通過）
- `CLAUDE.md` — 當前狀態同步：Phase 1-6 改為「介面精修 🔧」、Phase 1-7「部署 ⏸」；新增「介面借鑑：6 份來源僅貢獻結構模式」於已確認決策

### Decision
- **唯一視覺基本元素**：GitHub Dark token，外部 6 份來源不貢獻 color/font/shadow/border/radius/spacing
- **兩處唯一視覺例外**：AI 訊息氣泡 ring（GitHub Dark purple alpha）、`.kbd` 鍵帽多層 inset 陰影
- **執行順序變更**：UI 統一精修先於部署，避免上線後再大幅改 UI

## [2026-04-13] — Phase 1-6a/b 部署配置（Dockerfile + Zeabur）
### Added
- `zeabur.json` — Zeabur Template 定義（web + backend + PostgreSQL + Redis 四服務）
- `backend/start.sh` — 容器啟動腳本：先跑 Alembic migration 再啟動 uvicorn
- `docs/deployment.md` — Zeabur 部署指南（環境變數、service 串接、驗證步驟）

### Changed
- `backend/Dockerfile` — CMD 改為 `start.sh`，啟動時自動執行 DB migration

## [2026-04-13] — Phase 1-5d Chat Panel 收合/展開 toggle
### Added
- `web/components/workspace/toolbar.tsx` — Toolbar 新增 [AI] 按鈕，顯示 Chat Panel 展開/收合狀態（藍色 active / 灰色 inactive）

### Changed
- `web/components/workspace/workspace-context.tsx` — 新增 `chatOpen` / `toggleChat` props，從 AppShell 傳入
- `web/components/layout/app-shell.tsx` — 將 chatOpen/toggleChat 傳入 WorkspaceProvider

### 4 種 toggle 方式
| 方式 | 位置 |
|------|------|
| Toolbar [AI] 按鈕 | Workspace 頂部工具列 |
| ChatPanel 收合按鈕 | Chat 面板 header |
| Ctrl+B 快捷鍵 | 全域 |
| 浮動 ChatToggle | Chat 收合時右上角 |

## [2026-04-13] — Phase 1-5c Run 結果自動注入 Chat context
### Added
- `web/components/chat/run-result-card.tsx` — 執行結果摘要卡片：通過/編譯失敗/執行錯誤狀態 badge + stdout/stderr 預覽
- `web/lib/chat-types.ts` — Chat 型別定義：`MessageItem | ExecutionItem` union type

### Changed
- `web/components/workspace/workspace-context.tsx` — 新增 `onExecutionComplete` 事件訂閱機制（subscribe/notify pattern）
- `web/hooks/use-chat.ts` — 新增 `injectExecutionResult()` 注入執行結果卡片至訊息列表
- `web/components/layout/chat-panel.tsx` — 訂閱執行事件，Run 完成後自動在 Chat 中顯示結果卡片
- `web/components/chat/message-list.tsx` — 支援 `ChatItem` union type 渲染（message / execution）

## [2026-04-13] — Phase 1-5b 對話歷史持久化（session 管理 + 歷史載入）
### Added
- `web/hooks/use-sessions.ts` — session 列表管理 hook：串接 GET/DELETE /chat/sessions API，自動載入歷史 session
- `web/components/chat/session-list.tsx` — session 歷史下拉選單：新對話、切換 session、刪除 session

### Changed
- `web/hooks/use-chat.ts` — 新增 `loadSession(id)` 載入既有對話、`startNewSession()` 開始新對話、`onSessionCreated` 回呼
- `web/components/layout/chat-panel.tsx` — 整合 useSessions + SessionList，header 加入對話歷史按鈕

## [2026-04-13] — Phase 1-5a Chat Panel 元件（訊息氣泡 + 輸入框 + Context 共享）
### Added
- `web/hooks/use-chat.ts` — 聊天狀態管理 hook：訊息列表、session 追蹤、發送訊息（串接 `/chat/interact` REST API）
- `web/components/chat/message-bubble.tsx` — 訊息氣泡元件：user 靠右藍底、assistant 靠左灰底，含頭像
- `web/components/chat/message-list.tsx` — 可捲動訊息列表：自動捲到底部、空狀態提示、loading 動畫
- `web/components/chat/chat-input.tsx` — 聊天輸入框：textarea + Enter 發送、Shift+Enter 換行
- `web/components/workspace/workspace-context.tsx` — WorkspaceContext：用 ref 共享編輯器程式碼與執行結果，不觸發額外 re-render

### Changed
- `web/components/layout/chat-panel.tsx` — 從 placeholder 重構為功能完整的 Chat Panel，整合 MessageList + ChatInput + useChat
- `web/components/layout/app-shell.tsx` — 包裹 WorkspaceProvider、提取 ShellLayout 子元件
- `web/app/(app)/workspace/page.tsx` — 同步程式碼變更與執行結果至 WorkspaceContext

## [2026-04-13] — Phase 1-4e 安全防護：輸入三層防護 + 輸出驗證
### Added
- `backend/services/security/sanitizer.py` — 輸入安全防護 service：
  - Regex 層：12 個 prompt injection 偵測模式（中英文，含角色覆寫、資訊洩漏、直接要求答案）
  - XML 標籤隔離：`<student_input>` / `<student_code>` 包裝使用者輸入
  - `sanitize_input()` — 偵測到 injection 時拋出 422
- `backend/tests/test_sanitizer.py` — 18 個安全防護測試

### Changed
- `backend/services/chat.py` — interact 前先 `sanitize_input()` 過濾使用者提問
- `backend/services/edf/evidence.py` — user prompt 用 `<student_code>` XML 標籤包裝程式碼
- `backend/services/edf/feedback.py` — user message 用 `<student_input>` XML 標籤包裝

### 三層防護完整對照
| 層 | 位置 | 功能 |
|---|---|---|
| 1. Regex | sanitizer.py | 偵測已知 prompt injection 模式 |
| 2. XML 隔離 | evidence.py + feedback.py | 防止 LLM 混淆使用者輸入與系統指令 |
| 3. System Preamble | feedback.py PREAMBLE | 5 條不可覆寫規則 |
| 輸出驗證 | feedback.py validate_output() | 阻擋 >8 行無 TODO 的完整程式碼 |

## [2026-04-13] — Phase 1-4d Chat API 端點
### Added
- `backend/models/chat.py` — ChatSession + ChatMessage SQLAlchemy models（JSON 欄位存 execution_result/evidence）
- `backend/alembic/versions/a1b2c3d4e5f6_create_chat_tables.py` — migration：chat_sessions + chat_messages 表
- `backend/services/chat.py` — Chat service（interact 串接 EDF 三層管線、session CRUD、對話歷史管理）
- `backend/api/routes/chat.py` — 4 個 API 端點：POST /chat/interact、GET /chat/sessions、GET /chat/sessions/{sid}、DELETE /chat/sessions/{sid}
- `backend/tests/test_chat.py` — 4 個 Chat service 測試（建立 session、復用 session、列表、刪除）

### Changed
- `backend/models/__init__.py` — 匯入 ChatSession、ChatMessage
- `backend/main.py` — 註冊 chat router
- `backend/tests/conftest.py` — pytest_configure 改為 drop+create 確保 schema 最新

## [2026-04-13] — Phase 1-4c Feedback 層 prompt 組裝 + 輸出驗證
### Added
- `backend/services/edf/feedback.py` — Feedback 層 service：
  - 分層 prompt 組裝（preamble 5 條不可違反規則 → persona → strategy 指令 → evidence context）
  - LLM 呼叫（GPT-4o, temperature=0.7），支援對話歷史（最近 10 輪）
  - 輸出驗證：不允許程式碼時移除 code block、允許時超過 8 行且無 TODO/FIXME 自動截斷
- `backend/tests/test_feedback.py` — 11 個 Feedback 層測試（prompt 組裝 3 個、輸出驗證 5 個、LLM 呼叫 3 個）

## [2026-04-13] — Phase 1-4b Decision 層策略矩陣
### Added
- `backend/services/edf/decision.py` — Decision 層：6×6 Bloom × Hint Ladder 策略矩陣（36 格教學指令），RAG 觸發條件（hint≥2 且 bloom≥ANALYZE），回傳 TeachingStrategy（instruction + allow_code_snippet + use_rag）
- `backend/tests/test_decision.py` — 10 個 Decision 層測試（低/高 Bloom×Hint 組合、RAG 觸發/不觸發、邊界值 clamp、36 格完整性驗證）

## [2026-04-13] — Phase 1-4a Evidence 層 LLM 結構化分析
### Added
- `backend/services/edf/models.py` — EDF 共用模型（BloomLevel 6 級 enum、ErrorType 6 類 enum、20 個 ConceptTag 常數、EvidenceResult schema）
- `backend/services/edf/evidence.py` — Evidence 層 service：呼叫 OpenAI GPT-4o（JSON mode），分析學生程式碼回傳錯誤分類、ConceptTag、Bloom 認知等級
- `backend/tests/test_evidence.py` — 8 個 Evidence 層測試（prompt 組裝、model 解析、LLM 成功/失敗/JSON 異常）
- `backend/pyproject.toml` — 新增 openai、httpx 依賴

## [2026-04-13] — Phase 1-3f resize handle UX 改善
### Changed
- `web/app/(app)/workspace/page.tsx` — 垂直 resize handle 從 1px 改為 4px hit area + 1px 視覺線條（before pseudo-element）
- `web/components/layout/app-shell.tsx` — 水平 resize handle 同樣改善，更容易拖曳

## [2026-04-13] — 移除 stdin 前端 UI
### Removed
- `web/components/workspace/stdin-panel.tsx` — Phase 1 不需要前端 stdin 面板，後端 API 仍保留 stdin 參數供未來 test case 機制使用

### Changed
- `web/components/workspace/toolbar.tsx` — 移除 stdin 按鈕及相關 props
- `web/app/(app)/workspace/page.tsx` — 移除 stdin state 和 StdinPanel 引用

## [2026-04-13] — Phase 1-3d 前端 Run 按鈕串接 + Output Panel
### Changed
- `web/app/(app)/workspace/page.tsx` — 串接 Run 按鈕：點擊呼叫 `POST /api/code/execute`，管理 isRunning/output state，自動展開 Output Panel，顯示執行狀態（Running → Passed/Error）
- `web/components/editor/code-editor.tsx` — mount 時通知父層初始程式碼內容，確保 Run 可取得程式碼

## [2026-04-13] — Phase 1-3c Judge0 API client
### Added
- `backend/services/judge0.py` — Judge0 async client（submit + polling），支援 RapidAPI 和自架模式，base64 編碼，逾時/限流/不可用錯誤處理
- `backend/api/routes/code.py` — `POST /code/execute` 端點（需登入），接收 code/language_id/stdin，回傳 stdout/stderr/compile_output
- `backend/tests/test_judge0.py` — 7 個 Judge0 service 測試（b64 解碼、submit+poll 成功、編譯錯誤、429 限流、503 不可用）

### Changed
- `backend/main.py` — 註冊 code router

## [2026-04-13] — Phase 1-3b Workspace 頁面基礎佈局
### Added
- `web/components/workspace/toolbar.tsx` — Toolbar 元件（檔名顯示、C++ 語言標籤、stdin 按鈕、▶ Run 按鈕）
- `web/components/workspace/output-panel.tsx` — Output Panel 元件（stdout/stderr/compile tabs、stderr 紅點指示、可收合為單行 status bar）

### Changed
- `web/app/(app)/workspace/page.tsx` — 重構為三區佈局：Toolbar (40px) + Editor (70%) + Output Panel (30%)，使用 react-resizable-panels 垂直拖曳調整

## [2026-04-13] — Phase 1-3a CodeMirror 6 整合
### Added
- `web/components/editor/code-editor.tsx` — CodeMirror 6 編輯器元件（C++ 語法高亮、One Dark 主題、行號、括號配對、fold gutter、歷史紀錄）
- CodeMirror 6 相關套件：codemirror、@codemirror/lang-cpp、@codemirror/theme-one-dark、@codemirror/state、@codemirror/view

### Changed
- `web/app/(app)/workspace/page.tsx` — 替換 placeholder 為 CodeEditor 元件，佔滿可用空間

## [2026-04-13] — Phase 1-2e Role-based 權限 middleware
### Added
- `backend/api/deps.py` — `require_roles(*roles)` 依賴工廠，檢查使用者角色，不符合回傳 403 FORBIDDEN
- `backend/tests/test_roles.py` — 5 個 role-based 權限測試（student 可/不可存取、teacher 升級、admin 全通、多角色允許）
- `backend/tests/helpers.py` — 共用測試工具（DB engine、session factory、token 加密），修復 conftest 雙重載入問題
- `backend/tests/conftest.py` — 重構為純 fixtures（DB 初始化/清理、client、secret 設定）

### Changed
- 測試基礎設施全面重構：pytest-asyncio 升級至 1.3，SQLite file-based DB 取代 in-memory（解決事件迴圈綁定），27 個測試全數通過

## [2026-04-13] — Phase 1-2d 前端登入/登出頁面 + 未登入重導
### Added
- 確認先前實作的登入頁面、登出按鈕、middleware 重導功能完整可用，正式標記 1-2d 完成

## [2026-04-13] — Phase 1-2c 使用者首次登入自動建立 DB 記錄
### Added
- `backend/services/user.py` — `get_or_create_user()` 依 google_id 查找/建立使用者，每次登入更新 name、avatar、last_login_at
- `backend/tests/test_user_service.py` — 5 個使用者 service 測試（首次建立、重複登入、profile 更新、fallback google_id）

### Changed
- `backend/api/deps.py` — 新增 `get_current_db_user` 依賴注入（token 解析 + DB upsert）
- `backend/api/routes/auth.py` — `/auth/me` 改用 `get_current_db_user`，回傳完整 DB 使用者資訊（含 UUID、role）
- `backend/tests/test_auth.py` — 整合測試改用 SQLite in-memory 覆蓋 DB 依賴，新增重複呼叫測試

## [2026-04-13] — Phase 1-2b 後端 JWT 驗證 middleware
### Added
- `backend/core/auth.py` — NextAuth v5 JWE token 解密（HKDF-SHA256 金鑰衍生 + authlib 解密 + `TokenPayload` model）
- `backend/api/routes/auth.py` — `GET /auth/me` 端點，回傳當前登入使用者資訊
- `backend/tests/test_auth.py` — 6 個 auth 測試（金鑰衍生、token 解碼、401 保護、/auth/me 整合測試）
- `backend/Dockerfile` + `web/Dockerfile` — 前後端 Docker 建構設定
- `backend/tests/test_cors.py` / `test_errors.py` / `test_models.py` — 補齊先前功能的 unit tests

### Changed
- `backend/api/deps.py` — 匯出 `get_current_user` + `TokenPayload` 供路由依賴注入
- `backend/main.py` — 註冊 auth router
- `backend/pyproject.toml` — 新增 `authlib`、`cryptography`、`PyJWT` 依賴

## [2026-04-13] — Phase 1-2a 前端 Auth 完善
### Added
- `web/app/login/page.tsx` — Google OAuth 登入頁面
- `web/middleware.ts` — NextAuth v5 middleware，未登入重導至 /login
- `web/app/(app)/` — 路由群組，所有需認證頁面移入此群組

### Changed
- `web/auth.ts` — 新增 `authorized` callback 控制存取 + `jwt`/`session` callbacks 傳遞 Google profile
- `web/app/layout.tsx` — 移除 `(app)` 群組外的 SessionProvider（改由群組內 layout 處理）

## [2026-04-13] — Phase 1-2a NextAuth.js Google OAuth 設定
### Added
- `web/auth.ts` — NextAuth v5 核心設定（Google OAuth provider + JWT/session callbacks）
- `web/app/api/auth/[...nextauth]/route.ts` — Auth API route handler（`/api/auth/*`）
- `web/components/providers/session-provider.tsx` — Client-side SessionProvider wrapper
- `web/.env.example` — 前端環境變數範本（AUTH_SECRET、AUTH_GOOGLE_ID、AUTH_GOOGLE_SECRET）

### Changed
- `web/app/layout.tsx` — 加入 SessionProvider 包裹全域
- `web/.gitignore` — 排除 `.env.example` 使其可被追蹤

## [2026-04-13] — Phase 1-1f Health check + 前端連線狀態顯示
### Added
- `hooks/use-health-check.ts` — 定期 poll `/api/health`（30 秒），回傳 DB/Redis 連線狀態
- StatusBar 即時顯示：連線成功綠點 `Connected` / 斷線紅點 `Disconnected`

### Changed
- Phase 1-1 專案骨架全部完成（1-1a ~ 1-1g 共 7 個子任務）

## [2026-04-13] — Phase 1-1e 前後端通訊串接
### Added
- `web/app/api/[...path]/route.ts` — catch-all API proxy，將 `/api/*` 轉發至 FastAPI backend
- `web/lib/api.ts` — 前端統一 API client（`api<T>(path)` 函式 + 錯誤攔截 + `ApiRequestError` 類別）
- 支援所有 HTTP method（GET/POST/PUT/PATCH/DELETE）、query string 保留、body 轉發
- 後端不可用時回傳 502 + 標準錯誤格式

## [2026-04-13] — Phase 1-1d Alembic 初始化 + users 表
### Added
- Alembic async migration 環境（`alembic/env.py` 改寫為 asyncio + asyncpg）
- `models/user.py` — User SQLAlchemy model（UUID PK、email、name、role enum、google_id、timestamps）
- 第一次 migration `29ec153bbf77_create_users_table`：建立 `users` 表 + `user_role` enum + email/google_id unique index

## [2026-04-13] — Phase 1-1c PostgreSQL + Redis 連線
### Added
- `core/database.py` — SQLAlchemy async engine + sessionmaker + `Base` 宣告式基底 + `get_db` 依賴注入
- `core/redis.py` — Redis async client 初始化/關閉 + `get_redis` 依賴注入
- `main.py` 新增 `lifespan` context manager 管理 DB engine dispose + Redis 連線生命週期
- `api/routes/health.py` 升級為完整健康檢查：回傳 DB + Redis 連線狀態（`connected` / `disconnected`）
- `api/deps.py` 匯出 `get_db`、`get_redis` 供路由依賴注入使用

## [2026-04-13] — Phase 1-1b FastAPI 專案建立
### Added
- `backend/` 目錄結構：`api/routes/`、`api/middleware/`、`models/`、`services/`、`core/`
- `pyproject.toml` + `requirements.lock` 依賴管理（FastAPI 0.135 + Pydantic 2.13 + SQLAlchemy 2.0 + asyncpg）
- `core/config.py` — Pydantic Settings 管理環境變數（DB、Redis、Auth、OpenAI、Judge0）
- `core/errors.py` — 標準錯誤回應模型 `ErrorResponse` + 全域例外處理（`AppError` → JSON）
- `main.py` — FastAPI 進入點 + CORS middleware（僅允許 NEXTAUTH_URL）+ health route
- `api/routes/health.py` — `GET /health` 端點
- `.env.example` — 環境變數範本

## [2026-04-13] — Activity Bar 放大並加入文字標籤
### Changed
- Activity Bar 從 48px icon-only 改為 180px icon + 文字標籤（英文名稱 + 中文說明）
- Chat Panel 預設寬度改為 350px（pixel-based），修正原本過窄的問題

## [2026-04-13] — Phase 1-1g 前端 UI 基礎建設
### Added
- 安裝 shadcn/ui（base-nova style, dark preset）+ lucide-react + react-resizable-panels v4
- Activity Bar 元件（48px 左側導覽，9 項 icon 導覽 + Avatar + Tooltip）
- AI Chat Panel 空殼（Header + 訊息佔位 + 輸入區，支援收合/展開）
- Status Bar 元件（24px 底部，連線狀態 + 語言 + 編碼 + 游標位置 + 精熟度）
- AppShell 全域骨架整合 react-resizable-panels 拖曳調整 Content / Chat 寬度
- 響應式佈局：Desktop 三欄 / Laptop Chat overlay / Tablet 漢堡選單頂部 bar / Mobile 底部 tab bar
- 8 個路由佔位頁面（workspace / learn / quiz / knowledge / overview / notifications / dashboard / settings）
- `useBreakpoint` hook（4 斷點偵測）
- Ctrl+B 快捷鍵收合/展開 Chat Panel

## [2026-04-13] — 新增 UI/UX 介面規格書
### Added
- `docs/ui-ux-spec.md` — 完整 UI/UX 介面規格書（13 章節）
- VSCode 風格 IDE 佈局：Activity Bar + Content Area + AI Chat Panel
- 7 個頁面規格：Workspace、Learn、Quiz、Knowledge、Overview、Dashboard、Settings
- Workspace 檔案樹（多檔案管理）、學生 Overview 獨立頁面、通知系統鈴鐺
- 響應式設計（Desktop / Laptop / Tablet / Mobile 四斷點）
- 動效、快捷鍵、狀態列、Pre-Coding Reflection / Post-Solution 互動流程

## [2026-04-13] — Phase 1-1a Next.js 專案初始化
### Added
- `web/` 目錄：Next.js 16 + App Router + TypeScript + Tailwind CSS v4
- Design Tokens（GitHub Dark）套用為 CSS 變數，Tailwind `@theme` 映射為 utility class
- 字型載入：Inter（UI）+ Noto Sans TC（中文）+ JetBrains Mono（程式碼）
- Dark mode 預設啟用（`<html class="dark">`）
- `lang="zh-TW"` 設定

## [2026-04-13] — Roadmap 新增前端 UI 基礎建設任務
### Changed
- `roadmap.md` Phase 1-1 新增 1-1g：shadcn/ui 安裝 + 全域 Layout + Header Navigation + 響應式骨架，確保後續功能開發時已有成熟 UI 框架

## [2026-04-13] — 文檔交叉引用修正
### Fixed
- `architecture.md` routes 註解補齊 `dashboard, analytics, reflection` 端點
- `changelog.md` Module 9 參考專案計數修正（7→6）
- `db-schema.md` Module 6 `student_answers` 加入 comprehension 擴充欄位交叉引用
- `roadmap.md` Phase 2 header 補齊影響頁面（Workspace Pre-Coding Reflection 側邊欄）
- `roadmap.md` Phase 4-2c `dialogue_act` enum 補漏 `acknowledgment`

## [2026-04-13] — 新增 Pre-Coding Reflection 反認知外包機制
### Added
- 跨模組機制：Pre-Coding Reflection（解題前反思閘門，方案 B 一次追問機會）
- 跨模組機制：Post-Solution Comprehension Check（EPL / 預測輸出 / 變體挑戰）
- DB Schema：`reflections` 表 + `student_answers` 擴充 comprehension 欄位
- API：Reflection 端點（create + update + get）+ Quiz comprehension 端點
- Roadmap：Phase 2 新增 2-5（反思閘門）+ 2-6（理解驗證）、Phase 3-1 新增 3-1e
- 學術參考：7 篇新增至 references.md（CodeAid、PRIMM、EPL、Self-explanation 等）

### Changed
- modules.md Module 6/7 加入反思觸發點、Module 9 加入反認知外包指標
- edf-pipeline.md Evidence 層加入反思內容注入、Feedback 層加入反思引用
- references.md 新增 Pre-Coding Reflection 參考區塊

## [2026-04-13] — 新增 Module 9 學習行為分析模組
### Added
- Module 9：學習行為分析（教師專屬，Phase 4）— 中粒度追蹤 coding 行為與 AI 互動
- DB Schema：`coding_events` 事件紀錄表 + `behavior_aggregates` 預聚合表
- `chat_messages` 擴充 `dialogue_act` 欄位（Phase 4-2c）
- API：Behavior Analytics 端點（班級總覽/散佈圖/熱力圖/個人時序/摘要）
- Roadmap Phase 4 拆分為 5 子階段（4-1 班級管理 → 4-2 資料收集 → 4-3 分析演算法 → 4-4 視覺化 → 4-5 作業指派）
- 參考專案：ProgSnap2、KOALA、StudyChat、pyBKT、PM4Py、OpenLAP 等 6 個新增至 references.md
- 目錄結構新增 `backend/services/analytics/`

### Changed
- modules.md 擴充為 9 模組
- CLAUDE.md 更新模組數量

## [2026-04-13] — 新增開源參考專案文檔
### Added
- `docs/references.md` — 8 個開源參考專案對照表（DeepTutor、OATutor、Mr. Ranedeer、EduAdapt-AI 等）
- 各功能最佳參考來源對照（EDF、RAG、Knowledge Tracing、智慧出題、學習路徑）
- 學術資源連結（論文、awesome list）

### Changed
- `docs/modules.md` — Module 3/4/6/7 加入對應開源參考來源
- `docs/roadmap.md` — Phase 1-4、2-1、2-3、2-4、3-1 加入參考專案指引
- `.claude/rules/edf-pipeline.md` — 加入開源參考區塊
- `CLAUDE.md` — 文件索引新增 references.md

## [2026-04-13] — 文檔一致性修正
### Fixed
- 將 `CHANGELOG.md` 搬移至 `docs/changelog.md`，與 CLAUDE.md 文件索引一致
- 修正 changelog 格式：每次變更使用獨立日期標頭，移除非標準的 `Previous` 區塊
- 統一導覽 Tab 命名：wireframe Header 的 `Graph` → `Knowledge`，並補上 `Dashboard` tab
- api-spec.md 新增 Dashboard API 端點（`/api/dashboard/summary` + `/api/dashboard/activity`）

## [2026-04-13] — Phase 0 規劃文檔完善
### Changed
- Roadmap 拆分為原子級子任務（每個 checkbox = 一次對話可完成）
- DB Schema 補齊 index/constraint 標記（unique、GIN、HNSW、複合索引）
- EDF pipeline 補完 Bloom 6 級定義 + Hint Ladder 6 級策略表
- architecture.md 新增前後端通訊模式（Next.js API proxy）+ 標準錯誤 JSON 格式
- API spec 更新 Chat 端點（SSE streaming + session CRUD）
- rules/frontend.md 補入測試策略 + API 呼叫規範

### Added
- `.env.example` — 環境變數範本
- `db-schema.md` Module 3 Chat Session 表（chat_sessions + chat_messages）

## [2026-04-12] — 文檔架構重構
### Changed
- 重構全部文檔架構，最佳化 Claude Code 上下文效率
- 新增 `.claude/rules/` 自動注入規則（frontend、backend、edf-pipeline）
- 拆分大檔案：modules + db-schema、ui-wireframes + rules/frontend
- 合併冗餘文件：06-phases → roadmap、00-overview → CLAUDE.md
- 刪除 7 個舊文件，重組為 8 個 docs + 3 個 rules

### Added
- `.claude/rules/frontend.md` — 前端 Design Tokens、元件規格、響應式（自動注入 web/**）
- `.claude/rules/backend.md` — 錯誤處理、安全規範、環境變數（自動注入 backend/**）
- `.claude/rules/edf-pipeline.md` — EDF 管線規範（自動注入 backend/services/edf/**）
- `docs/architecture.md` — 系統架構圖 + 目錄結構
- `docs/modules.md` — 8 模組功能摘要
- `docs/db-schema.md` — 全部 DB Schema
- `docs/ui-wireframes.md` — 5 頁 wireframe

### Removed
- `docs/00-overview.md` — 內容已涵蓋在 CLAUDE.md
- `docs/01-tech-stack.md` — 拆分至 architecture.md + CLAUDE.md
- `docs/02-modules.md` — 拆分至 modules.md + db-schema.md + edf-pipeline.md
- `docs/03-ui-design.md` — 拆分至 ui-wireframes.md + rules/frontend.md
- `docs/04-api-spec.md` — 重命名為 api-spec.md
- `docs/05-engineering.md` — 拆分至 rules/backend.md
- `docs/06-phases.md` — 合併至 roadmap.md

## [2026-04-11] — 專案初始化
### Added
- 新增 `CLAUDE.md` 專案級開發指揮中心
- 專案初始化，建立 Git repository
- 新增 .gitignore
