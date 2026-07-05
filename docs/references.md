# 開源參考專案

> **強制守則**：開發新功能前**必先檢視本文件 §1 決策矩陣**，確認是否有可直接 `pip/npm install` 的成熟套件或可採用的 schema。違反「避免重複造輪子」原則的設計將被拒絕（CLAUDE.md 執行守則 #7）。

---

## 1. OSS 重用決策矩陣

### ✅ Tier 1：立即依賴（pip/npm install，最高 ROI）

| 套件 | License | 對應 Phase | 用法 |
|------|---------|-----------|------|
| **pyBKT** | MIT | 2-3 精熟度追蹤、5-3 行為分析 | `pip install pyBKT`，scikit-learn 風格 API。**取代 OATutor BKT-brain.js 移植**，省 1-2 天 |
| **LlamaIndex** | MIT | 2-1 RAG 索引管線 | 已鎖定技術棧。直接用 `PGVectorStore` + `IngestionPipeline`，**禁止自寫 chunking/embedding 流程** |
| **Cytoscape.js** + `cytoscape-fcose` | MIT | 2-2 知識圖譜渲染 | force-directed layout 一行設定，**禁止用 D3 從頭刻** |
| **Vercel AI SDK (`ai`)** | Apache-2.0 | 1-5 Chat 串流（如需重構）| `useChat` hook + SSE backend helper，省手刻 streaming parsing |
| **`prefixspan`** | MIT | 5-3 行為流程分析 | Sequential pattern mining。**取代 AGPL 的 PM4Py**（見 Tier 4） |
| **shadcn/ui + Radix UI** | MIT | 全站元件 | 已採用 |
| **CodeMirror 6** | MIT | 編輯器 | 已採用 |
| **react-resizable-panels** | MIT | Workspace 拖曳 | 已採用 |
| **NextAuth.js (Auth.js)** | ISC | Auth | 已採用 |

### ✅ Tier 2：Schema 直接採用（抄欄位定義，零依賴）

| Schema 來源 | License | 用法 |
|------------|---------|------|
| **ProgSnap2** EventType / SubjectID 五欄主鍵 | CC-BY-4.0 | 直接套用至 `coding_events` 表（5-2a）。未來可與學界資料集互通 |
| **StudyChat** dialogue act 階層分類（asking_hint / clarification_request / debugging / off_topic / acknowledgment / verification 等）| CC-BY-4.0 | 直接套用至 `chat_messages.dialogue_act` 欄位（5-2c），16,851 筆標註可作未來分類器訓練語料 |
| **OATutor** Hint Ladder 6 階（0-5） | MIT | 已採用於 EDF Decision 層 |

### ⚠ Tier 3：Clone 研讀後移植（無對應套件，需手寫實作）

| 來源 | License | 對應 | 借鑑深度 |
|------|---------|------|---------|
| **DeepTutor** | Apache-2.0 | 2-1c 檢索 service | 讀 `agents/` 與 `tools/` 的 hybrid retrieval（dense + BM25 reranking）+ citation tracking 模式。**本身是完整 app 不是 lib** |
| **Mr. Ranedeer** | License 未明示 | 1-4c Feedback prompt | 已用於 1-4c。僅汲取 prompt 設計思路，**不複製文字內容**（避免授權糾紛） |
| **JetBrains Edu Plugin** | Apache-2.0 | 2-4 出題流程 | 讀 `taskDescription` 模板設計 |

### ❌ Tier 4：不採用（授權風險或過度工程）

| 來源 | 不採用原因 | 替代方案 |
|------|-----------|---------|
| **PM4Py** | ❌ AGPL-3.0：網路服務觸發第 13 條，要求公開後端整體源碼，**與閉源商業化衝突** | Tier 1 的 `prefixspan`（MIT）+ 自刻簡化版 process flow 統計 |
| **OATutor `BKT-brain.js`** port | 已有 pyBKT 套件且更穩定 | Tier 1 直接用 pyBKT |
| **EduAdapt-AI RL learning path** | RL 對 MVP 過度工程 | Phase 3-1 先用拓撲排序 + 弱項補強，後期再評估 |
| **BloomBERT** | LLM 結構化輸出已足夠，引入額外模型增加維運成本 | 保留交叉驗證可能，Phase 1 不引入 |
| **Socratic-LLM** fine-tune | 不做 fine-tuning（用 GPT-4o + prompt engineering）| — |

### 📌 決策記錄：K5a 知識圖譜視覺化套件（2026-07-05）

**結論：維持 Cytoscape.js + cytoscape-fcose，不遷移。**

| 候選 | 評估 | 判定 |
|------|------|------|
| **Cytoscape.js**（現用） | MIT；graph-theory 導向，原生支援 compound node（分章 cluster 直接用 parent node 表達）；fcose 為 CoSE 系最新最快版，唯一同時支援 compound + placement constraint 的 force-directed layout；現有整合約 600 行 | ✅ 維持 |
| **React Flow (@xyflow)** | MIT；定位是 workflow/node-editor（HTML 自訂節點強），但 layout 需外掛（dagre/elk）、cluster/combo 支援弱、大圖分析非其目標場景；遷移需重寫全部 graph 程式碼，無決定性優勢 | ❌ 不遷移 |
| **D3 手刻** | 一切自建（layout/互動/hover），本文件 §1 Tier 1 已明令「禁止用 D3 從頭刻」 | ❌ 禁用 |

**Layout 評估（K5b 分章 cluster）**：
- **fcose** ✅ — 支援 compound node + constraint，force-directed 適合非嚴格層級的 90 條多對多 PREREQUISITE 邊
- dagre ❌ — 純 hierarchical DAG 排版，**不支援 compound node**，無法做分章 cluster
- klay/elk ❌ — layered 排版支援 compound 但整體視覺偏工程流程圖，與 Obsidian 風小圓點定位不符，且需新增依賴

**依據**：[Cytoscape.js 2023 paper (Oxford Bioinformatics/PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9889963/)、[cytoscape.js-dagre README（DAGs and trees 定位）](https://github.com/cytoscape/cytoscape.js-dagre)、[Cytoscape.js layouts 官方 blog（fcose = latest and greatest CoSE）](https://blog.js.cytoscape.org/2020/05/11/layouts/)、React Flow 官方 discussion（layout 需自接外部演算法）。

---

## 2. 授權白名單／黑名單

| License | 使用條件 | 範例 |
|---------|---------|------|
| **MIT / Apache-2.0 / BSD-3 / ISC** | ✅ 直接採用 | pyBKT, LlamaIndex, Cytoscape.js |
| **CC-BY-4.0**（資料/規格）| ✅ 採用，註明出處 | ProgSnap2, StudyChat schema |
| **LGPL** | ⚠ 動態連結可，靜態連結需評估 | 個案處理 |
| **AGPL-3.0** | ❌ **嚴禁**：網路服務觸發第 13 條，需公開整體源碼 | PM4Py |
| **GPL-3.0** | ❌ **嚴禁**：傳染性，會強制本專案開源 | — |
| **未明示 license** | ⚠ 僅可汲取設計思路，**禁止複製程式碼或文案** | Mr. Ranedeer (prompt 思路 OK，文字禁複製) |
| **Custom / 商用限制** | ❌ 禁用 | — |

> **檢查清單**（每次新增 dependency 前）：
> 1. 套件 GitHub 的 LICENSE 檔內容（不要只看 README 標示）
> 2. `package.json` / `pyproject.toml` 的 `license` 欄位
> 3. 若是 fork，需追溯到原始上游 license

---

## 3. 各 Phase 快速查表

| Phase | 必用 OSS（Tier 1）| 採用 Schema（Tier 2）|
|-------|------------------|---------------------|
| **Phase 2-1 RAG** | LlamaIndex（PGVectorStore）| — |
| **Phase 2-2 知識圖譜** | Cytoscape.js + fcose | — |
| **Phase 2-3 精熟度** | **pyBKT** | — |
| **Phase 2-4 智慧出題** | LlamaIndex（教材檢索）| — |
| **Phase 2-5 Pre-Coding Reflection** | （無，純後端 + UI）| — |
| **Phase 2-6 Comprehension Check** | （無，純 LLM prompt）| — |
| **Phase 3-1 學習路徑** | （拓撲排序，不引 RL）| — |
| **Phase 4 部署** | Zeabur 官方模板 + `pgvector/pgvector:pg16` + Judge0 docker-compose | — |
| **Phase 5-2 行為事件** | （無）| ProgSnap2 + StudyChat |
| **Phase 5-3 行為分析** | pyBKT + `prefixspan` | — |

---

## 4. 專案總覽

| 專案 | Stars | License | 主要參考價值 | 對應 Phase |
|------|-------|---------|-------------|-----------|
| [DeepTutor](https://github.com/HKUDS/DeepTutor) | 17k+ | Apache-2.0 | RAG hybrid retrieval + Knowledge Graph | Phase 2-1 |
| [OATutor](https://github.com/CAHLR/OATutor) | 190 | MIT | BKT 演算法（已被 pyBKT 取代）+ Hint pathway | Phase 2-3, 1-4 |
| [Mr. Ranedeer](https://github.com/JushBJJ/Mr.-Ranedeer-AI-Tutor) | 29k+ | 未明示 | Socratic prompt 思路（不複製文字） | Phase 1-4 |
| [EduAdapt-AI](https://github.com/mwasifanwar/eduadapt-ai) | 10 | 未明示 | ❌ Tier 4：RL 過重，僅讀架構 | Phase 3-1 |
| [BloomBERT](https://github.com/RyanLauQF/BloomBERT) | 36 | MIT | ❌ Tier 4：LLM 已足夠 | — |
| [Socratic-LLM](https://github.com/GiovanniGatti/socratic-llm) | 31 | MIT | ❌ Tier 4：不做 fine-tune | — |
| [Open TutorAI CE](https://github.com/Open-TutorAi/open-tutor-ai-CE) | 48 | BSD-3 | 多角色 dashboard UI | Phase 5-1 |
| [JetBrains Edu Plugin](https://github.com/JetBrains/educational-plugin) | 174 | Apache-2.0 | 漸進式 hint generation | Phase 1-4 |
| [pyBKT](https://github.com/CAHLR/pyBKT) | 250 | MIT | ✅ Tier 1：BKT Python 套件 | Phase 2-3, 5-3 |
| [prefixspan-py](https://github.com/chuanconggao/PrefixSpan-py) | 400+ | MIT | ✅ Tier 1：sequential pattern mining，取代 PM4Py | Phase 5-3 |
| [ProgSnap2](https://github.com/CSSPLICE/progsnap2) | 5 | CC-BY-4.0 | ✅ Tier 2：事件 schema 規格 | Phase 5-2 |
| [KOALA](https://github.com/JetBrains-Research/KOALA) | 10 | MIT | ProgSnap2 輸出實作參考 | Phase 5-2 |
| [StudyChat](https://huggingface.co/datasets/wmcnicho/StudyChat) | — | CC-BY-4.0 | ✅ Tier 2：dialogue act schema | Phase 5-2 |
| ~~[PM4Py](https://github.com/process-intelligence-solutions/pm4py)~~ | 941 | ❌ AGPL-3.0 | **不採用**，改用 prefixspan | — |

---

## 5. 學術資源（讀論文，不複製程式碼）

| 資源 | 說明 |
|------|------|
| [awesome-ai-llm4education](https://github.com/GeminiLight/awesome-ai-llm4education) | AI/LLM for education 論文清單（179 stars，持續更新）|
| [SocraticLM (OpenReview)](https://openreview.net/forum?id=qkoZgJhxsA) | Dean-Teacher-Student 多 agent，超越 GPT-4 12% |
| [OATutor LLM hint 論文](https://doi.org/10.1371/journal.pone.0304013) | ChatGPT hints 與人工 hints 效果相當的實證研究 |
| [JetBrains AI Hints 研究](https://blog.jetbrains.com/research/2025/07/ai-hints-for-online-learning/) | 學生使用 AI hints 的行為分析數據 |
| [Autograder+ (arXiv:2510.26402)](https://arxiv.org/abs/2510.26402) | LLM 生成教學性 feedback 的 fine-tuning 方法 |
| [StudyChat (arXiv:2503.07928)](https://arxiv.org/abs/2503.07928) | dialogue act 分類 schema 論文 |
| [ProgSnap2 (ITiCSE 2020)](https://dl.acm.org/doi/10.1145/3341525.3387373) | 程式教育 process data 標準格式 |
| [pyBKT (EDM 2021)](https://arxiv.org/abs/2105.00385) | Bayesian Knowledge Tracing Python 函式庫 |
| [CodeWatcher (ICSME 2025)](https://arxiv.org/abs/2510.11536) | IDE telemetry 追蹤 LLM 互動 |
| Self-explanation effect (Chi et al., 1989; Bisra et al. 2018 meta-analysis) | 自我解釋效果 d=0.55 |
| CodeAid (Kazemitabaar et al., 2023-24) | 不給直接程式碼的 AI tutor 學習效果顯著更好 |
| Automation complacency (Prather et al., ICER 2023) | Copilot 造成「能力幻覺」 |
| EPL questions (Fowler et al., 2021-24) | 自然語言解釋程式碼，與考試成績相關性高 |
| PRIMM (Sentance & Waite, 2017) | Predict-Run-Investigate-Modify-Make 五階段 |
| Desirable difficulties (Bjork & Bjork, 1994-2020) | 策略性摩擦提升長期記憶 |

### 5.1 K6 熟練度演算法關鍵文獻（📌 論文引用標注，2026-07-06）

> K6a / K6b / K6c 與 U2b 的實作理論依據。論文撰寫時直接引用本清單。

| 主題 | 文獻 | 在本系統的對應 |
|------|------|----------------|
| BKT 基礎 | Corbett & Anderson (1995), *Knowledge tracing: Modeling the acquisition of procedural knowledge*, UMUAI | `services/mastery/updater.py` Bayes 線上更新；[pyBKT (EDM 2021)](https://arxiv.org/abs/2105.00385) 為參數擬合工具 |
| BKT + 遺忘 | Khajah, Lindsey & Mozer (2016), *How Deep is Knowledge Tracing?*, EDM — BKT 加 forgetting 可匹敵 DKT；[KT Survey (arXiv:2105.15106)](https://arxiv.org/pdf/2105.15106) §forgetting 綜述 | K6b 衰減設計依據；pyBKT 原生支援 `forgets=True` |
| 遺忘曲線 | Ebbinghaus (1885/1913) 指數衰減；[個人化遺忘機制 (arXiv:2404.12127)](https://arxiv.org/pdf/2404.12127) | K6b `exp(−λ × days)` 函式形 |
| 記憶穩定度 | [FSRS 演算法](https://github.com/open-spaced-repetition/free-spaced-repetition-scheduler)（MIT；Anki 已採用）— 穩定度隨成功複習成長 → 半衰期變長 | K6b 半衰期隨 success_count 成長 |
| 間隔重複 | Settles & Meeker (2016), *A Trainable Spaced Repetition Model for Language Learning*（Duolingo HLR）, ACL | K6b 半衰期參數化思路；衰減 framing＝複習提示（cracked skill / due for review） |
| 證據通道雜訊 | BKT slip/guess 語意（Corbett & Anderson 1995；Baker, Corbett & Aleven 2008 contextual guess/slip） | K6a 弱證據＝高 guess / 低 learn，留在 BKT 數學框架內、不外掛權重係數 |
| Open Learner Model | Bull & Kay (2007/2016) SMILI 框架；[OLM 與 SRL 系統性回顧 (Computers & Education, 2020)](https://www.sciencedirect.com/science/article/abs/pii/S0360131520300774)；[OLM 知識監控實證 (RPTEL 2020)](https://telrp.springeropen.com/articles/10.1186/s41039-020-00137-5) | K6c 事件級透明化、不給逐筆帳本（避免分數導向 / gaming / 損失厭惡） |
| 生成式學習 | Fiorella & Mayer (2015), *Learning as a Generative Activity* — 自我生成摘要 > 提供現成摘要；Sweller 冗餘效應（CLT） | U2b 移除 LEARN 摘要 tab 的依據 |

---

## 6. 功能對照（細節參考）

### EDF 教學管線（Phase 1-4 已完成）
- **Bloom 分類**：BloomBERT 可作為 LLM 輸出交叉驗證（Tier 4 不引入）
- **Hint Ladder**：採用 OATutor 6 階設計（Tier 2）
- **Prompt 設計**：Mr. Ranedeer 思路（Tier 3）

### 精熟度追蹤（Phase 2-3）
- **直接 `pip install pyBKT`**，scikit-learn API
- 整合點：EDF Evidence 結果 → BKT update → `student_mastery.confidence`

### RAG 檢索（Phase 2-1）
- LlamaIndex 內建 `PGVectorStore` + `IngestionPipeline`
- 參考 DeepTutor hybrid retrieval（dense + BM25 reranking）模式

### 學習路徑（Phase 3-1）
- **不採用 EduAdapt-AI 的 RL 方案**
- MVP 用拓撲排序 + 弱項補強

### 行為分析（Phase 5）
- 事件 schema：ProgSnap2（Tier 2）
- Dialogue act：StudyChat（Tier 2）
- Knowledge tracing：pyBKT（Tier 1）
- Process mining：prefixspan（Tier 1，取代 PM4Py）
