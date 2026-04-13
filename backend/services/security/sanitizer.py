"""輸入安全防護 — Regex prompt injection 偵測 + XML 標籤隔離。

三層防護設計：
1. Regex 層：偵測已知 prompt injection 模式（中英文）
2. XML 標籤隔離：包裝使用者輸入，防止 LLM 混淆
3. System Preamble：不可覆寫規則（已在 feedback.py PREAMBLE 實作）
"""

import re

from core.errors import AppError

# === Regex 層：已知 prompt injection 模式 ===

_INJECTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    # 英文 — 角色覆寫
    (re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|rules?|prompts?)", re.I),
     "嘗試覆寫系統指令"),
    (re.compile(r"you\s+are\s+now\s+(a|an|the)\s+", re.I),
     "嘗試重新定義角色"),
    (re.compile(r"(pretend|act|behave)\s+(as\s+if\s+)?you('re|\s+are)\s+", re.I),
     "嘗試角色扮演注入"),
    (re.compile(r"(new|override|replace)\s+(system\s+)?(prompt|instruction|rule)", re.I),
     "嘗試替換系統 prompt"),
    (re.compile(r"disregard\s+(your|the|all)\s+(rules?|instructions?|guidelines?)", re.I),
     "嘗試忽略規則"),

    # 英文 — 資訊洩漏
    (re.compile(r"(reveal|show|display|print|output)\s+(me\s+)?(your|the)?\s*(system\s+)?(prompt|instructions?|rules?)", re.I),
     "嘗試取得系統 prompt"),
    (re.compile(r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?|rules?)", re.I),
     "嘗試查詢系統指令"),

    # 英文 — 直接要求答案
    (re.compile(r"(give|write|show|provide)\s+me\s+(the\s+)?(complete|full|entire)\s+(solution|answer|code)", re.I),
     "嘗試要求完整解答"),

    # 中文 — 角色覆寫
    (re.compile(r"忽略(之前|以上|所有|先前)(的)?(指令|規則|提示|設定)"),
     "嘗試覆寫系統指令"),
    (re.compile(r"你(現在|從現在起)是"),
     "嘗試重新定義角色"),
    (re.compile(r"(假裝|扮演|模擬)(你是|成為)"),
     "嘗試角色扮演注入"),

    # 中文 — 直接要求答案
    (re.compile(r"(給我|提供|寫出|告訴我)(完整|全部)(的)?(答案|解答|程式碼|代碼)"),
     "嘗試要求完整解答"),
]


def check_injection(text: str) -> str | None:
    """檢查文字是否包含 prompt injection 模式。

    回傳偵測到的模式描述，或 None 表示安全。
    """
    for pattern, description in _INJECTION_PATTERNS:
        if pattern.search(text):
            return description
    return None


def sanitize_input(text: str) -> str:
    """清理使用者輸入 — 偵測 injection 後拋出 422。"""
    detected = check_injection(text)
    if detected:
        raise AppError(
            422,
            "INPUT_REJECTED",
            f"輸入包含不允許的內容：{detected}",
        )
    return text.strip()


# === XML 標籤隔離 ===

def wrap_student_input(question: str) -> str:
    """用 XML 標籤包裝學生提問，防止 LLM 混淆角色。"""
    return f"<student_input>{question}</student_input>"


def wrap_student_code(code: str) -> str:
    """用 XML 標籤包裝學生程式碼。"""
    return f"<student_code>\n{code}\n</student_code>"
