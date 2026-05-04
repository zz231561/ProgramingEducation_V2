# 變更日誌

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
