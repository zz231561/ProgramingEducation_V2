# 模組規劃

> DB Schema 詳見 `db-schema.md`，EDF 管線詳見 `.claude/rules/edf-pipeline.md`

## Module 1：Auth 與使用者管理
Google OAuth (NextAuth.js) + JWT + 角色 (student/teacher/admin) + Rate limiting (per-user)

## Module 2：程式碼編輯與執行
CodeMirror 6 (C++ 語法高亮) + Judge0 API 編譯執行 + stdin 支援 + Batch 模式
- 開發期用 Judge0 RapidAPI (免費 50 次/天)，上線後自架
- 執行 timeout 統一 10 秒，language_id 抽象化供未來擴充

## Module 3：EDF 教學管線
Evidence → Decision → Feedback 三層管線，保留 V1 核心設計。詳見 `.claude/rules/edf-pipeline.md`
- 參考：OATutor (BKT→hint selection→feedback)、Mr. Ranedeer (prompt 設計)、BloomBERT (Bloom 分類驗證)

## Module 4：RAG 知識檢索
pgvector + LlamaIndex 索引 C++ 教材/cppreference/講義，檢索結果注入 EDF Feedback 層 prompt
- Embedding: OpenAI text-embedding-3-small
- 參考：DeepTutor (hybrid retrieval + citation tracking)、Open TutorAI CE (教材上傳→向量化→對話引用)

## Module 5：知識圖譜
PostgreSQL 鄰接表（非 Neo4j，100 人規模 + 20 ConceptTag + <200 邊，不需圖資料庫）
- 先修/包含/特化/相關 4 種邊類型
- Cytoscape.js 或 D3.js 視覺化，節點顏色依精熟度：綠 >0.7 / 黃 0.4-0.7 / 紅 <0.4

## Module 6：智慧出題
4 階段管線 (Select → Generate → Validate → Present)，支援選擇題/填空題/程式撰寫題
- 難度自適應：Bloom 等級 + concept confidence
- 參考：OATutor (adaptive selection)、DeepTutor (教材出題)、EduAdapt-AI (difficulty scaling)

## Module 7：結構化學習路徑
知識圖譜拓撲排序生成路徑，每節點 = 學習單元 (說明 + 範例 + 練習 + 摘要)
- 弱項自動補強：confidence 下降時插入複習單元
- 參考：EduAdapt-AI (RL-based learning path optimization + content graph)

## Module 8：教師 Dashboard（Phase 4）
班級管理、精熟度熱力圖、常見錯誤統計、作業指派。Schema 先設計，後續實作。

## Module 9：學習行為分析（Phase 4，教師專屬）
中粒度追蹤學生 coding 行為與 AI Tutor 互動模式，視覺化圖表呈現行為與成效的關聯。自建分析，不依賴外部服務。

**資料來源（從現有模組擷取，不新增前端 event listener）：**
- Coding 行為：編譯頻率/成功率（Judge0）、錯誤類型分布（EDF Evidence）、修復時間（submit 間隔）、session 時長、程式碼變化量（code_snapshot diff）
- AI 互動行為：對話輪數、hint level 分布（EDF Decision）、AI 建議採納率、對話類型分布（dialogue act 分類）、主動提問 vs 被動觸發
- 學習成效：精熟度趨勢（student_mastery）、Quiz 正確率（student_answers）、Bloom 等級進展

**視覺化圖表：**
- 行為-成效散佈圖：行為指標 vs 精熟度提升，每點 = 一位學生
- 錯誤類型熱力圖：ConceptTag × 學生，顏色 = 錯誤頻率
- 學習行為時序圖：時間軸標記 Run/Chat/Hint 事件
- Hint 階梯使用分布：各 hint level 觸發次數長條圖
- 班級行為群聚分析：依行為模式分群（主動型/被動型/掙扎型）
- 精熟度趨勢線：學生或班級的 confidence 隨時間變化

- 參考：ProgSnap2 + KOALA (事件 schema)、StudyChat (dialogue act 分類)、pyBKT (精熟度演算法)、PM4Py (行為流程分析)、OpenLAP (三層架構)
