---
description: EDF 教學管線規範 — Evidence/Decision/Feedback 三層架構與 ConceptTag
globs: backend/services/edf/**
---

# EDF 教學管線規範

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
