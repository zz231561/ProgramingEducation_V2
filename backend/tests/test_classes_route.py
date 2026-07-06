"""班級管理 API 測試（5-1b-2）— 教師 CRUD + 授權 + 邀請碼。"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from models.user import User, UserRole
from tests.helpers import encrypt_test_token, TestSessionFactory

TEACHER_A = {
    "sub": "t-a",
    "email": "teacher-a@example.com",
    "name": "Teacher A",
    "googleId": "g-t-a",
}
TEACHER_B = {
    "sub": "t-b",
    "email": "teacher-b@example.com",
    "name": "Teacher B",
    "googleId": "g-t-b",
}
STUDENT = {
    "sub": "s-1",
    "email": "student@example.com",
    "name": "Student",
    "googleId": "g-s-1",
}

_COOKIE = "authjs.session-token"


async def _set_role(email: str, role: UserRole) -> None:
    async with TestSessionFactory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.role = role
        await session.commit()


async def _as_teacher(client: AsyncClient, payload: dict) -> dict:
    """建立使用者、升級為 teacher，回傳 cookies dict。"""
    token = encrypt_test_token(payload)
    cookies = {_COOKIE: token}
    # 首次請求觸發 get_or_create_user（此時仍是 student，回 403 無妨）
    await client.get("/classes", cookies=cookies)
    await _set_role(payload["email"], UserRole.TEACHER)
    return cookies


# === 建立 ===

async def test_create_class_returns_6_digit_code(client: AsyncClient):
    cookies = await _as_teacher(client, TEACHER_A)
    resp = await client.post("/classes", json={"name": "資工一甲"}, cookies=cookies)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "資工一甲"
    assert body["is_active"] is True
    assert body["member_count"] == 0
    # 邀請碼為 6 位數字
    assert len(body["invite_code"]) == 6
    assert body["invite_code"].isdigit()


async def test_two_classes_get_distinct_codes(client: AsyncClient):
    cookies = await _as_teacher(client, TEACHER_A)
    c1 = (await client.post("/classes", json={"name": "A"}, cookies=cookies)).json()
    c2 = (await client.post("/classes", json={"name": "B"}, cookies=cookies)).json()
    assert c1["invite_code"] != c2["invite_code"]


async def test_student_cannot_create_class(client: AsyncClient):
    token = encrypt_test_token(STUDENT)
    cookies = {_COOKIE: token}
    resp = await client.post("/classes", json={"name": "X"}, cookies=cookies)
    assert resp.status_code == 403
    assert resp.json()["error"] == "FORBIDDEN"


async def test_create_class_rejects_empty_name(client: AsyncClient):
    cookies = await _as_teacher(client, TEACHER_A)
    resp = await client.post("/classes", json={"name": ""}, cookies=cookies)
    assert resp.status_code == 422


# === 列出 ===

async def test_list_returns_only_own_classes(client: AsyncClient):
    a_cookies = await _as_teacher(client, TEACHER_A)
    b_cookies = await _as_teacher(client, TEACHER_B)
    await client.post("/classes", json={"name": "A-class"}, cookies=a_cookies)
    await client.post("/classes", json={"name": "B-class"}, cookies=b_cookies)

    a_list = (await client.get("/classes", cookies=a_cookies)).json()
    assert [c["name"] for c in a_list] == ["A-class"]


# === 更新 ===

async def test_patch_deactivates_and_renames(client: AsyncClient):
    cookies = await _as_teacher(client, TEACHER_A)
    created = (await client.post("/classes", json={"name": "old"}, cookies=cookies)).json()

    resp = await client.patch(
        f"/classes/{created['id']}",
        json={"name": "new", "is_active": False},
        cookies=cookies,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "new"
    assert body["is_active"] is False


async def test_patch_other_teacher_class_returns_404(client: AsyncClient):
    a_cookies = await _as_teacher(client, TEACHER_A)
    b_cookies = await _as_teacher(client, TEACHER_B)
    a_class = (await client.post("/classes", json={"name": "A"}, cookies=a_cookies)).json()

    resp = await client.patch(
        f"/classes/{a_class['id']}",
        json={"is_active": False},
        cookies=b_cookies,
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "CLASS_NOT_FOUND"
