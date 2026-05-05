"""Comprehension API route 整合測試（roadmap 2-6a）。

涵蓋：
- 401 未登入
- GET 初始狀態 → 4 欄位皆 null
- PUT 寫入完整 comprehension
- PUT partial 更新（保留未提供欄位）
- PUT 422 type 非法
- GET / PUT 跨使用者 → 404（不洩漏存在性）
- GET / PUT 不存在的 student_answer → 404
"""

import uuid

from httpx import AsyncClient

from models.quiz import Question, StudentAnswer
from tests.helpers import TestSessionFactory, encrypt_test_token

OWNER_PAYLOAD = {
    "sub": "comp-owner",
    "email": "owner@test.com",
    "name": "Owner",
    "googleId": "g-comp-owner",
}

OTHER_PAYLOAD = {
    "sub": "comp-other",
    "email": "other-comp@test.com",
    "name": "Other",
    "googleId": "g-comp-other",
}


async def _seed_answer_for(user_payload: dict, client: AsyncClient) -> uuid.UUID:
    """走 auth 流程登入一次以建立 user，再用 ORM 直接插 question + student_answer。"""
    # 1. 登入觸發 user upsert（getCurrentUser dep 會自動建立 User）
    token = encrypt_test_token(user_payload)
    await client.get("/auth/me", cookies={"authjs.session-token": token})

    # 2. 找該 user 並 seed
    from sqlalchemy import select

    from models.user import User

    async with TestSessionFactory() as db:
        user = (
            await db.execute(select(User).where(User.google_id == user_payload["googleId"]))
        ).scalar_one()
        q = Question(
            type="multiple_choice",
            concept_tags=["syntax-basic"],
            bloom_level=3,
            difficulty=1,
            content={"stem": "...", "options": ["a", "b"], "answer_index": 0},
            explanation="",
            source="generated",
            validated=True,
        )
        db.add(q)
        await db.flush()
        ans = StudentAnswer(
            user_id=user.id,
            question_id=q.id,
            answer={"selected": 0},
            is_correct=True,
            time_spent_seconds=12,
            hint_level_used=0,
            feedback="",
        )
        db.add(ans)
        await db.commit()
        await db.refresh(ans)
        return ans.id


# === auth ===


async def test_get_requires_auth(client: AsyncClient):
    resp = await client.get(f"/comprehension/{uuid.uuid4()}")
    assert resp.status_code == 401


async def test_put_requires_auth(client: AsyncClient):
    resp = await client.put(
        f"/comprehension/{uuid.uuid4()}",
        json={"comprehension_type": "epl"},
    )
    assert resp.status_code == 401


# === GET ===


async def test_get_initial_state_returns_nulls(client: AsyncClient):
    answer_id = await _seed_answer_for(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    resp = await client.get(
        f"/comprehension/{answer_id}",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["student_answer_id"] == str(answer_id)
    assert body["comprehension_type"] is None
    assert body["comprehension_prompt"] is None
    assert body["comprehension_answer"] is None
    assert body["comprehension_passed"] is None


async def test_get_nonexistent_returns_404(client: AsyncClient):
    token = encrypt_test_token(OWNER_PAYLOAD)
    # 觸發 user upsert
    await client.get("/auth/me", cookies={"authjs.session-token": token})

    resp = await client.get(
        f"/comprehension/{uuid.uuid4()}",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "STUDENT_ANSWER_NOT_FOUND"


async def test_get_other_user_returns_404(client: AsyncClient):
    # owner 建作答 → other 嘗試讀取
    answer_id = await _seed_answer_for(OWNER_PAYLOAD, client)
    other_token = encrypt_test_token(OTHER_PAYLOAD)
    await client.get("/auth/me", cookies={"authjs.session-token": other_token})

    resp = await client.get(
        f"/comprehension/{answer_id}",
        cookies={"authjs.session-token": other_token},
    )
    assert resp.status_code == 404


# === PUT ===


async def test_put_writes_full_comprehension(client: AsyncClient):
    answer_id = await _seed_answer_for(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    resp = await client.put(
        f"/comprehension/{answer_id}",
        json={
            "comprehension_type": "epl",
            "comprehension_prompt": "用自己的話解釋你的解法",
            "comprehension_answer": "我用了一個迴圈逐一檢查每個元素",
            "comprehension_passed": True,
        },
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["comprehension_type"] == "epl"
    assert body["comprehension_prompt"] == "用自己的話解釋你的解法"
    assert body["comprehension_answer"] == "我用了一個迴圈逐一檢查每個元素"
    assert body["comprehension_passed"] is True


async def test_put_partial_preserves_existing_fields(client: AsyncClient):
    """先寫 prompt + type，再 partial 寫 answer + passed → prompt/type 不變。"""
    answer_id = await _seed_answer_for(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    # 先寫 prompt + type
    await client.put(
        f"/comprehension/{answer_id}",
        json={
            "comprehension_type": "predict_output",
            "comprehension_prompt": "輸入 [3,1,4]，輸出？",
        },
        cookies={"authjs.session-token": token},
    )

    # partial：補 answer + passed
    resp = await client.put(
        f"/comprehension/{answer_id}",
        json={
            "comprehension_answer": "[1,3,4]",
            "comprehension_passed": False,
        },
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["comprehension_type"] == "predict_output"  # 保留
    assert body["comprehension_prompt"] == "輸入 [3,1,4]，輸出？"  # 保留
    assert body["comprehension_answer"] == "[1,3,4]"
    assert body["comprehension_passed"] is False


async def test_put_invalid_type_returns_422(client: AsyncClient):
    answer_id = await _seed_answer_for(OWNER_PAYLOAD, client)
    token = encrypt_test_token(OWNER_PAYLOAD)

    resp = await client.put(
        f"/comprehension/{answer_id}",
        json={"comprehension_type": "homework"},  # 非 enum
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "INVALID_COMPREHENSION_TYPE"


async def test_put_other_user_returns_404(client: AsyncClient):
    answer_id = await _seed_answer_for(OWNER_PAYLOAD, client)
    other_token = encrypt_test_token(OTHER_PAYLOAD)
    await client.get("/auth/me", cookies={"authjs.session-token": other_token})

    resp = await client.put(
        f"/comprehension/{answer_id}",
        json={"comprehension_type": "epl", "comprehension_passed": True},
        cookies={"authjs.session-token": other_token},
    )
    assert resp.status_code == 404


async def test_put_nonexistent_returns_404(client: AsyncClient):
    token = encrypt_test_token(OWNER_PAYLOAD)
    await client.get("/auth/me", cookies={"authjs.session-token": token})

    resp = await client.put(
        f"/comprehension/{uuid.uuid4()}",
        json={"comprehension_type": "epl"},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404
