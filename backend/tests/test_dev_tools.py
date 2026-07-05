"""開發者工具端點測試（DEV-3/5/6）— 分類重置、熟練度覆寫、身分切換。"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from core.config import settings
from models.chat import ChatMessage, ChatSession, MessageRole
from models.concept import Concept
from models.learning import LearningPath, LearningUnit
from models.mastery import StudentMastery
from models.quiz import Question, StudentAnswer
from models.reflection import Reflection, ReflectionSourceType
from models.user import User, UserRole
from tests.helpers import TestSessionFactory, encrypt_test_token

DEV_EMAIL = "dev@test.com"

DEV_PAYLOAD = {
    "sub": "devtools-user",
    "email": DEV_EMAIL,
    "name": "Dev Tools Tester",
    "googleId": "g-devtools-user",
}


@pytest.fixture
def dev_mode_on(monkeypatch):
    monkeypatch.setattr(settings, "DEV_MODE_ENABLED", True)
    monkeypatch.setattr(settings, "DEV_MODE_EMAILS", DEV_EMAIL)


def _dev_cookies() -> dict:
    return {"authjs.session-token": encrypt_test_token(DEV_PAYLOAD)}


def _concept(tag: str, category: str = "入門") -> Concept:
    return Concept(
        tag=tag, name_zh=f"{tag}-中文", name_en=tag,
        category=category, difficulty_level=2,
    )


async def _seed_user_with_data() -> dict:
    """建立 dev user + 各類學習資料，回傳 ids。"""
    async with TestSessionFactory() as db:
        user = User(
            email=DEV_EMAIL, name="Dev Tools Tester",
            google_id="g-devtools-user",
        )
        c1 = _concept("dev-c1")
        c2 = _concept("dev-c2", category="迴圈")
        db.add_all([user, c1, c2])
        await db.flush()

        question = Question(
            type="multiple_choice", concept_tags=["dev-c1"], bloom_level=2,
            difficulty=2, content={"stem": "q"},
        )
        path = LearningPath(user_id=user.id, title="p")
        db.add_all([question, path])
        await db.flush()

        db.add_all([
            StudentMastery(user_id=user.id, concept_id=c1.id, confidence=0.5),
            LearningUnit(
                path_id=path.id, concept_id=c1.id, order_index=0, content={},
            ),
            StudentAnswer(
                user_id=user.id, question_id=question.id,
                answer={"choice": 0}, is_correct=True,
            ),
            Reflection(
                user_id=user.id,
                source_type=ReflectionSourceType.QUIZ.value,
                source_id=question.id, planned_steps=[],
            ),
        ])
        session = ChatSession(user_id=user.id)
        db.add(session)
        await db.flush()
        db.add(ChatMessage(
            session_id=session.id, role=MessageRole.USER, content="hi",
        ))
        await db.commit()
        return {"user_id": user.id, "c1": c1.id, "c2": c2.id}


async def _count(model) -> int:
    async with TestSessionFactory() as db:
        return (await db.execute(select(func.count()).select_from(model))).scalar()


# === 403 防線 ===

@pytest.mark.asyncio
@pytest.mark.parametrize("method,path,body", [
    ("POST", "/dev/reset", {"categories": ["mastery"]}),
    ("PUT", "/dev/mastery", {"tags": ["x"], "confidence": 0.5}),
    ("PUT", "/dev/role", {"role": "teacher"}),
])
async def test_dev_endpoints_forbidden_for_normal_user(
    client: AsyncClient, dev_mode_on, method, path, body,
):
    token = encrypt_test_token({
        "sub": "normal", "email": "normal@test.com",
        "name": "N", "googleId": "g-normal",
    })
    resp = await client.request(
        method, path, json=body, cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 403


# === POST /dev/reset ===

@pytest.mark.asyncio
async def test_reset_single_category_keeps_others(client: AsyncClient, dev_mode_on):
    await _seed_user_with_data()
    resp = await client.post(
        "/dev/reset", json={"categories": ["mastery"]}, cookies=_dev_cookies(),
    )
    assert resp.status_code == 200
    assert resp.json()["deleted"] == {"mastery": 1}
    assert await _count(StudentMastery) == 0
    # 其他類別不受影響
    assert await _count(StudentAnswer) == 1
    assert await _count(LearningPath) == 1
    assert await _count(ChatSession) == 1


@pytest.mark.asyncio
async def test_reset_all_categories(client: AsyncClient, dev_mode_on):
    await _seed_user_with_data()
    resp = await client.post(
        "/dev/reset",
        json={"categories": ["mastery", "progress", "quiz", "chat"]},
        cookies=_dev_cookies(),
    )
    assert resp.status_code == 200
    for model in (
        StudentMastery, LearningPath, LearningUnit,
        StudentAnswer, Reflection, ChatSession, ChatMessage,
    ):
        assert await _count(model) == 0, model.__name__
    # 題庫與 concepts（非使用者資料）保留
    assert await _count(Question) == 1
    assert await _count(Concept) == 2


@pytest.mark.asyncio
async def test_reset_empty_categories_422(client: AsyncClient, dev_mode_on):
    await _seed_user_with_data()
    resp = await client.post(
        "/dev/reset", json={"categories": []}, cookies=_dev_cookies(),
    )
    assert resp.status_code == 422


# === PUT /dev/mastery ===

@pytest.mark.asyncio
async def test_set_mastery_by_tags_upserts(client: AsyncClient, dev_mode_on):
    ids = await _seed_user_with_data()
    resp = await client.put(
        "/dev/mastery",
        json={"tags": ["dev-c1", "dev-c2"], "confidence": 0.9},
        cookies=_dev_cookies(),
    )
    assert resp.status_code == 200
    assert resp.json() == {"updated": 2}
    async with TestSessionFactory() as db:
        rows = {
            m.concept_id: m
            for m in (await db.execute(select(StudentMastery))).scalars()
        }
    # 既有記錄更新、無記錄新建（exposure_count=1 標記已互動）
    assert rows[ids["c1"]].confidence == 0.9
    assert rows[ids["c2"]].confidence == 0.9
    assert rows[ids["c2"]].exposure_count == 1
    assert rows[ids["c2"]].last_practiced_at is not None


@pytest.mark.asyncio
async def test_set_mastery_by_category(client: AsyncClient, dev_mode_on):
    await _seed_user_with_data()
    resp = await client.put(
        "/dev/mastery",
        json={"category": "迴圈", "confidence": 0.2},
        cookies=_dev_cookies(),
    )
    assert resp.status_code == 200
    assert resp.json() == {"updated": 1}


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [
    {"confidence": 0.5},                                  # 兩者皆缺
    {"tags": ["x"], "category": "入門", "confidence": 0.5},  # 兩者皆給
    {"tags": ["x"], "confidence": 1.5},                    # 超出範圍
])
async def test_set_mastery_validation_422(client: AsyncClient, dev_mode_on, body):
    await _seed_user_with_data()
    resp = await client.put("/dev/mastery", json=body, cookies=_dev_cookies())
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_set_mastery_unknown_tags_updates_zero(client: AsyncClient, dev_mode_on):
    await _seed_user_with_data()
    resp = await client.put(
        "/dev/mastery",
        json={"tags": ["no-such-tag"], "confidence": 0.5},
        cookies=_dev_cookies(),
    )
    assert resp.status_code == 200
    assert resp.json() == {"updated": 0}


# === PUT /dev/role ===

@pytest.mark.asyncio
async def test_set_role_switches_and_persists(client: AsyncClient, dev_mode_on):
    ids = await _seed_user_with_data()
    resp = await client.put(
        "/dev/role", json={"role": "teacher"}, cookies=_dev_cookies(),
    )
    assert resp.status_code == 200
    assert resp.json() == {"role": "teacher"}
    async with TestSessionFactory() as db:
        user = await db.get(User, ids["user_id"])
        assert user.role == UserRole.TEACHER

    # 切回 student
    resp = await client.put(
        "/dev/role", json={"role": "student"}, cookies=_dev_cookies(),
    )
    assert resp.json() == {"role": "student"}


@pytest.mark.asyncio
async def test_set_role_rejects_admin(client: AsyncClient, dev_mode_on):
    await _seed_user_with_data()
    resp = await client.put(
        "/dev/role", json={"role": "admin"}, cookies=_dev_cookies(),
    )
    assert resp.status_code == 422
