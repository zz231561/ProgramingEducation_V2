# 開源參考專案

> 實作各 Phase 時，clone 對應專案深入研究再制定細節計畫。

## 專案總覽

| 專案 | Stars | License | 主要參考價值 | 對應 Phase |
|------|-------|---------|-------------|-----------|
| [DeepTutor](https://github.com/HKUDS/DeepTutor) | 17k+ | Apache-2.0 | RAG hybrid retrieval + Knowledge Graph | Phase 2 |
| [OATutor](https://github.com/CAHLR/OATutor) | 190 | MIT | BKT 精熟度演算法 + Hint pathway | Phase 1-4, 2-3 |
| [Mr. Ranedeer](https://github.com/JushBJJ/Mr.-Ranedeer-AI-Tutor) | 29k+ | — | Socratic prompt template 設計 | Phase 1-4 |
| [EduAdapt-AI](https://github.com/mwasifanwar/eduadapt-ai) | 10 | — | RL learning path + adaptive quiz（FastAPI） | Phase 2-4, 3-1 |
| [BloomBERT](https://github.com/RyanLauQF/BloomBERT) | 36 | MIT | Bloom taxonomy 自動分類 | Phase 1-4 |
| [Socratic-LLM](https://github.com/GiovanniGatti/socratic-llm) | 31 | MIT | Socratic dialogue fine-tuning | Phase 1-4 |
| [Open TutorAI CE](https://github.com/Open-TutorAi/open-tutor-ai-CE) | 48 | BSD-3 | 教材 RAG + 多角色 dashboard | Phase 2-1, 4 |
| [JetBrains Edu Plugin](https://github.com/JetBrains/educational-plugin) | 174 | Apache-2.0 | 漸進式 hint generation | Phase 1-4 |

## 功能對照：各功能最佳參考來源

### EDF 教學管線（Phase 1-4）
- **Evidence 層 — Bloom 分類**: BloomBERT 用 BERT 自動判定認知等級，可作為 LLM 輸出的交叉驗證
- **Decision 層 — 策略矩陣**: 無直接對應開源實作（本專案原創），最接近的是 OATutor 的 BKT → hint selection 流程
- **Feedback 層 — Prompt 設計**: Mr. Ranedeer 的 system prompt 控制教學行為（不給答案、引導提問、風格切換）
- **Socratic 對話**: Socratic-LLM 的 fine-tuning dataset 結構 + 評估 metrics

### Knowledge Tracing / 精熟度追蹤（Phase 2-3）
- **OATutor** — Bayesian Knowledge Tracing (BKT) 實作
  - 核心檔案：`BKT-brain.js`（演算法）、`bktParams.js`（參數設定）
  - 可移植為 Python 版，作為 `student_mastery.confidence` 更新公式
  - 論文驗證：LLM-generated hints 與人工 hints 效果相當（DOI: 10.1371/journal.pone.0304013）
- **OATutor 相關子專案**:
  - [OATutor-GPT-Study](https://github.com/CAHLR/OATutor-GPT-Study) — ChatGPT 生成 hint 的實驗
  - [OATutor-AI-Feedback-Experiment](https://github.com/CAHLR/OATutor-AI-Feedback-Experiment) — AI feedback 效果研究
  - [OATutor-Question-Generation-Final](https://github.com/CAHLR/OATutor-Question-Generation-Final) — AI 出題流程

### RAG 知識檢索（Phase 2-1）
- **DeepTutor** — RAG hybrid retrieval 最成熟的開源實作
  - 四層架構：UI → Agent Modules → Tool Integration → Knowledge Foundation
  - 向量搜尋 + 知識庫的混合檢索策略
  - Session memory + citation tracking
- **Open TutorAI CE** — 教材 RAG 完整流程
  - PDF / 講義 / 作業上傳 → 向量化 → 對話引用

### 智慧出題（Phase 2-4）
- **DeepTutor** — 從教材抽取概念再生成測驗題
- **OATutor** — Adaptive problem selection（選 mastery probability 最低的技能出題）
- **EduAdapt-AI** — Adaptive quiz difficulty scaling 實作

### 學習路徑生成（Phase 3-1）
- **EduAdapt-AI** — Reinforcement learning-based learning path optimization
  - Content graph（概念關係圖）資料結構
  - 可參考其 RL policy 設計，對照我們的拓撲排序 + 弱項補強方案

### 教師 Dashboard（Phase 4）
- **Open TutorAI CE** — 多角色 dashboard UI（學生 / 教師 / 家長）

## 學術資源

| 資源 | 說明 |
|------|------|
| [awesome-ai-llm4education](https://github.com/GeminiLight/awesome-ai-llm4education) | AI/LLM for education 論文清單（179 stars，持續更新） |
| [SocraticLM (OpenReview)](https://openreview.net/forum?id=qkoZgJhxsA) | Dean-Teacher-Student 多 agent Socratic 教學，超越 GPT-4 12% |
| [OATutor LLM hint 論文](https://doi.org/10.1371/journal.pone.0304013) | ChatGPT hints 與人工 hints 效果相當的實證研究 |
| [JetBrains AI Hints 研究](https://blog.jetbrains.com/research/2025/07/ai-hints-for-online-learning/) | 學生使用 AI hints 的行為分析數據 |
| [Autograder+ (arXiv:2510.26402)](https://arxiv.org/abs/2510.26402) | LLM 生成教學性 feedback 的 fine-tuning 方法 |
