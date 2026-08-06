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
- 7-C2a'：另輸出 `comprehension_signal`（understood/not_understood/unclear）與
  `continues_previous_issue` 供 Decision 的 need 狀態機——**搭在既有那次呼叫上，零額外請求**
  （同 `is_on_topic` 的作法）。需注入上一輪問答摘要才判得出來
- 注入 Judge0 執行結果（stdout/stderr）作為分析脈絡
- 注入 Pre-Coding Reflection 內容（若有）：學生的解題計畫 + 反思品質分數

### Decision（教學策略）
- **累積式揭露階梯 6 級 + Bloom 深度修飾 6 條**（7-C2a，2026-08-06 取代 6×6＝36 格矩陣）
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

## 揭露階梯 reveal_level（6 級 0-5，累積式；7-C2a 2026-08-06 改版）

單調的維度是「**本題解法被揭露多少**」，不是「講了多少話」——每級都在前一級之上**多揭露一點**，
因此指令累積生效（L3 同時含 L0-L2 的行為）。

| Level | 本級額外揭露 | 允許程式碼 |
|-------|------------|-----------|
| 0 | 回答學生實際問的問題、解釋所需概念，可舉與本題無關的例子；本題解法揭露 0% | ✗ |
| 1 | ＋指出問題落在哪個區域／哪個概念 | ✗ |
| 2 | ＋精確位置（行號）＋為什麼錯 | ✗ |
| 3 | ＋解法骨架，TODO 必須真留白 | ✓ |
| 4 | ＋逐步帶到只剩最後一步 | ✓ |
| 5 | ＋逐行完整解釋、修正後**片段** | ✓ |

**動態選層：** `reveal_level = min(5, base(error_type) + need)`
- `base`：none → 0（純提問／程式正確）；syntax・compilation・runtime → 2（學生看不懂錯誤訊息，
  指出位置不算給答案）；logic・semantic → 1（找出邏輯錯在哪本身就是練習，直接指位置等於代寫）
- `need`（`services/chat_signals.py`，**後端從對話歷史自算**）＝估計「學生離自己解出來還差多少」，
  **不是追問次數**——7-C2a' 實測證實計數會讓索答施壓一路爬級（堅持不等於值得）：

  | 訊號 | delta | 來源 |
  |---|---|---|
  | 學生展現理解（understood） | −1 | Evidence `comprehension_signal` |
  | 學生表示沒理解（not_understood） | +1 | 同上 |
  | 改了程式又跑失敗 | +1 | `code_snapshot` 差異 + 執行結果 |
  | 顯式求助（按鈕，尚未實作） | +2 | 前端 |
  | **單純追問／索答施壓** | **0** | comprehension = unclear |

  歸零三途：程式跑成功（事實）／換卡點 `continues_previous_issue=False`（LLM 保守二元判定）／
  閒置超過 30 分鐘（純時間）。前端不再送 `hint_level`——送得出來的數字就可能被寫死成 0

**Bloom 修飾**與等級正交：等級管揭露多少，Bloom 管講多深（`_BLOOM_DEPTH` 6 條，
REMEMBER 直接給定義 → CREATE 給可選設計方向）。Feedback 層組裝「累積指令 ＋ 深度修飾」。

### 不變量（高於階梯，任何等級不得突破）

1. **RULE-1／RULE-2 凌駕階梯**：L5 的「完整」指**解釋**完整、非**程式碼**完整。
   機械防線＝`validate_output` 即使 `allow_code=True` 仍截斷 >8 行且無 TODO 的區塊。
2. **兩條階梯語意不同不可混用**：chat 的 `reveal_level` 是**系統依錯誤類型與堅持程度推論**的；
   Quiz `hint.py` 的 `hint_level` 1–5 是**學生實際按了 N 次提示鈕**（維持原樣，不受本節影響）。

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
