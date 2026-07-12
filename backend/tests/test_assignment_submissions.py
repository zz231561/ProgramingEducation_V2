"""作業繳交 API 測試（5-5b）— 學生繳交 + 教師交件檢視/評分。"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from models.classroom import ClassMember
from models.user import User, UserRole
from tests.helpers import TestSessionFactory, encrypt_test_token

TEACHER = {"sub": "st", "email": "st@ex.com", "name": "ST", "googleId": "g-st"}
STUDENT = {"sub": "ss", "email": "ss@ex.com", "name": "SS", "googleId": "g-ss"}
OUTSIDER = {"sub": "so", "email": "so@ex.com", "name": "SO", "googleId": "g-so"}
_COOKIE = "authjs.session-token"


def _ck(p: dict) -> dict:
    return {_COOKIE: encrypt_test_token(p)}


async def _uid(email: str) -> uuid.UUID:
    async with TestSessionFactory() as db:
        return (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one().id


async def _as_teacher(client: AsyncClient) -> dict:
    ck = _ck(TEACHER)
    await client.get("/assignments", cookies=ck)
    async with TestSessionFactory() as db:
        u = (
            await db.execute(select(User).where(User.email == TEACHER["email"]))
        ).scalar_one()
        u.role = UserRole.TEACHER
        await db.commit()
    return ck


async def _register(client: AsyncClient, p: dict) -> dict:
    ck = _ck(p)
    await client.get("/users/me", cookies=ck)
    return ck


async def _add_member(class_id: str, email: str) -> None:
    async with TestSessionFactory() as db:
        db.add(ClassMember(class_id=uuid.UUID(class_id), user_id=await _uid(email)))
        await db.commit()


async def _setup(client: AsyncClient) -> tuple[dict, dict, str, str]:
    """建立教師+班級+作業，學生入班。回傳 (teacher_ck, student_ck, class_id, assignment_id)。"""
    t = await _as_teacher(client)
    cid = (await client.post("/classes", json={"name": "班"}, cookies=t)).json()["id"]
    aid = (
        await client.post(
            "/assignments",
            json={"class_id": cid, "title": "作業一", "description": "說明"},
            cookies=t,
        )
    ).json()["id"]
    s = await _register(client, STUDENT)
    await _add_member(cid, STUDENT["email"])
    return t, s, cid, aid


# === 學生列表/詳情 ===

async def test_student_sees_assignment_in_their_class(client: AsyncClient):
    _t, s, _cid, aid = await _setup(client)
    rows = (await client.get("/assignments/mine", cookies=s)).json()
    assert len(rows) == 1
    assert rows[0]["id"] == aid
    assert rows[0]["submission"] is None


async def test_outsider_cannot_see_detail(client: AsyncClient):
    _t, _s, _cid, aid = await _setup(client)
    o = await _register(client, OUTSIDER)
    resp = await client.get(f"/assignments/mine/{aid}", cookies=o)
    assert resp.status_code == 404


# === 繳交（upsert）===

async def test_submit_creates_then_updates(client: AsyncClient):
    _t, s, _cid, aid = await _setup(client)
    r1 = await client.put(
        f"/assignments/{aid}/submission", json={"text": "初稿"}, cookies=s
    )
    assert r1.status_code == 200
    sid = r1.json()["id"]
    assert r1.json()["text"] == "初稿"
    # 重繳覆蓋，同一份
    r2 = await client.put(
        f"/assignments/{aid}/submission", json={"text": "改稿"}, cookies=s
    )
    assert r2.json()["id"] == sid
    assert r2.json()["text"] == "改稿"


async def test_submit_and_upload_attachment_and_download(client: AsyncClient):
    _t, s, _cid, aid = await _setup(client)
    sid = (
        await client.put(
            f"/assignments/{aid}/submission", json={"text": "x"}, cookies=s
        )
    ).json()["id"]
    up = await client.post(
        f"/submissions/{sid}/attachments",
        files={"file": ("hw.pdf", b"mydata", "application/pdf")},
        cookies=s,
    )
    assert up.status_code == 201
    att_id = up.json()["id"]
    # 學生下載自己的繳交附件
    dl = await client.get(f"/attachments/{att_id}", cookies=s)
    assert dl.status_code == 200 and dl.content == b"mydata"
    # 詳情帶出繳交附件
    detail = (await client.get(f"/assignments/mine/{aid}", cookies=s)).json()
    assert detail["submission_attachments"][0]["filename"] == "hw.pdf"
    # 學生刪自己的繳交附件
    assert (await client.delete(f"/attachments/{att_id}", cookies=s)).status_code == 204


# === 教師交件檢視 + 評分 ===

async def test_teacher_lists_submissions_with_status(client: AsyncClient):
    t, s, _cid, aid = await _setup(client)
    await client.put(f"/assignments/{aid}/submission", json={"text": "done"}, cookies=s)
    rows = (await client.get(f"/assignments/{aid}/submissions", cookies=t)).json()
    assert len(rows) == 1  # 名冊 1 位學生
    assert rows[0]["submission"]["text"] == "done"


async def test_teacher_list_includes_submission_attachments(client: AsyncClient):
    t, s, _cid, aid = await _setup(client)
    sid = (
        await client.put(
            f"/assignments/{aid}/submission", json={"text": "x"}, cookies=s
        )
    ).json()["id"]
    await client.post(
        f"/submissions/{sid}/attachments",
        files={"file": ("hw.pdf", b"mydata", "application/pdf")},
        cookies=s,
    )
    rows = (await client.get(f"/assignments/{aid}/submissions", cookies=t)).json()
    assert rows[0]["attachments"][0]["filename"] == "hw.pdf"
    # 教師可下載學生繳交附件
    att_id = rows[0]["attachments"][0]["id"]
    dl = await client.get(f"/attachments/{att_id}", cookies=t)
    assert dl.status_code == 200 and dl.content == b"mydata"


async def test_teacher_grades_submission(client: AsyncClient):
    t, s, _cid, aid = await _setup(client)
    sid = (
        await client.put(
            f"/assignments/{aid}/submission", json={"text": "done"}, cookies=s
        )
    ).json()["id"]
    r = await client.patch(
        f"/submissions/{sid}/grade",
        json={"score": 90, "feedback": "很好"},
        cookies=t,
    )
    assert r.status_code == 200
    assert r.json()["score"] == 90
    assert r.json()["feedback"] == "很好"
    assert r.json()["graded_at"] is not None


async def test_student_cannot_grade(client: AsyncClient):
    _t, s, _cid, aid = await _setup(client)
    sid = (
        await client.put(
            f"/assignments/{aid}/submission", json={"text": "d"}, cookies=s
        )
    ).json()["id"]
    r = await client.patch(
        f"/submissions/{sid}/grade", json={"score": 100, "feedback": "x"}, cookies=s
    )
    assert r.status_code == 403
