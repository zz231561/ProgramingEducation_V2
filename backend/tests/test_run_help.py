"""執行問題 Coddy 主動說明測試（2026-08-05）。

重點：平台限制走固定文案**不呼叫 LLM**，學生自己的錯誤才走 LLM 引導。
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from services.run_help import detect_unavailable_header, uses_local_time
from tests.helpers import encrypt_test_token

USER = {"sub": "ce-a", "email": "ce@ex.com", "name": "A", "googleId": "g-ce-a"}
_CK = {"authjs.session-token": encrypt_test_token(USER)}

QT_ERROR = (
    "main.cpp:1:10: fatal error: QInputDialog: No such file or directory\n"
    '    1 | #include <QInputDialog>\n      |          ^~~~~~~~~~~~~~\n'
    "compilation terminated.\n"
)
SYNTAX_ERROR = (
    "main.cpp:5:15: error: expected ';' before '}' token\n    5 |   int x = 1\n"
)


@pytest.mark.parametrize(
    "output,expected",
    [
        (QT_ERROR, "QInputDialog"),
        ('fatal error: tinyfiledialogs.h: No such file or directory', "tinyfiledialogs.h"),
        # 標準標頭找不到＝環境異常，不可對學生說是平台限制
        ("fatal error: iostream: No such file or directory", None),
        ("fatal error: stdio.h: No such file or directory", None),
        (SYNTAX_ERROR, None),
        ("", None),
    ],
)
def test_detect_unavailable_header(output: str, expected: str | None):
    assert detect_unavailable_header(output) == expected


async def test_platform_limit_answers_without_llm(client: AsyncClient):
    """引用 Qt → 固定文案直說，且完全不觸發 LLM（零成本）。"""
    with patch(
        "services.run_help._generate_guidance", new_callable=AsyncMock
    ) as llm:
        resp = await client.post(
            "/chat/run-help",
            json={"code": "#include <QInputDialog>", "compile_output": QT_ERROR},
            cookies=_CK,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_mechanical"] is True
    llm.assert_not_called()

    content = body["assistant_message"]["content"]
    assert "QInputDialog" in content
    assert "cin" in content  # 指向這個環境做得到的替代方案


async def test_student_error_goes_through_llm_guidance(client: AsyncClient):
    with patch(
        "services.run_help._generate_guidance",
        new_callable=AsyncMock,
        return_value="先看第 5 行結尾少了什麼。",
    ) as llm:
        resp = await client.post(
            "/chat/run-help",
            json={"code": "int main(){int x = 1}", "compile_output": SYNTAX_ERROR},
            cookies=_CK,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_mechanical"] is False
    assert body["assistant_message"]["content"] == "先看第 5 行結尾少了什麼。"
    llm.assert_awaited_once()


async def test_message_persists_into_session_history(client: AsyncClient):
    """主動說明要留在對話歷史裡，重開對話仍看得到。"""
    with patch(
        "services.run_help._generate_guidance",
        new_callable=AsyncMock,
        return_value="引導內容",
    ):
        first = (
            await client.post(
                "/chat/run-help",
                json={"code": "x", "compile_output": SYNTAX_ERROR},
                cookies=_CK,
            )
        ).json()

    session_id = first["session_id"]
    detail = (await client.get(f"/chat/sessions/{session_id}", cookies=_CK)).json()
    assert [m["content"] for m in detail["messages"]] == ["引導內容"]
    assert detail["session"]["title"] == "執行問題引導"


async def test_llm_failure_falls_back(client: AsyncClient):
    """LLM 掛掉不可讓學生看到錯誤畫面（fail-open，與 kickoff 一致）。"""
    with patch(
        "services.run_help._get_client",
        side_effect=RuntimeError("boom"),
    ):
        resp = await client.post(
            "/chat/run-help",
            json={"code": "x", "compile_output": SYNTAX_ERROR},
            cookies=_CK,
        )
    assert resp.status_code == 200
    assert "錯誤訊息的第一行" in resp.json()["assistant_message"]["content"]


async def test_timeout_answers_without_llm(client: AsyncClient):
    """逾時沒有編譯訊息可分析 → 固定文案直說，同樣不花 LLM。"""
    with patch(
        "services.run_help._generate_guidance", new_callable=AsyncMock
    ) as llm:
        resp = await client.post(
            "/chat/run-help",
            json={
                "code": "while(1){}",
                "compile_output": "",
                "status_description": "Time Limit Exceeded",
            },
            cookies=_CK,
        )
    assert resp.status_code == 200
    llm.assert_not_called()
    content = resp.json()["assistant_message"]["content"]
    assert "迴圈" in content and "輸入" in content


@pytest.mark.parametrize(
    "code,expected",
    [
        ("time_t t=time(NULL); localtime(&t);", True),
        ("strftime(buf,80,\"%Y\",tm);", True),
        ("std::cout<<time(NULL);", False),   # 只印 epoch，不受時區影響
        ("clock();", False),                  # CPU 時間，與時區無關
        ("int main(){}", False),
    ],
)
def test_uses_local_time(code: str, expected: bool):
    assert uses_local_time(code) is expected


async def test_timezone_notice_without_llm(client: AsyncClient):
    """時區提醒是環境事實 → 固定文案，不花 LLM。"""
    with patch(
        "services.run_help._generate_guidance", new_callable=AsyncMock
    ) as llm:
        resp = await client.post(
            "/chat/run-help",
            json={"code": "localtime(&t);", "kind": "timezone"},
            cookies=_CK,
        )
    assert resp.status_code == 200
    llm.assert_not_called()
    content = resp.json()["assistant_message"]["content"]
    assert "UTC" in content and "8 小時" in content


async def test_nzec_notice_separates_three_sources(client: AsyncClient):
    """NZEC 說明必須分清 C++ 標準 / OS 慣例 / 本平台判定，且零 LLM（7-C2b）。

    修的問題：由 LLM 即興解釋時會講成「線上評測通常…」——第三人稱迴避，
    而且把標準與慣例混為一談。規範來源是固定事實，該用固定文案。
    """
    with patch(
        "services.run_help._generate_guidance", new_callable=AsyncMock
    ) as llm:
        resp = await client.post(
            "/chat/run-help",
            json={"code": "int main(){return 1;}", "kind": "nzec"},
            cookies=_CK,
        )
    assert resp.status_code == 200
    llm.assert_not_called()
    assert resp.json()["is_mechanical"] is True
    content = resp.json()["assistant_message"]["content"]
    assert "C++ 標準" in content
    assert "作業系統慣例" in content
    assert "這個平台的判定" in content
    # 第一人稱交代本平台的行為，不用「通常」把來源含糊帶過
    assert "我沿用" in content
    assert "通常" not in content


def test_timeout_template_does_not_reference_removed_input_field():
    """R5d 移除了 Output 上方的「輸入」欄位；文案不可再叫學生去填它。"""
    from services.run_help import _TIMEOUT_TEMPLATE

    assert "「輸入」" not in _TIMEOUT_TEMPLATE
    assert "終端機" in _TIMEOUT_TEMPLATE  # 改成互動終端的實際操作方式
