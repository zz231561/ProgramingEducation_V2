"""EPL prompt 模板（roadmap 2-6b）。

獨立檔避免 epl.py 超過 250 行硬性限制。純字串組合，無外部副作用。
"""

import json

from models.quiz import Question, QuestionType, StudentAnswer


def format_student_answer(question: Question, student_answer: StudentAnswer) -> str:
    """把學生作答內容轉成人類可讀字串，供 LLM 看。題型決定格式。"""
    content = question.content or {}
    answer = student_answer.answer or {}
    stem = content.get("stem", "")
    if question.type == QuestionType.MULTIPLE_CHOICE.value:
        options = content.get("options", [])
        selected = answer.get("selected")
        if isinstance(selected, int) and 0 <= selected < len(options):
            chosen = options[selected]
        else:
            chosen = "（無）"
        return (
            f"題型：multiple_choice\n"
            f"題幹：{stem}\n"
            f"選項：{json.dumps(options, ensure_ascii=False)}\n"
            f"學生選擇：第 {selected} 項 — {chosen}\n"
            f"是否答對：{student_answer.is_correct}"
        )
    if question.type == QuestionType.FILL_BLANK.value:
        return (
            f"題型：fill_blank\n"
            f"題幹：{stem}\n"
            f"學生填的：{json.dumps(answer.get('answers', []), ensure_ascii=False)}\n"
            f"是否答對：{student_answer.is_correct}"
        )
    if question.type == QuestionType.CODING.value:
        code = answer.get("code", "")
        return (
            f"題型：coding\n"
            f"題幹：{stem}\n"
            f"學生程式碼：\n```cpp\n{code}\n```\n"
            f"是否答對：{student_answer.is_correct}"
        )
    return (
        f"題型：{question.type}\n題幹：{stem}\n"
        f"學生答案：{json.dumps(answer, ensure_ascii=False)}"
    )


def build_generate_prompt(question: Question, student_answer: StudentAnswer) -> str:
    """生成 EPL 提示題的 LLM system prompt。"""
    return f"""\
你是 C++ 學習教練。學生剛完成一題，現在要請他「用自己的話解釋」自己的解法/選擇，
以驗證是否真正理解（Self-explanation effect / EPL）。

學生作答脈絡：
{format_student_answer(question, student_answer)}
涉及概念：{question.concept_tags}
Bloom 等級：{question.bloom_level}

請出 1 個簡短中文 EPL 提示題，要求學生「用自己的話解釋」最關鍵的部分：
- 程式題 → 解釋程式做了什麼 / 為什麼這樣寫
- 選擇題 → 解釋為什麼選這個選項而非其他
- 填空題 → 解釋填的內容代表什麼意義

規則：
- 1 句中文，≤ 60 字
- 不可洩漏正確答案
- 不可給程式碼示範
- 引導學生用自己的話，不是「請複述題目」

回傳嚴格 JSON：{{"prompt": "<EPL 題目>"}}
"""


def build_grade_prompt(
    question: Question,
    student_answer: StudentAnswer,
    epl_prompt: str,
    epl_answer: str,
) -> str:
    """評分學生 EPL 回答的 LLM system prompt。"""
    return f"""\
你是 C++ 學習教練，正在評估學生對自己解法的「自我解釋」品質（EPL）。

學生原本作答：
{format_student_answer(question, student_answer)}
涉及概念：{question.concept_tags}

EPL 提示題：{epl_prompt}
學生 EPL 回答：{epl_answer!r}

請從 3 面向評分（每項 0.0–1.0；越接近 1 越好）：
A. conceptual_correctness：解釋是否正確對應到實際邏輯？誤解 / 與實際相反 → 偏低
B. specificity：是否提到具體變數 / 條件 / 步驟？「我做了一些操作」→ 偏低；
   「我用 i 從 0 跑到 n，每次比較 a[i] 與 max」→ 偏高
C. causality：是否解釋「為什麼」這樣寫？只說「我寫了 X」→ 偏低；
   「因為要逐個比較才能找最大值」→ 偏高

並給 1 句中文 feedback（≤ 100 字）：通過時點出最強面向；不通過時提示哪一面向需加強，
**不可給答案 / 程式碼**，只能引導學生再想一次。

回傳嚴格 JSON：
{{
  "conceptual_correctness": 0.0–1.0,
  "specificity": 0.0–1.0,
  "causality": 0.0–1.0,
  "feedback": "<1 句中文回饋>"
}}
"""
