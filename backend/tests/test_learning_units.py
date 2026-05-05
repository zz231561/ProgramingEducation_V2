"""學習單元狀態 service + HTTP 整合測試（roadmap 3-1d）。

涵蓋：
- update_unit_status：合法 transition / 非法 transition / 完成解鎖下一單元 / 跨使用者
- HTTP 401 / 422 (locked / 非 enum) / 404 / 200 + 解鎖
- revisit (in_progress → available) 清空 completed_at
- 最後一個 unit 完成 → next_unlocked_unit=None
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.errors import AppError
from models.concept import Concept
from models.learning import LearningPath, LearningUnit, LearningUnitStatus
from models.user import User
from services.learning import update_unit_status
from tests.helpers import TestSessionFactory, encrypt_test_token

OWNER = {
    "sub": "unit-owner",
    "email": "unit-owner@test.com",
    "name": "Unit Owner",
    "googleId": "g-unit-owner",
}
OTHER = {
    "sub": "unit-other",
    "email": "unit-other@test.com",
    "name": "Unit Other",
    "googleId": "g-unit-other",
}


async def _seed_path_with_units(
    user_payload: dict, count: int, client: AsyncClient
) -> tuple[uuid.UUID, list[uuid.UUID]]:
    """建立 user + path + count 個 unit。第 1 個 available，其餘 locked。回 (user_id, [unit_ids])。"""
    token = encrypt_test_token(user_payload)
    await client.get("/auth/me", cookies={"authjs.session-token": token})

    async with TestSessionFactory() as db:
        user = (
            await db.execute(select(User).where(User.google_id == user_payload["googleId"]))
        ).scalar_one()
        # 建 count 個 concept
        concept_ids: list[uuid.UUID] = []
        for i in range(count):
            c = Concept(
                tag=f"u-{uuid.uuid4().hex[:8]}",
                name_zh=f"概念{i}",
                name_en="x",
                description="",
                difficulty_level=1,
                category="基礎",
            )
            db.add(c)
            await db.flush()
            concept_ids.append(c.id)

        path = LearningPath(user_id=user.id, title="P")
        db.add(path)
        await db.flush()

        unit_ids: list[uuid.UUID] = []
        for i, cid in enumerate(concept_ids):
            unit = LearningUnit(
                path_id=path.id, concept_id=cid, order_index=i, content={},
                status=(
                    LearningUnitStatus.AVAILABLE.value if i == 0
                    else LearningUnitStatus.LOCKED.value
                ),
            )
            db.add(unit)
            await db.flush()
            unit_ids.append(unit.id)
        await db.commit()
        return user.id, unit_ids


# === Service unit tests ===


@pytest.mark.asyncio
async def test_available_to_in_progress(client: AsyncClient):
    user_id, [u0, _] = await _seed_path_with_units(OWNER, 2, client)
    async with TestSessionFactory() as db:
        unit, nxt = await update_unit_status(
            db, user_id, u0, LearningUnitStatus.IN_PROGRESS
        )
    assert unit.status == "in_progress"
    assert nxt is None  # 只是 in_progress 不解鎖下一個


@pytest.mark.asyncio
async def test_completed_unlocks_next(client: AsyncClient):
    user_id, [u0, u1] = await _seed_path_with_units(OWNER, 2, client)
    async with TestSessionFactory() as db:
        await update_unit_status(db, user_id, u0, LearningUnitStatus.IN_PROGRESS)
        unit, nxt = await update_unit_status(
            db, user_id, u0, LearningUnitStatus.COMPLETED
        )
    assert unit.status == "completed"
    assert unit.completed_at is not None
    assert nxt is not None
    assert nxt.id == u1
    assert nxt.status == "available"


@pytest.mark.asyncio
async def test_completed_last_unit_no_next(client: AsyncClient):
    user_id, [u0] = await _seed_path_with_units(OWNER, 1, client)
    async with TestSessionFactory() as db:
        await update_unit_status(db, user_id, u0, LearningUnitStatus.IN_PROGRESS)
        _, nxt = await update_unit_status(db, user_id, u0, LearningUnitStatus.COMPLETED)
    assert nxt is None


@pytest.mark.asyncio
async def test_locked_to_in_progress_rejected(client: AsyncClient):
    user_id, [_, u1] = await _seed_path_with_units(OWNER, 2, client)
    async with TestSessionFactory() as db:
        with pytest.raises(AppError) as exc:
            await update_unit_status(db, user_id, u1, LearningUnitStatus.IN_PROGRESS)
    assert exc.value.status_code == 422
    assert exc.value.error == "LEARNING_UNIT_INVALID_TRANSITION"


@pytest.mark.asyncio
async def test_completed_to_available_rejected(client: AsyncClient):
    """已完成的單元不可重置（避免精熟度反覆波動）。"""
    user_id, [u0] = await _seed_path_with_units(OWNER, 1, client)
    async with TestSessionFactory() as db:
        await update_unit_status(db, user_id, u0, LearningUnitStatus.IN_PROGRESS)
        await update_unit_status(db, user_id, u0, LearningUnitStatus.COMPLETED)
        with pytest.raises(AppError) as exc:
            await update_unit_status(db, user_id, u0, LearningUnitStatus.AVAILABLE)
    assert exc.value.error == "LEARNING_UNIT_INVALID_TRANSITION"


@pytest.mark.asyncio
async def test_revisit_clears_completed_at(client: AsyncClient):
    """in_progress → available（revisit 重置）→ completed_at 應清空（雖無此欄位變動但邏輯保險）。"""
    user_id, [u0] = await _seed_path_with_units(OWNER, 1, client)
    async with TestSessionFactory() as db:
        await update_unit_status(db, user_id, u0, LearningUnitStatus.IN_PROGRESS)
        # in_progress → available 是合法（revisit）
        unit, _ = await update_unit_status(db, user_id, u0, LearningUnitStatus.AVAILABLE)
    assert unit.status == "available"
    assert unit.completed_at is None


@pytest.mark.asyncio
async def test_other_user_returns_404(client: AsyncClient):
    user_id_owner, [u0] = await _seed_path_with_units(OWNER, 1, client)
    other_id, _ = await _seed_path_with_units(OTHER, 1, client)
    async with TestSessionFactory() as db:
        with pytest.raises(AppError) as exc:
            await update_unit_status(db, other_id, u0, LearningUnitStatus.IN_PROGRESS)
    assert exc.value.status_code == 404
    assert exc.value.error == "LEARNING_UNIT_NOT_FOUND"


# === HTTP integration ===


async def test_patch_unit_requires_auth(client: AsyncClient):
    resp = await client.patch(
        f"/learning/units/{uuid.uuid4()}",
        json={"status": "in_progress"},
    )
    assert resp.status_code == 401


async def test_patch_unit_invalid_status_string(client: AsyncClient):
    _, [u0] = await _seed_path_with_units(OWNER, 1, client)
    token = encrypt_test_token(OWNER)
    resp = await client.patch(
        f"/learning/units/{u0}",
        json={"status": "rocket"},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "INVALID_UNIT_STATUS"


async def test_patch_unit_locked_rejected(client: AsyncClient):
    """使用者不可手動 set 'locked'（系統管理狀態）。"""
    _, [u0] = await _seed_path_with_units(OWNER, 1, client)
    token = encrypt_test_token(OWNER)
    resp = await client.patch(
        f"/learning/units/{u0}",
        json={"status": "locked"},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "INVALID_UNIT_STATUS"


async def test_patch_unit_completed_returns_next_unlocked(client: AsyncClient):
    _, [u0, u1] = await _seed_path_with_units(OWNER, 2, client)
    token = encrypt_test_token(OWNER)

    # available → in_progress
    await client.patch(
        f"/learning/units/{u0}",
        json={"status": "in_progress"},
        cookies={"authjs.session-token": token},
    )
    # in_progress → completed
    resp = await client.patch(
        f"/learning/units/{u0}",
        json={"status": "completed"},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["unit"]["status"] == "completed"
    assert body["unit"]["completed_at"] is not None
    assert body["next_unlocked_unit"] is not None
    assert body["next_unlocked_unit"]["id"] == str(u1)
    assert body["next_unlocked_unit"]["status"] == "available"


async def test_patch_unit_invalid_transition(client: AsyncClient):
    """locked unit 直接 set in_progress → 422 LEARNING_UNIT_INVALID_TRANSITION。"""
    _, [_, u1] = await _seed_path_with_units(OWNER, 2, client)
    token = encrypt_test_token(OWNER)
    resp = await client.patch(
        f"/learning/units/{u1}",
        json={"status": "in_progress"},
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "LEARNING_UNIT_INVALID_TRANSITION"


async def test_patch_unit_other_user_returns_404(client: AsyncClient):
    _, [u0] = await _seed_path_with_units(OWNER, 1, client)
    other_token = encrypt_test_token(OTHER)
    await client.get("/auth/me", cookies={"authjs.session-token": other_token})
    resp = await client.patch(
        f"/learning/units/{u0}",
        json={"status": "in_progress"},
        cookies={"authjs.session-token": other_token},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "LEARNING_UNIT_NOT_FOUND"
