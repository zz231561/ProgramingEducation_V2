"""學生 profile + 加入班級 + 教師名冊 API 測試（5-1b-3）。"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from models.user import User, UserRole
from tests.helpers import encrypt_test_token, TestSessionFactory

TEACHER = {
    "sub": "t-1",
    "email": "teacher@example.com",
    "name": "Teacher",
    "googleId": "g-t-1",
}
STUDENT = {
    "sub": "s-1",
    "email": "student@example.com",
    "name": "Google Nick",
    "googleId": "g-s-1",
}
OTHER_TEACHER = {
    "sub": "t-2",
    "email": "teacher2@example.com",
    "name": "Teacher2",
    "googleId": "g-t-2",
}

_COOKIE = "authjs.session-token"
_PROFILE = {
    "school": "台灣大學",
    "department": "資訊工程學系",
    "student_id": "B10901001",
    "real_name": "王小明",
}


async def _set_role(email: str, role: UserRole) -> None:
    async with TestSessionFactory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.role = role
        await session.commit()


async def _as_teacher(client: AsyncClient, payload: dict) -> dict:
    cookies = {_COOKIE: encrypt_test_token(payload)}
    await client.get("/classes", cookies=cookies)
    await _set_role(payload["email"], UserRole.TEACHER)
    return cookies


def _student_cookies() -> dict:
    return {_COOKIE: encrypt_test_token(STUDENT)}


# === profile ===

async def test_get_profile_before_submit_returns_404(client: AsyncClient):
    resp = await client.get("/profile", cookies=_student_cookies())
    assert resp.status_code == 404
    assert resp.json()["error"] == "PROFILE_NOT_FOUND"


async def test_submit_then_get_profile(client: AsyncClient):
    cookies = _student_cookies()
    post = await client.post("/profile", json=_PROFILE, cookies=cookies)
    assert post.status_code == 200
    body = post.json()
    assert body["real_name"] == "王小明"
    assert body["email"] == STUDENT["email"]  # email 來自 users，非前端提交

    got = (await client.get("/profile", cookies=cookies)).json()
    assert got["student_id"] == "B10901001"


async def test_submit_profile_is_upsert(client: AsyncClient):
    cookies = _student_cookies()
    await client.post("/profile", json=_PROFILE, cookies=cookies)
    updated = {**_PROFILE, "real_name": "王大明"}
    resp = await client.post("/profile", json=updated, cookies=cookies)
    assert resp.status_code == 200
    assert resp.json()["real_name"] == "王大明"


async def test_submit_profile_rejects_blank_field(client: AsyncClient):
    resp = await client.post(
        "/profile", json={**_PROFILE, "school": ""}, cookies=_student_cookies()
    )
    assert resp.status_code == 422


# === join ===

async def _make_class(client: AsyncClient, teacher_cookies: dict) -> dict:
    return (
        await client.post("/classes", json={"name": "班"}, cookies=teacher_cookies)
    ).json()


async def test_join_without_profile_returns_409(client: AsyncClient):
    t_cookies = await _as_teacher(client, TEACHER)
    klass = await _make_class(client, t_cookies)

    resp = await client.post(
        "/classes/join",
        json={"invite_code": klass["invite_code"]},
        cookies=_student_cookies(),
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "PROFILE_REQUIRED"


async def test_join_with_profile_succeeds(client: AsyncClient):
    t_cookies = await _as_teacher(client, TEACHER)
    klass = await _make_class(client, t_cookies)
    s_cookies = _student_cookies()
    await client.post("/profile", json=_PROFILE, cookies=s_cookies)

    resp = await client.post(
        "/classes/join",
        json={"invite_code": klass["invite_code"]},
        cookies=s_cookies,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "班"


async def test_join_is_idempotent(client: AsyncClient):
    t_cookies = await _as_teacher(client, TEACHER)
    klass = await _make_class(client, t_cookies)
    s_cookies = _student_cookies()
    await client.post("/profile", json=_PROFILE, cookies=s_cookies)

    for _ in range(2):
        await client.post(
            "/classes/join",
            json={"invite_code": klass["invite_code"]},
            cookies=s_cookies,
        )
    listed = (await client.get("/classes", cookies=t_cookies)).json()
    assert listed[0]["member_count"] == 1


async def test_join_invalid_code_returns_404(client: AsyncClient):
    s_cookies = _student_cookies()
    await client.post("/profile", json=_PROFILE, cookies=s_cookies)
    resp = await client.post(
        "/classes/join", json={"invite_code": "000000"}, cookies=s_cookies
    )
    assert resp.status_code == 404


async def test_join_inactive_class_returns_404(client: AsyncClient):
    t_cookies = await _as_teacher(client, TEACHER)
    klass = await _make_class(client, t_cookies)
    await client.patch(
        f"/classes/{klass['id']}", json={"is_active": False}, cookies=t_cookies
    )
    s_cookies = _student_cookies()
    await client.post("/profile", json=_PROFILE, cookies=s_cookies)

    resp = await client.post(
        "/classes/join",
        json={"invite_code": klass["invite_code"]},
        cookies=s_cookies,
    )
    assert resp.status_code == 404


async def test_join_bad_code_format_returns_422(client: AsyncClient):
    s_cookies = _student_cookies()
    await client.post("/profile", json=_PROFILE, cookies=s_cookies)
    resp = await client.post(
        "/classes/join", json={"invite_code": "abc"}, cookies=s_cookies
    )
    assert resp.status_code == 422


# === mine 我的班級 ===

async def test_mine_empty_before_join(client: AsyncClient):
    resp = await client.get("/classes/mine", cookies=_student_cookies())
    assert resp.status_code == 200
    assert resp.json() == []


async def test_mine_lists_joined_classes(client: AsyncClient):
    t_cookies = await _as_teacher(client, TEACHER)
    klass = await _make_class(client, t_cookies)
    s_cookies = _student_cookies()
    await client.post("/profile", json=_PROFILE, cookies=s_cookies)
    await client.post(
        "/classes/join",
        json={"invite_code": klass["invite_code"]},
        cookies=s_cookies,
    )

    rows = (await client.get("/classes/mine", cookies=s_cookies)).json()
    assert len(rows) == 1
    assert rows[0]["name"] == "班"
    assert rows[0]["teacher_name"] == TEACHER["name"]
    assert "invite_code" not in rows[0]  # 學生視角不洩漏邀請碼


# === members 名冊 ===

async def test_members_lists_student_profiles(client: AsyncClient):
    t_cookies = await _as_teacher(client, TEACHER)
    klass = await _make_class(client, t_cookies)
    s_cookies = _student_cookies()
    await client.post("/profile", json=_PROFILE, cookies=s_cookies)
    await client.post(
        "/classes/join",
        json={"invite_code": klass["invite_code"]},
        cookies=s_cookies,
    )

    resp = await client.get(f"/classes/{klass['id']}/members", cookies=t_cookies)
    assert resp.status_code == 200
    roster = resp.json()
    assert len(roster) == 1
    assert roster[0]["real_name"] == "王小明"
    assert roster[0]["school"] == "台灣大學"
    assert roster[0]["email"] == STUDENT["email"]


async def test_members_other_teacher_returns_404(client: AsyncClient):
    t_cookies = await _as_teacher(client, TEACHER)
    other_cookies = await _as_teacher(client, OTHER_TEACHER)
    klass = await _make_class(client, t_cookies)

    resp = await client.get(
        f"/classes/{klass['id']}/members", cookies=other_cookies
    )
    assert resp.status_code == 404


async def test_members_requires_teacher_role(client: AsyncClient):
    t_cookies = await _as_teacher(client, TEACHER)
    klass = await _make_class(client, t_cookies)
    resp = await client.get(
        f"/classes/{klass['id']}/members", cookies=_student_cookies()
    )
    assert resp.status_code == 403
