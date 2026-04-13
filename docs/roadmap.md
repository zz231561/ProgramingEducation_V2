# Roadmap

## Phase 1：基礎建設（MVP）
> 完成標準：學生可登入、寫 C++ 程式碼、執行、與 AI 對話學習
> 對應頁面：Workspace (Page 1)

### 1-1 專案骨架
- [ ] 1-1a 建立 Next.js 15 專案（App Router + TypeScript + Tailwind）
- [ ] 1-1b 建立 FastAPI 專案（專案結構 + Pydantic Settings + CORS）
- [ ] 1-1c PostgreSQL + Redis 連線（SQLAlchemy async + redis-py）
- [ ] 1-1d Alembic 初始化 + 第一次 migration（users 表）
- [ ] 1-1e 前後端通訊串接（Next.js API proxy → FastAPI）
- [ ] 1-1f Health check 端點 + 前端連線狀態顯示

### 1-2 Auth 模組
- [ ] 1-2a NextAuth.js 設定（Google OAuth provider）
- [ ] 1-2b 後端 JWT 驗證 middleware（解析 NextAuth token）
- [ ] 1-2c 使用者首次登入自動建立 DB 記錄
- [ ] 1-2d 前端登入/登出頁面 + 未登入重導
- [ ] 1-2e Role-based 權限 middleware（student/teacher/admin）

### 1-3 程式碼編輯與執行
- [ ] 1-3a CodeMirror 6 整合（C++ 語法高亮 + One Dark 主題）
- [ ] 1-3b Workspace 頁面基礎佈局（Editor + Output + Toolbar）
- [ ] 1-3c Judge0 API client（submit + polling 取結果）
- [ ] 1-3d 前端 Run 按鈕串接 + Output Panel 顯示結果
- [ ] 1-3e stdin 輸入支援
- [ ] 1-3f react-resizable-panels 拖曳調整

### 1-4 EDF 教學管線
> 參考：OATutor (BKT→hint→feedback)、Mr. Ranedeer (prompt 設計)、BloomBERT (Bloom 分類)
- [ ] 1-4a Evidence 層：LLM 結構化輸出（錯誤分類 + ConceptTag + Bloom）
- [ ] 1-4b Decision 層：Bloom × Hint Ladder 策略矩陣
- [ ] 1-4c Feedback 層：分層 prompt 組裝 + 輸出驗證
- [ ] 1-4d Chat API 端點（interact + history）
- [ ] 1-4e 安全防護：輸入三層防護 + 輸出完整程式碼阻擋

### 1-5 AI 對話介面
- [ ] 1-5a Chat Panel 元件（訊息氣泡 + 輸入框 + 串流顯示）
- [ ] 1-5b 對話歷史持久化（DB 存取 + session 管理）
- [ ] 1-5c Run 結果自動注入 Chat context
- [ ] 1-5d Chat Panel 收合/展開 toggle

### 1-6 部署
- [ ] 1-6a Dockerfile（前端 + 後端）
- [ ] 1-6b Zeabur 部署配置（環境變數 + service 串接）
- [ ] 1-6c 首次上線驗證（登入 → 寫碼 → 執行 → 對話 golden path）

## Phase 2：智慧功能
> 完成標準：RAG 檢索可用、知識圖譜可視覺化、弱項可自動出題
> 對應頁面：Knowledge (Page 4)、Quiz 基礎版

### 2-1 RAG 知識檢索
> 參考：DeepTutor (hybrid retrieval + citation tracking)、Open TutorAI CE (教材 RAG)
- [ ] 2-1a pgvector 擴充啟用 + documents/chunks 表 migration
- [ ] 2-1b LlamaIndex 索引管線（文件上傳 → chunking → embedding → 存入 DB）
- [ ] 2-1c 檢索 service（query → 向量搜尋 → top-k chunks）
- [ ] 2-1d RAG 結果注入 EDF Feedback 層 prompt

### 2-2 知識圖譜
- [ ] 2-2a concepts + concept_edges 表 migration + 初始 20 ConceptTag seed
- [ ] 2-2b 圖譜查詢 service（全圖 / 單節點 + 鄰居）
- [ ] 2-2c Knowledge 頁面：Cytoscape.js 圖譜渲染
- [ ] 2-2d Concept Detail Panel（點擊節點顯示詳情）

### 2-3 精熟度追蹤
> 參考：OATutor BKT 演算法（`BKT-brain.js`、`bktParams.js`）→ 移植為 Python 版
- [ ] 2-3a student_mastery 表 migration
- [ ] 2-3b 精熟度更新邏輯（EDF Evidence 結果 → confidence 調整）
- [ ] 2-3c 圖譜節點顏色依精熟度著色（綠/黃/紅/灰）

### 2-4 智慧出題
> 參考：OATutor (adaptive selection)、DeepTutor (教材出題)、EduAdapt-AI (difficulty scaling)
- [ ] 2-4a questions + student_answers 表 migration
- [ ] 2-4b Select 階段：弱項概念選取 + 知識圖譜關聯
- [ ] 2-4c Generate 階段：LLM 出題 + RAG 教材注入
- [ ] 2-4d Validate 階段：LLM 自我檢查答案
- [ ] 2-4e Quiz API 端點（generate + submit + history）

## Phase 3：學習體驗
> 完成標準：學生可從頭到尾跟隨學習路徑，完成測驗，查看進度
> 對應頁面：Learn (Page 2)、Quiz (Page 3)、Dashboard (Page 5)

### 3-1 結構化學習路徑
> 參考：EduAdapt-AI (RL-based learning path optimization + content graph)
- [ ] 3-1a learning_paths + learning_units 表 migration
- [ ] 3-1b 路徑生成 service（拓撲排序 + 弱項補強）
- [ ] 3-1c Learn 頁面：路徑視覺化 + 進度條
- [ ] 3-1d 學習單元內容頁（概念說明 / 範例 / 練習 / 摘要 tab）

### 3-2 Quiz 完整版
- [ ] 3-2a Quiz 頁面：選擇題 + 程式撰寫題 UI
- [ ] 3-2b 計時器 + 提示系統（hint_level 0-5）
- [ ] 3-2c 作答結果頁 + EDF 回饋顯示

### 3-3 Dashboard
- [ ] 3-3a Dashboard 頁面：統計卡片 + 今日建議
- [ ] 3-3b 最近活動時間線
- [ ] 3-3c 精熟度總覽圖表

## Phase 4：教師端（未來）

- [ ] 4-1 教師 Dashboard（classes 表 migration + 班級管理 UI）
- [ ] 4-2 作業指派 + 學生進度查看
- [ ] 4-3 班級學習數據分析

## 已確認決策

- Terminal：Batch 模式，不需即時互動式 terminal
- 介面語言：繁體中文為主，暫不做多語系
- UI：GitHub Dark + VS Code 風格，純 Dark Mode
- Judge0：開發期 RapidAPI (免費 50 次/天) → 上線後自架
- 部署：Zeabur (Tencent Tokyo VPS) | 使用者規模：初期 < 100 人
- 即時通訊：Phase 1 用 REST + SSE (chat streaming)，未來視需求加 WebSocket
