"""Feedback 層 — `validate_output` 單元測試（阻擋完整程式碼洩漏）。"""

from services.edf.feedback import validate_output


def test_validate_removes_code_when_not_allowed():
    text = "看看這個：\n```cpp\nint x = 1;\n```\n試試看"
    result = validate_output(text, allow_code=False)
    assert "int x" not in result
    assert "已移除" in result


def test_validate_keeps_short_code():
    text = "提示：\n```cpp\nif (p != nullptr) {\n    // TODO: 處理 p\n}\n```"
    result = validate_output(text, allow_code=True)
    assert "TODO" in result
    assert result == text


def test_validate_truncates_long_code_without_guard():
    lines = "\n".join([f"int x{i} = {i};" for i in range(12)])
    text = f"看這個：\n```cpp\n{lines}\n```"
    result = validate_output(text, allow_code=True)
    assert "請自己完成" in result
    assert "int x11" not in result


def test_validate_keeps_long_code_with_todo():
    lines = "\n".join([f"int x{i} = {i};" for i in range(12)])
    lines += "\n// TODO: 補上回傳值"
    text = f"框架：\n```cpp\n{lines}\n```"
    result = validate_output(text, allow_code=True)
    assert "TODO" in result
    assert result == text


def test_validate_no_code_blocks():
    text = "你覺得第 6 行會發生什麼？試著追蹤變數 x 的值。"
    result = validate_output(text, allow_code=True)
    assert result == text
