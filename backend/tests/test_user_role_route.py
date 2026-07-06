"""身分自選 / 切換 API 測試（5-1d-2）。"""

import pytest
from httpx import AsyncClient

from tests.helpers import encrypt_test_token

USER = {
    "sub": "u-1",
    "email": "user@example.com",
    "name": "Google Name",
    "googleId": "g-u-1",
}
_COOKIE = "authjs.session-token"
_PROFILE = {
    "school": "台大",
    "department": "資工",
    "student_id": "B123",
    "real_name": "小明",
}


def _cookies() -> dict:
    return {_COOKIE: encrypt_test_token(USER)}


# === 首次選擇（不清資料）===

async def test_first_pick_sets_role_no_reset(client: AsyncClient):
    cookies = _cookies()
    resp = await client.post("/users/role", json={"role": "teacher"}, cookies=cookies)
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "teacher"
    assert body["role_selected"] is True
    assert body["did_reset"] is False


async def test_users_me_reflects_role_selected(client: AsyncClient):
    cookies = _cookies()
    before = (await client.get("/users/me", cookies=cookies)).json()
    assert before["role_selected"] is False
    await client.post("/users/role", json={"role": "student"}, cookies=cookies)
    after = (await client.get("/users/me", cookies=cookies)).json()
    assert after["role"] == "student"
    assert after["role_selected"] is True


# === 切換（全清資料）===

async def test_switch_role_resets_profile(client: AsyncClient):
    cookies = _cookies()
    # 首選學生 + 填 profile
    await client.post("/users/role", json={"role": "student"}, cookies=cookies)
    await client.post("/profile", json=_PROFILE, cookies=cookies)
    assert (await client.get("/profile", cookies=cookies)).status_code == 200

    # 切換為教師 → 全清（did_reset=True），profile 消失
    resp = await client.post("/users/role", json={"role": "teacher"}, cookies=cookies)
    assert resp.json()["did_reset"] is True
    assert (await client.get("/profile", cookies=cookies)).status_code == 404


# === 驗證 ===

async def test_cannot_self_select_admin(client: AsyncClient):
    resp = await client.post("/users/role", json={"role": "admin"}, cookies=_cookies())
    assert resp.status_code == 422


async def test_role_requires_auth(client: AsyncClient):
    resp = await client.post("/users/role", json={"role": "student"})
    assert resp.status_code == 401
