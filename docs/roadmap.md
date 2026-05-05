# Roadmap

> **執行策略**：功能優先（Phase 2 → 3）→ 部署（Phase 4）→ 教師端（Phase 5）。
> 因 API 串接 + Zeabur 部署反覆卡關，將部署延後至學生端功能全數完成後一次處理，避免邊開發邊維運耗能。
> **OSS 重用**：開發前必查 `docs/references.md` §1 決策矩陣（CLAUDE.md 守則 #7）。

## Phase 1：基礎建設（MVP）✅
> 完成標準：學生可登入、寫 C++ 程式碼、執行、與 AI 對話學習
> 對應頁面：Workspace (Page 1)

### 1-1 專案骨架
- [x] 1-1a 建立 Next.js 15 專案（App Router + TypeScript + Tailwind）
- [x] 1-1g 前端 UI 基礎建設（shadcn/ui + 全域 Layout + Header Nav + 響應式骨架）
- [x] 1-1b 建立 FastAPI 專案（專案結構 + Pydantic Settings + CORS）
- [x] 1-1c PostgreSQL + Redis 連線（SQLAlchemy async + redis-py）
- [x] 1-1d Alembic 初始化 + 第一次 migration（users 表）
- [x] 1-1e 前後端通訊串接（Next.js API proxy → FastAPI）
- [x] 1-1f Health check 端點 + 前端連線狀態顯示

### 1-2 Auth 模組
- [x] 1-2a NextAuth.js 設定（Google OAuth provider）
- [x] 1-2b 後端 JWT 驗證 middleware（解析 NextAuth token）
- [x] 1-2c 使用者首次登入自動建立 DB 記錄
- [x] 1-2d 前端登入/登出頁面 + 未登入重導
- [x] 1-2e Role-based 權限 middleware（student/teacher/admin）

### 1-3 程式碼編輯與執行
- [x] 1-3a CodeMirror 6 整合（C++ 語法高亮 + One Dark 主題）
- [x] 1-3b Workspace 頁面基礎佈局（Editor + Output + Toolbar）
- [x] 1-3c Judge0 API client（submit + polling 取結果）
- [x] 1-3d 前端 Run 按鈕串接 + Output Panel 顯示結果
- [x] 1-3f react-resizable-panels 拖曳調整

### 1-4 EDF 教學管線
> 參考：OATutor (BKT→hint→feedback)、Mr. Ranedeer (prompt 設計)、BloomBERT (Bloom 分類)
- [x] 1-4a Evidence 層：LLM 結構化輸出（錯誤分類 + ConceptTag + Bloom）
- [x] 1-4b Decision 層：Bloom × Hint Ladder 策略矩陣
- [x] 1-4c Feedback 層：分層 prompt 組裝 + 輸出驗證
- [x] 1-4d Chat API 端點（interact + history）
- [x] 1-4e 安全防護：輸入三層防護 + 輸出完整程式碼阻擋

### 1-5 AI 對話介面
- [x] 1-5a Chat Panel 元件（訊息氣泡 + 輸入框 + 串流顯示）
- [x] 1-5b 對話歷史持久化（DB 存取 + session 管理）
- [x] 1-5c Run 結果自動注入 Chat context
- [x] 1-5d Chat Panel 收合/展開 toggle

### 1-6 介面精修（統一視覺協議）
> 完成標準：6 份設計系統借鑑（Cursor/Warp/Linear/Claude/Vercel/Raycast）僅貢獻結構模式，所有視覺基本元素統一為 GitHub Dark；通過 §5 違和感 7 條檢核。
> 詳細設計規格與借鑑映射：`docs/design-plan.md`、`docs/design-references/*.md`
- [x] 1-6a Surface / Shadow / Border / Radius token 增補（design-plan §3.1-3.5）→ 同步 `frontend.md`
- [x] 1-6b Inter OpenType `cv01, ss03` 全站套用 + 三權重檢核（design-plan §3.4）
- [x] 1-6c Output Panel Run Block 化（每次 Run 為獨立可摺疊 block + status badge + Run→Chat 按鈕）（design-plan §2.3）
- [x] 1-6d Chat 訊息氣泡 ring 區分 user/AI + Bloom 等級 badge（design-plan §2.4）
- [x] 1-6e Toolbar Linear 風格化（高度 48px + 5 頁籤 + 檔名儲存狀態）（design-plan §2.5）
- [x] 1-6f EDF Pipeline mini timeline（在每則 AI 訊息上方顯示教學決策過程）（design-plan §2.1）

> 部署原 1-7 已移至 **Phase 4**（功能優先策略）

## Phase 2：智慧功能
> 完成標準：RAG 檢索可用、知識圖譜可視覺化、弱項可自動出題
> 對應頁面：Knowledge (Page 4)、Quiz 基礎版、Workspace 擴充（Pre-Coding Reflection 側邊欄）

### 2-1 RAG 知識檢索
> **OSS**：✅ Tier 1 LlamaIndex `PGVectorStore` + `IngestionPipeline`（禁止自寫 chunking/embedding）
> 參考：DeepTutor hybrid retrieval 模式（Tier 3）
- [x] 2-1a pgvector 擴充啟用 + documents 表 migration（chunks/向量表交給 LlamaIndex 2-1b 自動建立）
- [x] 2-1b LlamaIndex 索引管線（用 `IngestionPipeline`，不自刻）
  - 完成：`backend/services/rag/{pipeline,ingest}.py` + `scripts/verify_rag_ingest.py`；向量表 `data_codedge_rag` 自動建立（vector(1536)）
  - 驗證通過：範例教材 → chunk 寫入向量表（2026-05-04，使用者已確認）
- [x] 2-1c 檢索 service（用 LlamaIndex query engine + 可選 BM25 reranking）
  - 完成：`backend/services/rag/retrieve.py`（`retrieve_chunks` + `RetrievedChunk`） + `scripts/verify_rag_retrieve.py`
  - 暫不實作 BM25（roadmap 標註可選；2-1d 後視需要補）；驗證通過 2026-05-04
- [x] 2-1d RAG 結果注入 EDF Feedback 層 prompt
  - 完成：`backend/services/edf/rag_integration.py`（44 行 helper）+ `feedback.py` 注入 `rag_block`；觸發條件沿用 Decision 層 `strategy.use_rag`
  - 失敗安全：`fetch_rag_chunks_safe` 吞所有異常回傳 `[]`，RAG 失敗不阻擋教學回應
  - 驗證通過：22 個 feedback/rag 測試 + 18 個 evidence/decision 測試全綠（2026-05-04）

### 2-2 知識圖譜
> **OSS**：✅ Tier 1 Cytoscape.js + `cytoscape-fcose` layout（禁止自刻力導向圖）
- [x] 2-2a concepts + concept_edges 表 migration + 初始 20 ConceptTag seed
  - 完成：alembic migration `c3d4e5f6a7b8`；`concepts` 含 unique(tag) + check(difficulty 1-5) + index(category)；`concept_edges` 含 4-value ENUM `concept_edge_type` + CASCADE FK + unique(source/target/type) + check(無自環)
  - 20 筆 seed 分 6 個 category（基礎語法 6 / 記憶體 4 / 物件導向 3 / STL 2 / 演算法 2 / 進階 3）
  - ⚠ category / difficulty / name_zh 為暫定值，記於 `docs/tech-debt.md`，2-2c 後校準
- [x] 2-2b 圖譜查詢 service（全圖 / 單節點 + 鄰居）
  - 完成：`models/concept.py` ORM + `services/graph/queries.py`（`get_full_graph` + `get_concept_neighborhood`） + `api/routes/concepts.py`（`GET /concepts/graph` + `GET /concepts/{tag}` 含方向標記）
  - 9 個新測試 + 既有 96 全綠 = 105 passed（2026-05-04）
- [x] 2-2c Knowledge 頁面：Cytoscape.js 圖譜渲染
  - 完成：`web/components/knowledge/{knowledge-graph,*-style,*-types}.tsx` + 替換 `(app)/knowledge/page.tsx`
  - fcose 自動佈局；節點顏色依 category、大小依 difficulty；點選擴增至 header（panel 留給 2-2d）
  - 連帶修兩個阻塞 bug：Auth.js v5 HKDF info 字串對齊 + Postgres ENUM `values_callable`
- [x] 2-2d Concept Detail Panel（點擊節點顯示詳情）
  - 完成：`web/components/knowledge/concept-detail-panel.tsx`，串 `GET /concepts/{tag}`，渲染基本資訊 + 先修 + 進階 sections
  - 互動：點鄰居切換 concept、點 X 關閉、點圖上其他節點切換
- [x] 2-2e Knowledge Graph 視覺精修（Obsidian Graph View 風格 + edges seed）
  - Part 1 ✅：migration `d4e5f6a7b8c9` 種 23 條邊（20 prerequisite + 3 related）— 邊內容為暫定，記於 `tech-debt.md`
  - Part 2 ✅：ellipse 節點 + 22-38px 尺寸 + label 外下方 + hover 點亮鄰居/淡化其他（opacity 0.18）
  - 連帶修：`models/concept.py` `EdgeType` 加 `values_callable`（同 User/Chat enum bug 第三處）

### 2-3 精熟度追蹤
> **OSS**：✅ Tier 1 **`pip install pyBKT`**（scikit-learn 風格 API，**禁止 port OATutor JS 版**）
- [x] 2-3a student_mastery 表 migration
  - 完成：alembic migration `e5f6a7b8c9d0` + `models/mastery.py` ORM
  - schema：confidence (0-1) / exposure / success / error counts / bloom_level (1-6 nullable smallint) / last_practiced_at；UNIQUE(user_id, concept_id) + 3 check constraints + 2 indexes
- [x] 2-3b 精熟度更新邏輯（pyBKT Model + EDF Evidence 結果 → confidence 調整）
  - 完成：`services/mastery/{updater,__init__}.py` + `tests/test_mastery_updater.py`（10 測試）
  - 串入 `services/chat.py` interact() 流程，每次 EDF Evidence 後更新 mastery；失敗安全（同 RAG 處理）
  - **pyBKT 使用策略**：套件已裝（OSS 守則 ✅）；cold-start 階段用標準 BKT Bayes 公式線上更新；Phase 5 真實資料後跑 `pyBKT.Model.fit()` 學 per-concept 參數，餵入此 service 即可
- [x] 2-3c 圖譜節點顏色依精熟度著色（綠/黃/紅/灰）
  - 後端：`GET /concepts/mastery` + `services/mastery/queries.py` `get_user_mastery_summary`
  - 前端：fetch 上提至 page 層，KnowledgeGraph 改 presentational；節點 underlay 圓環依 confidence 分群（≥0.8 mastered / 0.4-0.8 learning / <0.4 struggling / 無 row 不畫）；Detail Panel 加「我的精熟度」區塊
  - 6 個新測試（3 backend + 3 frontend type/style 同步驗證 via TS）— 共 118 passed

### 2-4 智慧出題
> **OSS**：LlamaIndex 教材檢索注入 prompt（Tier 1）
> 參考：OATutor adaptive selection 思路（Tier 3，不引程式碼）
- [x] 2-4a questions + student_answers 表 migration
  - 完成：alembic `f6a7b8c9d0e1` + `models/quiz.py`（Question + StudentAnswer + QuestionType / QuestionSource）
  - enum 改 String + CHECK（避開 PG ENUM enum.value/.name 同款坑）；concept_tags 用 JSON 而非 PG `text[]`（SQLite 測試相容）
  - Comprehension 擴充欄位（2-6）留給後續 migration
- [x] 2-4b Select 階段：弱項概念選取 + 知識圖譜關聯
  - 完成：`services/quiz/select.py` `select_weak_concepts(db, user_id, top_k=5)`
  - 弱項定義：`confidence < 0.4 AND exposure_count >= 1`；中心度加權 score = (1-conf) × (1 + 0.2 × out_degree)
  - Cold-start 回 []；7 個單元測試（邊界條件 + 排序 + 中心度 + top_k）
- [x] 2-4c Generate 階段：LLM 出題 + RAG 教材注入
  - 完成：`services/quiz/generate.py` `generate_question(db, concept, type, difficulty, bloom)` + 三種 type Pydantic content 模型
  - OpenAI `json_object` mode + RAG `retrieve_chunks` 注入；分層錯誤（LLM_ERROR / LLM_PARSE_ERROR / LLM_VALIDATION_ERROR）
  - 寫入 `questions.validated=False`，等 2-4d 過審；8 個單元測試（mock LLM + RAG）
- [x] 2-4d Validate 階段：LLM 自我檢查答案
  - 完成：`services/quiz/validate.py` `validate_question(db, question) -> ValidationReport`
  - 三面向審查（answer_correct / concept_fits / bloom_appropriate）皆 True 才 flip `validated=True`；任一 False 回 `ValidationReport(passed=False, issues=[...])` 讓 caller 決定 retry / 丟棄
  - 8 個單元測試（pass / 各面向 fail / 多 fail / LLM error / parse error / schema error）
- [x] 2-4e Quiz API 端點（generate + submit + history）
  - 完成：`services/quiz/{grade,orchestrator}.py` + `api/routes/quiz.py`
  - 端點：`POST /quiz/generate`（auto-select + retry validation）/ `POST /quiz/submit`（grade + mastery 更新）/ `GET /quiz/history`（分頁）
  - 答案 mask：generate 不回 answer_index/answers；submit 後才完整回 content
  - Grading：MC 比 selected_index、Fill 用 trim+casefold；Coding MVP 不自動判分（待 Judge0 整合）
  - 15 個新測試（8 grade + 7 route HTTP integration）

### 2-5 Pre-Coding Reflection（解題前反思）
> 參考：CodeAid (不給直接答案)、PRIMM、Polya 解題四步驟、Self-explanation effect (Chi et al.)
- [x] 2-5a reflections 表 migration + Reflection API 端點（create + update + get）
  - 完成：`alembic/versions/a7b8c9d0e1f2_create_reflections_table.py` + `models/reflection.py` + `services/reflection/crud.py` + `api/routes/reflection.py`
  - schema：`source_type` (quiz/learning_unit) + `source_id` polymorphic UUID + UNIQUE(user, source_type, source_id) + `quality_score` 0–1 CHECK
  - 端點：`POST /reflection`（201）/ `GET /reflection/{id}` / `PATCH /reflection/{id}`，對齊 api-spec.md
  - 權限：他人反思一律 404（避免列舉攻擊）；UNIQUE 衝突回 409
  - 18 個新測試（9 service + 9 HTTP integration）
- [x] 2-5b 反思品質評估 service（LLM 快速評分 + 追問生成）
  - 完成：`services/reflection/evaluate.py` `evaluate_reflection(reflection, question) -> ReflectionEvaluation`
  - 三面向評分（understanding / plan_quality / concept_recall）平均成 quality_score；`QUALITY_THRESHOLD=0.6` 才回追問
  - 整合到 `create_reflection` / `update_reflection`：寫入後自動評分；no-op PATCH 不呼叫 LLM
  - 容錯：無 API key / LLM 異常 / parse error / schema 違反 / 分數超範圍 → fallback `quality_score=None` 不擋寫入
  - 16 個新測試（9 evaluate unit + 5 service integration + 2 HTTP integration）
- [x] 2-5c 程式撰寫題開題時觸發反思表單 UI（必填 → 品質評估 → 追問或放行）
  - 完成：`lib/reflection.ts`（API helper）+ `components/reflection/{reflection-form,reflection-followup,reflection-flow,reflection-flow-parts}.tsx`
  - Modal 狀態機：form → submitting → (approved | followup) → resubmit → ...；MAX_FOLLOWUP_ROUNDS=2 後提供「已盡力直接看題」放行
  - LLM 失敗（quality_score=null）視為通過，不擋學生
  - Quiz 占位頁改造為 demo 觸發點：`POST /quiz/generate type=coding` → ReflectionFlow → 放行後顯示題目
  - 元件全部受控 prop-driven，預留給 2-5d 側邊欄、3-1e 練習 tab 復用
  - ESLint / TypeScript / next build 全綠
- [x] 2-5d 反思計畫側邊欄（Workspace 內持續顯示 + 可編輯）
  - 完成：`lib/active-reflection.ts`（sessionStorage helper + 同/跨 tab event）+ `lib/reflection.ts` 補 `getReflection`
  - 元件：`components/reflection/reflection-sidebar.{tsx,view.tsx,edit.tsx}` + `use-active-reflection.ts` hook
  - Workspace 整合：Toolbar 加 ListChecks toggle（active reflection 時顯示綠色 dot）；左側 resizable Panel（28%/20%/40%）；進入頁面有 active reflection 自動展開
  - Quiz demo ReflectionSummary 加「前往 Workspace 作答」`<Link>`，點擊寫 sessionStorage
  - 編輯模式呼叫 PATCH /reflection/{id} → 觸發後端重新評分；404 自動清過期 ID 退回空狀態
  - ESLint / TypeScript / next build 全綠
- [x] 2-5e 反思內容注入 EDF Evidence 層（AI Tutor 可引用學生計畫）
  - 完成：`services/edf/reflection_context.py`（兩種視圖：Evidence 簡短 / Feedback 詳細）
  - Evidence：`analyze_evidence(reflection_summary)` 注入 user prompt 結尾
  - Feedback：`build_system_prompt(reflection_block)` 注入順序 context → reflection → rag（測試強制保證）
  - chat service：`_load_reflection_safely` best-effort + 權限隔離（user_id 不符視為不存在）
  - chat API：`InteractRequest.reflection_id` 透傳；前端 use-chat 自動讀 sessionStorage 帶入
  - 18 個新測試（11 reflection_context + 3 feedback prompt + 4 chat integration）
  - 全套 208 tests 全綠；ESLint / TypeScript / next build 全綠

### 2-6 Post-Solution Comprehension Check（解題後理解驗證）
> 參考：EPL (Fowler et al.)、Variation Theory (Marton)
- [x] 2-6a student_answers 表擴充 comprehension 欄位 + Comprehension API
  - Migration `b8c9d0e1f2a3`：4 個 nullable 欄位（type/prompt/answer/passed）+ CHECK enum
  - ORM：`ComprehensionType` enum（epl/predict_output/variation）+ `StudentAnswer` 加欄位
  - Service `services/comprehension/`：get + upsert（擁有權檢查 → 404）
  - API：`GET /comprehension/{id}`、`PUT /comprehension/{id}` partial upsert
  - 10 個新測試，全套 218 tests 全綠
- [x] 2-6b EPL 驗證：LLM 生成「用自己的話解釋」題 + 評估學生回答
  - `services/comprehension/epl.py` + `epl_prompts.py`：generate / grade 兩條 LLM 流程，3 面向評分（conceptual / specificity / causality）avg ≥ 0.6 為 passed
  - `services/comprehension/orchestrator.py`：start_epl（重置語意）/ submit_epl（強制順序：必須先 generate）
  - API：`POST /comprehension/{id}/epl/generate`、`POST /comprehension/{id}/epl/grade`
  - 失敗策略：generate → 503；grade → 200 + passed=None（不擋學生）
  - 25 個新測試（16 unit + 9 HTTP），全套 243 tests 全綠
- [x] 2-6c 預測輸出驗證：自動生成新測資 + 比對學生預測
  - `services/comprehension/predict_output.py` + `predict_output_prompts.py`：LLM 生 (input, expected) + 兩階段 grade（normalize 嚴格 → LLM 語意 fallback → mismatch fallback）
  - orchestrator 加 `start_predict_for_answer`（拒非 coding → 422，JSON 編碼存 prompt 不洩漏 expected）+ `submit_predict_for_answer`
  - API：`POST /comprehension/{id}/predict_output/generate`、`POST /comprehension/{id}/predict_output/grade`，response 含 match_method ∈ {exact, semantic, mismatch}
  - expected 對「學生實際程式」推理（含 bug 行為），不是題目正解 — 對齊「能否預測自己程式行為」教學目標
  - 27 個新測試（16 unit + 11 HTTP），全套 270 tests 全綠
- [x] 2-6d 變體挑戰：LLM 生成變體題 + 禁用 AI 的作答環境
  - `services/comprehension/variation.py` + `variation_prompts.py`：LLM 生變體（同概念、不同情境/數值/方向）+ binary grade
  - `_call_llm_json` 共用 helper dedupe LLM boilerplate；StrictBool 拒絕 `"yes"` 等隱式轉型
  - 拆獨立 route 檔 `api/routes/comprehension_variation.py` 避免主 route 超 250 行
  - 「禁用 AI」屬前端責任（後端流程不串接 chat / EDF / hint，docstring 註明）
  - 保守 fallback：grade LLM 失敗 → `passed=False`（避免錯給通過拉高 mastery 信心度）
  - 23 個新測試（13 unit + 10 HTTP），全套 293 tests 全綠
- [x] 2-6e 動態觸發頻率（依學生 EPL 通過率調整）+ 驗證結果影響精熟度
  - `services/comprehension/mastery_hook.py`：comprehension passed → Evidence(NONE/LOGIC) → `update_mastery` BKT 上下調；passed=None 跳過；異常 swallow
  - `services/comprehension/trigger.py`：純規則 `_decide(pass_rate, is_coding)` — cold start → EPL；≥0.8 不觸發；[0.6,0.8)→VARIATION；[0.3,0.6)→PREDICT_OUTPUT；<0.3→EPL；非 coding 自動 fallback EPL
  - 三條 grade workflow（EPL/Predict/Variation）皆在 commit 前串接 mastery hook
  - API：`GET /comprehension/trigger-suggestion/{student_answer_id}`（獨立 route 檔）
  - 27 個新測試（16 unit + 6 HTTP + 4 mastery integration），全套 320 tests 全綠
  - **Phase 2-6 完成 🎉** — 後端教學引擎 + comprehension 驗證閉環就緒

## Phase 3：學習體驗
> 完成標準：學生可從頭到尾跟隨學習路徑，完成測驗，查看進度
> 對應頁面：Learn (Page 2)、Quiz (Page 3)、Dashboard (Page 5)

### 3-1 結構化學習路徑
> **OSS**：拓撲排序 + 弱項補強（**不採用 EduAdapt-AI 的 RL 方案**，過度工程）
- [x] 3-1a learning_paths + learning_units 表 migration
  - Migration `c9d0e1f2a3b4`：兩表 + status CHECK enum + UNIQUE(path_id, order_index) + order_index ≥ 0 CHECK
  - ORM `models/learning.py`：`LearningPath` + `LearningUnit` + `LearningUnitStatus(str, Enum)` (locked/available/in_progress/completed)
  - FK 策略：path.user_id CASCADE / unit.path_id CASCADE / unit.concept_id RESTRICT
  - 12 個新測試，全套 332 tests 全綠
- [x] 3-1b 路徑生成 service（拓撲排序 + 弱項補強，純 Python 實作）
  - `services/learning/topology.py`：priority Kahn's algorithm（純函式，O((N+E) log N)）
  - `services/learning/generator.py`：fetch concepts/edges/mastery → 篩除已熟練 → 拓撲 → 寫入；第一個 unit `available` 其餘 `locked`
  - 弱項優先：confidence 低排前；cold start (未練=0) 自動最前；priority 同 → 插入順序穩定
  - Cycle 容錯：殘留節點附加尾端不擲錯
  - `DEFAULT_SKIP_MASTERED_THRESHOLD = 0.8`；`content` 預留空骨架 `{summary, examples, exercise_question_ids}`
  - 21 個新測試（12 unit + 9 DB 整合），全套 353 tests 全綠
- [x] 3-1c Learn 頁面：路徑視覺化 + 進度條
  - Backend：4 endpoints (POST/GET list/GET detail/DELETE) + queries service（避免 N+1 + join concepts）
  - Frontend：page 三模式（list/detail/loading）+ path-card 進度條 + unit-status-icon 4 狀態 + generate-path-dialog
  - 13 個新後端測試，全套 366 tests 全綠；TypeScript/ESLint/next build 全綠
- [x] 3-1c+ Concept Graph 重建：59 影片 concept + 線性 PREREQUISITE 鏈
  - Schema migration `d0e1f2a3b4c5`：concepts 加 3 video 欄位
  - Seed migration `e1f2a3b4c5d6`：清空舊 20 EDF concept → seed 59 影片（編號 04-62）+ 58 條線性邊
  - tag 命名 `cpp-NN-keyword`；8 主題分類；difficulty 1-5 漸進
  - PG 驗證 59 + 58；YT video_id 等教授補後 PATCH
- [x] 3-1c++ Learn UX 簡化：onboarding 自動 seed + 移除手動生成 UI
  - 反思：concept graph 固定後，每位學生「生成」結果相同 → 手動 UI 無意義
  - Backend：`ensure_default_path_exists` + `GET /learning/paths/default` lazy seed
  - Frontend 大幅精簡：刪 path-card / generate-path-dialog；page 改為自動 fetch + 直顯 detail
  - 4 個新後端測試，全套 383 tests 全綠
- [x] 3-1d 學習單元內容頁（概念說明 / 範例 / 練習 / 摘要 tab）
  - Backend：`PATCH /learning/units/{id}` + `services/learning/units.py` (status transition 查表驗證 + 解鎖邏輯)
  - 合法 transition: available→in_progress / in_progress→completed (解鎖下一) / in_progress→available (revisit)
  - 非法一律 422 (locked/completed 不可手動設)
  - Frontend：unit-content.tsx 4 tab + 上下單元導航 + ActionButton 依 status 變化；path-detail unit 變可點
  - 13 個新後端測試，全套 379 tests 全綠
  - YT player / 範例 / 摘要為 placeholder，等教授補影片資料或 LLM 生成（見 tech-debt.md）
- [ ] 3-1e 練習 tab 嵌入 Pre-Coding Reflection 觸發點（復用 Phase 2-5 元件）

### 3-2 Quiz 完整版
- [ ] 3-2a Quiz 頁面：選擇題 + 程式撰寫題 UI
- [ ] 3-2b 計時器 + 提示系統（hint_level 0-5）
- [ ] 3-2c 作答結果頁 + EDF 回饋顯示

### 3-3 Dashboard
- [ ] 3-3a Dashboard 頁面：統計卡片 + 今日建議
- [ ] 3-3b 最近活動時間線
- [ ] 3-3c 精熟度總覽圖表

## Phase 4：部署上線（學生端完成後）
> 完成標準：學生端 Phase 1~3 全數完成後，一次性處理 Docker / Zeabur / Judge0 自架 / NextAuth callback / CORS / API proxy 串接。
> ⚠ 上次卡關於 API 串接（前後端 proxy / NextAuth callback URL / CORS / Judge0 endpoint），重啟前需先排查 `web/app/api/*` proxy 設定、`backend/app/core/config.py` 環境變數、Zeabur dashboard service 連線狀態。
> **前置條件**：Phase 1-3 全部完成。

### 4-1 容器化
- [ ] 4-1a Dockerfile（前端 + 後端）— 配置檔已存在，需重新驗證 build
- [ ] 4-1b `pgvector/pgvector:pg16` 容器配置（Phase 2-1 完成後驗證）
- [ ] 4-1c Judge0 自架 docker-compose（取代 RapidAPI 50 次/天限制）

### 4-2 Zeabur 部署
- [ ] 4-2a 環境變數分層配置（dev/prod，敏感資訊用 Zeabur Secrets）
- [ ] 4-2b Zeabur service 串接（internal DNS / Postgres / Redis / Judge0）— `zeabur.json` 已存在，需驗證
- [ ] 4-2c NextAuth callback URL + CORS 設定（前後端網域）

### 4-3 上線驗證
- [ ] 4-3a Golden path：登入 → 寫碼 → 執行 → AI 對話 → RAG 檢索 → 出題作答
- [ ] 4-3b 監控：Sentry / 日誌聚合 / 健康檢查
- [ ] 4-3c 效能 baseline（首次互動時間、LLM p95 延遲、Judge0 成功率）

---

## Phase 5：教師端（部署後）
> 完成標準：教師可管理班級、查看學生行為分析圖表、指派作業
> 對應頁面：Teacher Dashboard（教師專屬，學生不可見）
> **前置條件**：Phase 4 部署完成（教師分析需要實際學生資料）。

### 5-1 班級管理
- [ ] 5-1a classes + class_members 表 migration
- [ ] 5-1b 班級 CRUD API（建立/邀請碼/加入/移除）
- [ ] 5-1c 教師 Dashboard 頁面骨架 + 班級管理 UI

### 5-2 行為資料收集（Module 9）
> **OSS**：✅ Tier 2 直接採用 ProgSnap2 EventType schema + StudyChat dialogue act 分類 schema（references.md §1）
- [ ] 5-2a coding_events 表 migration（**採用 ProgSnap2 五欄主鍵 + EventType 列舉**）
- [ ] 5-2b 後端 event logging service（從 Judge0 + EDF 現有流程擷取資料）
- [ ] 5-2c chat_messages 擴充 dialogue_act 欄位（**採用 StudyChat schema**：asking_hint/clarification_request/debugging/off_topic/acknowledgment/verification）
- [ ] 5-2d 行為指標聚合 service（編譯頻率/成功率/修復時間/hint 分布等）

### 5-3 行為分析演算法（Module 9）
> **OSS**：✅ Tier 1 pyBKT（精熟度追蹤）+ `prefixspan`（sequential pattern mining，**取代 AGPL 的 PM4Py**）
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

## 已確認決策

- Terminal：Batch 模式，不需即時互動式 terminal
- 介面語言：繁體中文為主，暫不做多語系
- UI：GitHub Dark + VS Code 風格，純 Dark Mode
- Judge0：開發期 RapidAPI (免費 50 次/天) → 上線後自架
- 部署：Zeabur (Tencent Tokyo VPS) | 使用者規模：初期 < 100 人
- 即時通訊：Phase 1 用 REST + SSE (chat streaming)，未來視需求加 WebSocket
- 介面借鑑：6 份來源僅貢獻結構模式，視覺基本元素統一為 GitHub Dark（design-plan.md §0.3 七條硬規則）
- **OSS 重用**：開發前必查 `docs/references.md` §1 決策矩陣；禁止 AGPL/GPL 套件；禁止移植已有對應套件的演算法（如 BKT 必用 pyBKT）
- **執行順序**：功能優先（Phase 2 → 3）→ 部署（Phase 4）→ 教師端（Phase 5）；避免邊開發邊維運耗能
