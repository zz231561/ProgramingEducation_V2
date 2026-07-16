"""Workspace 程式碼存檔 API 測試（U2e）— 草稿 upsert + 命名檔案 CRUD。"""

import pytest
from httpx import AsyncClient

from tests.helpers import encrypt_test_token

USER_A = {"sub": "cf-a", "email": "cfa@ex.com", "name": "A", "googleId": "g-cf-a"}
USER_B = {"sub": "cf-b", "email": "cfb@ex.com", "name": "B", "googleId": "g-cf-b"}
_COOKIE = "authjs.session-token"


def _ck(p: dict) -> dict:
    return {_COOKIE: encrypt_test_token(p)}


# === 草稿 ===

async def test_draft_404_before_save(client: AsyncClient):
    resp = await client.get("/code/draft", cookies=_ck(USER_A))
    assert resp.status_code == 404
    assert resp.json()["error"] == "DRAFT_NOT_FOUND"


async def test_draft_upsert_and_restore(client: AsyncClient):
    ck = _ck(USER_A)
    r1 = await client.put("/code/draft", json={"code": "int main(){}"}, cookies=ck)
    assert r1.status_code == 200
    # 覆蓋
    await client.put("/code/draft", json={"code": "v2"}, cookies=ck)
    got = (await client.get("/code/draft", cookies=ck)).json()
    assert got["code"] == "v2"


async def test_draft_opened_name_roundtrip_and_keep(client: AsyncClient):
    ck = _ck(USER_A)
    # 帶 opened_name 儲存 → 讀回
    r = await client.put(
        "/code/draft", json={"code": "v1", "opened_name": "作業一"}, cookies=ck
    )
    assert r.json()["opened_name"] == "作業一"
    # 省略 opened_name（自動存檔情境）→ 保留現值
    r = await client.put("/code/draft", json={"code": "v2"}, cookies=ck)
    assert r.json()["opened_name"] == "作業一"
    # 帶 null → 清除（開新檔案）
    r = await client.put(
        "/code/draft", json={"code": "v3", "opened_name": None}, cookies=ck
    )
    assert r.json()["opened_name"] is None


async def test_draft_is_per_user(client: AsyncClient):
    await client.put("/code/draft", json={"code": "mine"}, cookies=_ck(USER_A))
    resp = await client.get("/code/draft", cookies=_ck(USER_B))
    assert resp.status_code == 404


# === 命名檔案 ===

async def test_save_list_load_delete_file(client: AsyncClient):
    ck = _ck(USER_A)
    saved = (
        await client.put(
            "/code/files", json={"name": "作業一", "code": "abc"}, cookies=ck
        )
    ).json()
    files = (await client.get("/code/files", cookies=ck)).json()
    assert [f["name"] for f in files] == ["作業一"]
    assert "code" not in files[0]  # 列表僅 meta

    loaded = (await client.get(f"/code/files/{saved['id']}", cookies=ck)).json()
    assert loaded["code"] == "abc"

    assert (
        await client.delete(f"/code/files/{saved['id']}", cookies=ck)
    ).status_code == 204
    assert (await client.get("/code/files", cookies=ck)).json() == []


async def test_save_same_name_overwrites(client: AsyncClient):
    ck = _ck(USER_A)
    f1 = (
        await client.put("/code/files", json={"name": "x", "code": "v1"}, cookies=ck)
    ).json()
    f2 = (
        await client.put("/code/files", json={"name": "x", "code": "v2"}, cookies=ck)
    ).json()
    assert f2["id"] == f1["id"]
    assert f2["code"] == "v2"


async def test_other_user_file_is_404(client: AsyncClient):
    fid = (
        await client.put(
            "/code/files", json={"name": "x", "code": "v"}, cookies=_ck(USER_A)
        )
    ).json()["id"]
    ck_b = _ck(USER_B)
    assert (await client.get(f"/code/files/{fid}", cookies=ck_b)).status_code == 404
    assert (
        await client.delete(f"/code/files/{fid}", cookies=ck_b)
    ).status_code == 404


async def test_blank_name_rejected(client: AsyncClient):
    resp = await client.put(
        "/code/files", json={"name": "   ", "code": "v"}, cookies=_ck(USER_A)
    )
    assert resp.status_code == 422


async def test_file_limit(client: AsyncClient, monkeypatch):
    import services.workspace_files as wf

    monkeypatch.setattr(wf, "MAX_FILES_PER_USER", 2)
    ck = _ck(USER_A)
    for i in range(2):
        await client.put(
            "/code/files", json={"name": f"f{i}", "code": ""}, cookies=ck
        )
    resp = await client.put(
        "/code/files", json={"name": "f2", "code": ""}, cookies=ck
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "CODE_FILE_LIMIT"
