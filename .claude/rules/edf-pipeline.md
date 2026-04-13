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

### Decision（教學策略）
- Bloom × Hint Ladder 6×6 策略矩陣（保留 V1 設計）
- RAG 觸發條件：hint_level >= 2 且 bloom_level 屬於 {ANALYZE, EVALUATE, CREATE}

### Feedback（回應生成）
- 分層 prompt 組裝：preamble → persona → strategy → context → RAG
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

| Level | 策略 | 範例 |
|-------|------|------|
| 0 | 只問問題，不給任何提示 | 「你覺得第 6 行會發生什麼？」 |
| 1 | 指出錯誤方向，不指出具體位置 | 「問題和記憶體有關，再看看」 |
| 2 | 指出具體位置 + 概念名稱 | 「第 6 行對 nullptr 解引用」 |
| 3 | 給出部分程式碼框架（含 TODO） | 「試試：`if (p != ???) { ... }`」 |
| 4 | 逐步引導，只差最後一步 | 「加上 null check 後，else 要做什麼？」 |
| 5 | 完整解釋 + 修正後程式碼片段 | 僅在反覆失敗 5+ 次後觸發 |

**策略矩陣：** Decision 層根據 `(bloom_level, hint_level)` 查表決定回應策略。
低 Bloom + 低 Hint → 直接提問；高 Bloom + 高 Hint → 給框架引導但不給完整答案。

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
