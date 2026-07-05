"""開發者 quiz 工具測試（DEV-7/8/9）— debug sink、診斷模擬、題庫檢視。"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from core.config import settings
from models.concept import Concept
from models.quiz import Question, StudentAnswer
from models.user import User
from services.chat import interact
from services.edf.models import BloomLevel, ErrorType, EvidenceResult
from tests.helpers import TestSessionFactory, encrypt_test_token

DEV_EMAIL = "dev@test.com"

DEV_PAYLOAD = {
    "sub": "devquiz-user",
    "email": DEV_EMAIL,
    "name": "Dev Quiz Tester",
    "googleId": "g-devquiz-user",
}


@pytest.fixture
def dev_mode_on(monkeypatch):
    monkeypatch.setattr(settings, "DEV_MODE_ENABLED", True)
    monkeypatch.setattr(settings, "DEV_MODE_EMAILS", DEV_EMAIL)


def _dev_cookies() -> dict:
    return {"authjs.session-token": encrypt_test_token(DEV_PAYLOAD)}


async def _seed_user_and_concept(tag: str = "dev-loop") -> dict:
    async with TestSessionFactory() as db:
        user = User(
            email=DEV_EMAIL, name="Dev Quiz Tester", google_id="g-devquiz-user",
        )
        concept = Concept(
            tag=tag, name_zh=f"{tag}-中文", name_en=tag,
            category="迴圈", difficulty_level=2,
        )
        db.add_all([user, concept])
        await db.commit()
        return {"user_id": user.id, "tag": tag}


# === DEV-7 debug sink（interact 單元）===

def _mock_evidence() -> EvidenceResult:
    return EvidenceResult(
        error_type=ErrorType.LOGIC,
        error_message="迴圈邊界",
        concept_tags=["control-flow"],
        bloom_level=BloomLevel.APPLY,
    )


@pytest.mark.asyncio
async def test_interact_fills_debug_sink():
    ids = await _seed_user_and_concept()
    sink: dict = {}
    with (
        patch("services.chat.analyze_evidence", new_callable=AsyncMock, return_value=_mock_evidence()),
        patch("services.chat.generate_feedback", new_callable=AsyncMock, return_value="ok"),
        patch("services.chat.fetch_kgraph_block_safe", new_callable=AsyncMock, return_value="<kgraph>x</kgraph>"),
    ):
        async with TestSessionFactory() as db:
            await interact(
                db=db, user_id=ids["user_id"], code="int main(){}",
                question="為什麼會錯？", debug_sink=sink,
            )
    assert sink["evidence"]["error_type"] == "logic"
    assert sink["strategy"]["hint_level"] == 0
    assert "instruction" in sink["strategy"]
    assert sink["kgraph_block"] == "<kgraph>x</kgraph>"
    assert sink["reflection_injected"] is False


@pytest.mark.asyncio
async def test_interact_without_sink_unchanged():
    """一般帳號路徑：不傳 sink，回傳形狀不變。"""
    ids = await _seed_user_and_concept()
    with (
        patch("services.chat.analyze_evidence", new_callable=AsyncMock, return_value=_mock_evidence()),
        patch("services.chat.generate_feedback", new_callable=AsyncMock, return_value="ok"),
    ):
        async with TestSessionFactory() as db:
            session, user_msg, ai_msg = await interact(
                db=db, user_id=ids["user_id"], code="", question="hi",
            )
    assert ai_msg.content == "ok"


# === DEV-8 診斷模擬 ===

@pytest.mark.asyncio
async def test_simulate_failures_injects_and_triggers(client: AsyncClient, dev_mode_on):
    ids = await _seed_user_and_concept()
    resp = await client.post(
        "/dev/simulate-failures",
        json={"tag": ids["tag"], "count": 3},
        cookies=_dev_cookies(),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["injected"] == 3
    assert body["streak"] == 3
    assert body["triggered"] is True  # CONSECUTIVE_FAILURES_REQUIRED = 3
    # stub 題目 + 3 筆答錯記錄已入庫
    async with TestSessionFactory() as db:
        answers = (
            await db.execute(select(func.count()).select_from(StudentAnswer))
        ).scalar()
        questions = (
            await db.execute(select(func.count()).select_from(Question))
        ).scalar()
    assert answers == 3
    assert questions == 1


@pytest.mark.asyncio
async def test_simulate_failures_reuses_existing_question(client: AsyncClient, dev_mode_on):
    ids = await _seed_user_and_concept()
    for _ in range(2):
        resp = await client.post(
            "/dev/simulate-failures",
            json={"tag": ids["tag"], "count": 2},
            cookies=_dev_cookies(),
        )
        assert resp.status_code == 200
    async with TestSessionFactory() as db:
        questions = (
            await db.execute(select(func.count()).select_from(Question))
        ).scalar()
    assert questions == 1  # 第二次重用 stub，不重複建題


@pytest.mark.asyncio
async def test_simulate_failures_unknown_tag_404(client: AsyncClient, dev_mode_on):
    await _seed_user_and_concept()
    resp = await client.post(
        "/dev/simulate-failures",
        json={"tag": "no-such"},
        cookies=_dev_cookies(),
    )
    assert resp.status_code == 404


# === DEV-9 題庫檢視 ===

@pytest.mark.asyncio
async def test_list_questions_filters_by_tag(client: AsyncClient, dev_mode_on):
    ids = await _seed_user_and_concept()
    async with TestSessionFactory() as db:
        db.add_all([
            Question(
                type="multiple_choice", concept_tags=[ids["tag"]],
                bloom_level=2, difficulty=1,
                content={"stem": "for 迴圈執行幾次？"}, validated=True,
            ),
            Question(
                type="coding", concept_tags=["other-tag"],
                bloom_level=3, difficulty=3, content={"stem": "無關題"},
            ),
        ])
        await db.commit()

    resp = await client.get(
        f"/dev/questions?tag={ids['tag']}", cookies=_dev_cookies(),
    )
    assert resp.status_code == 200
    questions = resp.json()["questions"]
    assert len(questions) == 1
    assert questions[0]["stem"] == "for 迴圈執行幾次？"
    assert questions[0]["validated"] is True


# === 403 防線 ===

@pytest.mark.asyncio
@pytest.mark.parametrize("method,path,body", [
    ("POST", "/dev/simulate-failures", {"tag": "x"}),
    ("GET", "/dev/questions?tag=x", None),
])
async def test_dev_quiz_endpoints_forbidden_for_normal_user(
    client: AsyncClient, dev_mode_on, method, path, body,
):
    token = encrypt_test_token({
        "sub": "normal2", "email": "normal2@test.com",
        "name": "N", "googleId": "g-normal2",
    })
    resp = await client.request(
        method, path, json=body, cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 403
