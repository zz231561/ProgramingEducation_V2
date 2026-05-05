"""Predict-Output prompt 模板（roadmap 2-6c）。

獨立檔避免 predict_output.py 超過 250 行硬性限制。純字串組合，無外部副作用。
"""

import json

from models.quiz import Question


def build_generate_prompt(question: Question, student_code: str) -> str:
    """LLM 看 (題目 + 學生程式碼) → 出新測資 + 對應預期輸出。

    強調：
    - 必須是 **未在 test_cases 中出現過** 的新測資（避免學生背答案）
    - expected 是「對學生實際提交的程式碼」的輸出（不是題目正解的輸出）
    """
    content = question.content or {}
    stem = content.get("stem", "")
    existing_cases = content.get("test_cases", [])
    return f"""\
你是 C++ 學習教練。學生剛交了一段程式碼，現在你要出一個新測資，請學生「預測」程式對該測資的輸出，
以驗證他是否真正理解自己寫的程式（不是亂試到對）。

題幹：{stem}
涉及概念：{question.concept_tags}
已有測資（不可重複）：{json.dumps(existing_cases, ensure_ascii=False)}

學生提交的程式碼：
```cpp
{student_code}
```

請出 1 筆新測資，並計算「對學生這份程式碼」的預期輸出（注意：是學生的程式，不是題目正解；
如果學生程式有 bug，expected 應反映這個 bug 的實際輸出）。

規則：
- input 與 existing_cases 不重複
- input 應觸發學生程式的關鍵邏輯（不是 trivial 例如 0 或空輸入）
- expected 為純文字輸出（含換行 \\n 表示）
- 若程式會無限迴圈 / 崩潰 → expected 填 "RUNTIME_ERROR"

回傳嚴格 JSON：
{{
  "input": "<新測資（多行用 \\n 串接）>",
  "expected": "<預期輸出>"
}}
"""


def build_semantic_grade_prompt(
    student_code: str,
    test_input: str,
    expected_output: str,
    student_predicted: str,
) -> str:
    """嚴格字串比對失敗時，請 LLM 判斷學生預測是否「語意一致」。

    用例：學生寫 `1, 2, 3` 而 expected 是 `1 2 3`；或 `True` vs `1`。
    """
    return f"""\
你是 C++ 學習教練。學生在預測程式輸出，請判斷他的回答是否「語意上與正確輸出一致」
（允許格式差異如逗號 vs 空白；但不可允許數值/邏輯錯誤）。

學生程式碼：
```cpp
{student_code}
```

測試輸入：{test_input!r}
正確輸出（程式實際會輸出）：{expected_output!r}
學生預測：{student_predicted!r}

判斷規則：
- 數值 / 順序 / 個數錯 → semantically_equal=false
- 僅格式差異（空白、換行、分隔符、大小寫）→ semantically_equal=true
- 語意完全不同 → false

並給 1 句中文 feedback（≤ 80 字）：點出差異原因或肯定。**不可給程式碼**。

回傳嚴格 JSON：
{{
  "semantically_equal": true / false,
  "feedback": "<1 句中文回饋>"
}}
"""
