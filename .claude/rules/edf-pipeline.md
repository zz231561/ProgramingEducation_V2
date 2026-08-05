---
description: EDF 教學管線規範 — Evidence/Decision/Feedback 三層架構與 ConceptTag
globs: backend/services/edf/**
---

# EDF 教學管線規範

## 開源參考
- OATutor：BKT → hint selection → feedback 流程，最接近 EDF 設計（詳見 `docs/references.md`）
- Mr. Ranedeer：Socratic prompt template 設計
- BloomBERT：Bloom taxonomy 自動分類驗證

## Evidence → Decision → Feedback 三層管線

### Evidence（程式碼分析）
- LLM 結構化輸出：錯誤分類、ConceptTag、Bloom 認知等級
- 注入 Judge0 執行結果（stdout/stderr）作為分析脈絡
- 注入 Pre-Coding Reflection 內容（若有）：學生的解題計畫 + 反思品質分數

### Decision（教學策略）
- Bloom × Hint Ladder 6×6 策略矩陣（保留 V1 設計）— **7-C2a 將改為 6 等級指令 + 6 Bloom 修飾**
- `decide_strategy()` **全專案只有 `services/chat.py` 呼叫**（Quiz 走獨立的 `services/quiz/hint.py`），
  改動此層不影響 Quiz
- ~~RAG 觸發條件：hint/bloom 門檻~~ → **K4b（2026-07-04）改為內容相關性**：Feedback 層每次互動都檢索，只注入 cosine 分數 >= `RAG_MIN_SCORE`（0.40 初始值，K4d 驗收調整）的 chunks

### Feedback（回應生成）
- 分層 prompt 組裝：preamble → persona → strategy → context → **kgraph** → reflection → RAG
- **K-Graph 鷹架（K4a）**：`kgraph_context.py` 依學生最弱相關概念的 confidence 分級——<0.4 框架填空/逐行拆解、0.4-0.7 引導式提問、>0.7 只點 edge case
- AI 可引用學生的反思計畫（如「你前面說要用迴圈處理，可以更具體嗎？」）
- Persona = Coddy（K4a 語氣修訂）：先肯定再引導、提問具體到程式碼、小事直接回答不硬展開教學；RULE-5 允許以行動建議收尾（不強制反問）
- 輸出驗證：阻擋完整程式碼洩漏，保持教學引導

## Bloom 認知等級（6 級）

| Level | 名稱 | 教學行為 |
|-------|------|---------|
| 1 | REMEMBER | 回憶定義/語法，直接提問「什麼是 X？」 |
| 2 | UNDERSTAND | 解釋概念含義，用自己的話複述 |
| 3 | APPLY | 在新情境中使用已知概念解題 |
| 4 | ANALYZE | 拆解問題結構，辨識模式與關係 |
| 5 | EVALUATE | 比較不同解法的優劣，判斷正確性 |
| 6 | CREATE | 設計新方案，綜合多個概念解決複雜問題 |

## Hint Ladder（6 級，0-5）

> ⚠ **2026-08-06：本節描述的是「現行實作」，已定案將於 7-C2a 改版**（累積式階梯 + 動態選層，
> 規格見 `docs/roadmap.md` 7-C2a 與「已確認決策」末條）。**動 `services/edf/decision.py` 前先讀那份規格**。

**現行（改版前）：**

| Level | 策略 | 範例 |
|-------|------|------|
| 0 | 只問問題，不給任何提示 | 「你覺得第 6 行會發生什麼？」 |
| 1 | 指出錯誤方向，不指出具體位置 | 「問題和記憶體有關，再看看」 |
| 2 | 指出具體位置 + 概念名稱 | 「第 6 行對 nullptr 解引用」 |
| 3 | 給出部分程式碼框架（含 TODO） | 「試試：`if (p != ???) { ... }`」 |
| 4 | 逐步引導，只差最後一步 | 「加上 null check 後，else 要做什麼？」 |
| 5 | 完整解釋 + 修正後程式碼片段 | ⚠ 見下方矛盾說明 |

**策略矩陣：** Decision 層根據 `(bloom_level, hint_level)` 查表（6×6＝36 格）決定回應策略。
低 Bloom + 低 Hint → 直接提問；高 Bloom + 高 Hint → 給框架引導但不給完整答案。

### ⚠ 已知矛盾（7-C2a 將消除）

1. **L5 措辭與 RULE-1 打架**：上表與 `decision.py` 的 (3,5)/(6,5) 寫「展示完整的應用方式/設計方案」，
   但 PREAMBLE RULE-1 是「絕對不要提供完整的解答程式碼」且標為不可違反。
   **實際行為以 RULE-1 為準**——`validate_output` 即使 `allow_code=True` 仍截斷 >8 行且無 TODO 的區塊，
   且 `services/quiz/hint.py` 的同級說明早已正確寫成「不可直接給完整答案」。**離群值是本表與 `decision.py`**。
   **原則**：RULE-1／RULE-2 是階梯之上的不變量，任何等級都不得突破；
   L5 的「完整」指**解釋**完整、非**程式碼**完整。
2. **「反覆失敗 5+ 次後觸發」從未被實作**（無任何程式碼強制此門檻）——7-C2a persistence 搬後端後才可能落實。
3. **兩條階梯語意不同不可混用**：chat 的等級是**系統依需求與堅持程度推論**的；
   Quiz `hint.py` 的 1–5 是**學生實際按了 N 次提示鈕**。共用欄位名但不是同一件事。

## ConceptTag（20 個，保留 V1 定義）

```
syntax-basic, io-streams, control-flow, function-design, arrays-strings,
pointer-arithmetic, memory-management, references, oop-encapsulation,
oop-inheritance, oop-polymorphism, stl-containers, stl-algorithms,
template-meta, recursion, error-handling, undefined-behavior,
algorithm-complexity, concurrency, namespaces
```

## 出題流程（4 階段）

1. **Select** — student_mastery 中 confidence < 0.4 的弱項 + 知識圖譜相關概念
2. **Generate** — LLM 根據概念 + 難度 + 題型生成，注入 RAG 教材片段
3. **Validate** — LLM 自我檢查答案正確性 + 確認不超出目標 Bloom 等級
4. **Present** — 前端渲染，作答後觸發 EDF Pipeline 教學引導
