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
    assert [f["name"] for f in files] == ["作業一.cpp"]  # 副檔名一律補上
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


# === 副檔名正規化（使用者驗收：main.md 也能執行，副檔名形同虛設）===

@pytest.mark.parametrize(
    "given,stored",
    [
        ("main", "main.cpp"),        # 無副檔名 → 補上
        ("main.cpp", "main.cpp"),    # 已正確 → 不重複補
        ("main.CPP", "main.CPP"),    # 大小寫不敏感
        ("main.md", "main.md.cpp"),  # 其他副檔名不靜默改寫，只補收尾
        (" a.cpp ", "a.cpp"),        # 前後空白去除
    ],
)
async def test_name_normalized_to_cpp(client: AsyncClient, given: str, stored: str):
    saved = (
        await client.put(
            "/code/files", json={"name": given, "code": ""}, cookies=_ck(USER_A)
        )
    ).json()
    assert saved["name"] == stored


async def test_name_too_long_after_suffix_rejected(client: AsyncClient):
    resp = await client.put(
        "/code/files", json={"name": "x" * 98, "code": ""}, cookies=_ck(USER_A)
    )
    assert resp.status_code == 422


# === 重新命名 ===

async def test_rename_moves_file_and_follows_draft(client: AsyncClient):
    ck = _ck(USER_A)
    saved = (
        await client.put("/code/files", json={"name": "舊", "code": "v"}, cookies=ck)
    ).json()
    await client.put(
        "/code/draft", json={"code": "v", "opened_name": "舊.cpp"}, cookies=ck
    )

    r = await client.patch(
        "/code/files", json={"old_name": "舊.cpp", "new_name": "新"}, cookies=ck
    )
    assert r.status_code == 200
    assert r.json()["name"] == "新.cpp"
    assert r.json()["id"] == saved["id"]  # 同一份檔案，非複製

    files = (await client.get("/code/files", cookies=ck)).json()
    assert [f["name"] for f in files] == ["新.cpp"]
    # 草稿的檔名關聯跟著改，重整後仍停在同一檔
    draft = (await client.get("/code/draft", cookies=ck)).json()
    assert draft["opened_name"] == "新.cpp"


async def test_rename_to_existing_name_conflicts(client: AsyncClient):
    ck = _ck(USER_A)
    await client.put("/code/files", json={"name": "a", "code": ""}, cookies=ck)
    await client.put("/code/files", json={"name": "b", "code": ""}, cookies=ck)
    resp = await client.patch(
        "/code/files", json={"old_name": "a.cpp", "new_name": "b"}, cookies=ck
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "CODE_FILE_NAME_TAKEN"


async def test_rename_other_user_file_is_404(client: AsyncClient):
    await client.put(
        "/code/files", json={"name": "a", "code": ""}, cookies=_ck(USER_A)
    )
    resp = await client.patch(
        "/code/files", json={"old_name": "a.cpp", "new_name": "z"}, cookies=_ck(USER_B)
    )
    assert resp.status_code == 404


async def test_concurrent_first_draft_save_does_not_500(client: AsyncClient):
    """自動存檔與 handoff 開檔可能同時建立第一份草稿（partial unique index）。"""
    import asyncio

    ck = _ck(USER_A)
    await client.get("/code/draft", cookies=ck)  # 先建好 user，只留草稿的競態
    results = await asyncio.gather(
        *(
            client.put("/code/draft", json={"code": f"v{i}"}, cookies=ck)
            for i in range(3)
        )
    )
    assert [r.status_code for r in results] == [200, 200, 200]
    assert (await client.get("/code/draft", cookies=ck)).status_code == 200


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
