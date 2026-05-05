"""Variation prompt 模板（roadmap 2-6d）。

獨立檔避免 variation.py 超過 250 行硬性限制。純字串組合，無外部副作用。

理論基礎：Variation Theory (Marton)
- 同核心概念，變更非本質特徵（情境 / 變數名 / 數值 / 邏輯方向）
- 學生能在新情境正確應用 → 確認真懂；只能解原題 → 死記
"""

import json

from models.quiz import Question


def build_generate_prompt(question: Question, student_code: str) -> str:
    """LLM 產生「同概念、不同情境」的變體題（含新題幹 / starter / test_cases）。"""
    content = question.content or {}
    stem = content.get("stem", "")
    return f"""\
你是 C++ 學習教練。學生剛完成一題，現在要出一個「變體題」驗證他真的理解概念
（Variation Theory — 同概念、不同情境）。

原題：
{stem}
涉及概念：{question.concept_tags}
學生原解法（程式碼）：
```cpp
{student_code}
```

請出 1 個變體題，符合：
- 核心概念與原題相同（不可換概念）
- 情境 / 變數名 / 數值 / 條件方向 至少改動一項（例：找最大 → 找最小；正整數 → 含負數；
  順序輸出 → 反向輸出）
- 難度近似原題，不可大幅變難
- 必須是 coding 題（變體只支援 coding 題型）
- starter_code 提供函式簽章 / I/O 框架，留學生實作核心邏輯
- 至少 2 筆 test_cases（涵蓋一般情況 + 邊界）

回傳嚴格 JSON：
{{
  "stem": "<新題幹（中文，含目標、I/O 規格、邊界條件）>",
  "starter_code": "<C++ 起始碼（含 I/O 處理 + 待填邏輯位置）>",
  "test_cases": [
    {{"input": "<stdin>", "expected": "<stdout>"}},
    {{"input": "<stdin>", "expected": "<stdout>"}}
  ],
  "concept_focus": "<1 句中文，說明這個變體驗證學生對哪個面向的理解>"
}}
"""


def build_grade_prompt(
    variation_stem: str,
    test_cases: list[dict],
    concept_focus: str,
    student_code: str,
) -> str:
    """LLM 判斷學生 code 是否解了該變體題（binary pass/fail + feedback）。"""
    return f"""\
你是 C++ 學習教練，正在評估學生對「變體題」的解答品質。

變體題目：
{variation_stem}

驗證重點：{concept_focus}
測試案例（可作為心智模擬參考）：
{json.dumps(test_cases, ensure_ascii=False, indent=2)}

學生提交的程式碼：
```cpp
{student_code}
```

請判斷：
- passed=true 條件：學生程式對所有 test_cases 都會輸出正確結果（在你心智模擬執行下），
  且核心邏輯符合 concept_focus 描述的能力
- passed=false 條件：邏輯錯誤 / 編譯錯誤 / 死迴圈 / 只硬編碼原題答案 / 任一 test_case 失敗

並給 1 句中文 feedback（≤ 100 字）：
- passed → 點出最關鍵的正確之處
- failed → 提示哪個 test_case / 哪段邏輯出問題
- **不可給程式碼示範 / 完整解答**

回傳嚴格 JSON：
{{
  "passed": true / false,
  "feedback": "<1 句中文回饋>"
}}
"""
