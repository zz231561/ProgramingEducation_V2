"""作業指派 API 測試（5-5a-2）— 教師 CRUD + 附件上傳/下載/授權。"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.errors import AppError
from models.assignment import MAX_ATTACHMENT_BYTES
from models.classroom import ClassMember
from models.user import User, UserRole
from services.assignment import validate_upload
from tests.helpers import TestSessionFactory, encrypt_test_token

TEACHER = {"sub": "at", "email": "at@example.com", "name": "AT", "googleId": "g-at"}
TEACHER2 = {"sub": "at2", "email": "at2@example.com", "name": "AT2", "googleId": "g-at2"}
STUDENT = {"sub": "as", "email": "as@example.com", "name": "AS", "googleId": "g-as"}
OUTSIDER = {"sub": "ao", "email": "ao@example.com", "name": "AO", "googleId": "g-ao"}
_COOKIE = "authjs.session-token"


def _cookies(payload: dict) -> dict:
    return {_COOKIE: encrypt_test_token(payload)}


async def _set_role(email: str, role: UserRole) -> None:
    async with TestSessionFactory() as db:
        u = (await db.execute(select(User).where(User.email == email))).scalar_one()
        u.role = role
        await db.commit()


async def _uid(email: str) -> uuid.UUID:
    async with TestSessionFactory() as db:
        return (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one().id


async def _as_teacher(client: AsyncClient, payload: dict) -> dict:
    cookies = _cookies(payload)
    await client.get("/assignments", cookies=cookies)  # 觸發 get_or_create
    await _set_role(payload["email"], UserRole.TEACHER)
    return cookies


async def _register(client: AsyncClient, payload: dict) -> dict:
    cookies = _cookies(payload)
    await client.get("/users/me", cookies=cookies)
    return cookies


async def _make_class(client: AsyncClient, cookies: dict) -> str:
    return (
        await client.post("/classes", json={"name": "班"}, cookies=cookies)
    ).json()["id"]


async def _make_assignment(client: AsyncClient, cookies: dict, class_id: str) -> str:
    return (
        await client.post(
            "/assignments",
            json={"class_id": class_id, "title": "作業一", "description": "說明"},
            cookies=cookies,
        )
    ).json()["id"]


# === CRUD + 授權 ===

async def test_create_and_get(client: AsyncClient):
    t = await _as_teacher(client, TEACHER)
    cid = await _make_class(client, t)
    resp = await client.post(
        "/assignments",
        json={"class_id": cid, "title": "作業一", "due_at": "2026-08-01T00:00:00Z"},
        cookies=t,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "作業一"
    assert body["due_at"] is not None
    got = await client.get(f"/assignments/{body['id']}", cookies=t)
    assert got.status_code == 200


async def test_create_on_foreign_class_404(client: AsyncClient):
    t1 = await _as_teacher(client, TEACHER)
    cid = await _make_class(client, t1)
    t2 = await _as_teacher(client, TEACHER2)
    resp = await client.post(
        "/assignments", json={"class_id": cid, "title": "x"}, cookies=t2
    )
    assert resp.status_code == 404


async def test_student_cannot_create(client: AsyncClient):
    t = await _as_teacher(client, TEACHER)
    cid = await _make_class(client, t)
    s = await _register(client, STUDENT)
    resp = await client.post(
        "/assignments", json={"class_id": cid, "title": "x"}, cookies=s
    )
    assert resp.status_code == 403


async def test_list_filtered_by_class(client: AsyncClient):
    t = await _as_teacher(client, TEACHER)
    c1, c2 = await _make_class(client, t), await _make_class(client, t)
    await _make_assignment(client, t, c1)
    rows = (await client.get(f"/assignments?class_id={c1}", cookies=t)).json()
    assert len(rows) == 1
    assert (await client.get(f"/assignments?class_id={c2}", cookies=t)).json() == []


async def test_patch_edits_title_and_due_at(client: AsyncClient):
    t = await _as_teacher(client, TEACHER)
    cid = await _make_class(client, t)
    aid = (
        await client.post(
            "/assignments",
            json={"class_id": cid, "title": "舊", "due_at": "2026-08-01T00:00:00Z"},
            cookies=t,
        )
    ).json()["id"]
    # 改標題 + 改截止時間
    r = await client.patch(
        f"/assignments/{aid}",
        json={"title": "新", "due_at": "2026-09-01T00:00:00Z"},
        cookies=t,
    )
    assert r.status_code == 200
    assert r.json()["title"] == "新"
    assert r.json()["due_at"].startswith("2026-09-01")


async def test_patch_can_clear_due_at(client: AsyncClient):
    t = await _as_teacher(client, TEACHER)
    cid = await _make_class(client, t)
    aid = (
        await client.post(
            "/assignments",
            json={"class_id": cid, "title": "t", "due_at": "2026-08-01T00:00:00Z"},
            cookies=t,
        )
    ).json()["id"]
    r = await client.patch(f"/assignments/{aid}", json={"due_at": None}, cookies=t)
    assert r.json()["due_at"] is None


async def test_patch_without_due_at_keeps_it(client: AsyncClient):
    t = await _as_teacher(client, TEACHER)
    cid = await _make_class(client, t)
    aid = (
        await client.post(
            "/assignments",
            json={"class_id": cid, "title": "t", "due_at": "2026-08-01T00:00:00Z"},
            cookies=t,
        )
    ).json()["id"]
    r = await client.patch(f"/assignments/{aid}", json={"title": "改標題"}, cookies=t)
    assert r.json()["due_at"] is not None  # 未提供 due_at → 保留


async def test_delete_assignment(client: AsyncClient):
    t = await _as_teacher(client, TEACHER)
    cid = await _make_class(client, t)
    aid = await _make_assignment(client, t, cid)
    assert (await client.delete(f"/assignments/{aid}", cookies=t)).status_code == 204
    assert (await client.get(f"/assignments/{aid}", cookies=t)).status_code == 404


# === 附件 ===

def test_validate_upload_rejects_bad_type():
    with pytest.raises(AppError) as e:
        validate_upload("virus.exe", 100)
    assert e.value.status_code == 415


def test_validate_upload_rejects_oversize():
    with pytest.raises(AppError) as e:
        validate_upload("big.pdf", MAX_ATTACHMENT_BYTES + 1)
    assert e.value.status_code == 413


def test_validate_upload_rejects_empty():
    with pytest.raises(AppError) as e:
        validate_upload("empty.pdf", 0)
    assert e.value.status_code == 422


async def _upload(client, cookies, aid, name, data, ctype):
    return await client.post(
        f"/assignments/{aid}/attachments",
        files={"file": (name, data, ctype)},
        cookies=cookies,
    )


async def test_upload_valid_and_download(client: AsyncClient):
    t = await _as_teacher(client, TEACHER)
    cid = await _make_class(client, t)
    aid = await _make_assignment(client, t, cid)
    up = await _upload(client, t, aid, "教材.pdf", b"%PDF-1.4 data", "application/pdf")
    assert up.status_code == 201
    att = up.json()
    assert att["filename"] == "教材.pdf"
    assert att["size_bytes"] == len(b"%PDF-1.4 data")
    # 教師下載
    dl = await client.get(f"/attachments/{att['id']}", cookies=t)
    assert dl.status_code == 200
    assert dl.content == b"%PDF-1.4 data"
    assert "attachment" in dl.headers["content-disposition"]


async def test_detail_lists_attachments(client: AsyncClient):
    t = await _as_teacher(client, TEACHER)
    cid = await _make_class(client, t)
    aid = await _make_assignment(client, t, cid)
    await _upload(client, t, aid, "a.pdf", b"data", "application/pdf")
    await _upload(client, t, aid, "b.txt", b"hello", "text/plain")
    detail = (await client.get(f"/assignments/{aid}", cookies=t)).json()
    names = {a["filename"] for a in detail["attachments"]}
    assert names == {"a.pdf", "b.txt"}


async def test_upload_bad_type_rejected(client: AsyncClient):
    t = await _as_teacher(client, TEACHER)
    cid = await _make_class(client, t)
    aid = await _make_assignment(client, t, cid)
    up = await _upload(client, t, aid, "x.exe", b"MZ", "application/octet-stream")
    assert up.status_code == 415


async def test_class_member_can_download_but_outsider_cannot(client: AsyncClient):
    t = await _as_teacher(client, TEACHER)
    cid = await _make_class(client, t)
    aid = await _make_assignment(client, t, cid)
    att = (
        await _upload(client, t, aid, "m.pdf", b"data", "application/pdf")
    ).json()

    # 學生（班級成員）
    s = await _register(client, STUDENT)
    async with TestSessionFactory() as db:
        db.add(ClassMember(class_id=uuid.UUID(cid), user_id=await _uid(STUDENT["email"])))
        await db.commit()
    assert (await client.get(f"/attachments/{att['id']}", cookies=s)).status_code == 200

    # 非成員
    o = await _register(client, OUTSIDER)
    assert (await client.get(f"/attachments/{att['id']}", cookies=o)).status_code == 403


async def test_delete_attachment(client: AsyncClient):
    t = await _as_teacher(client, TEACHER)
    cid = await _make_class(client, t)
    aid = await _make_assignment(client, t, cid)
    att = (await _upload(client, t, aid, "d.pdf", b"data", "application/pdf")).json()
    assert (
        await client.delete(f"/attachments/{att['id']}", cookies=t)
    ).status_code == 204
    assert (await client.get(f"/attachments/{att['id']}", cookies=t)).status_code == 404
