"""補救路徑測試（roadmap K4c）— 復用 test_diagnosis 的圖與作答 seeding。"""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from models.learning import LearningPath, LearningUnit, LearningUnitStatus
from services.learning.remedial import open_remedial_units
from tests.helpers import TestSessionFactory, encrypt_test_token
from tests.test_diagnosis import (
    STUDENT_PAYLOAD,
    _seed_answers,
    _seed_graph_and_user,
)


async def _seed_path_with_units(
    user_id: uuid.UUID, ids: dict, statuses: dict[str, str]
) -> dict[str, uuid.UUID]:
    """為 user 建 path + 指定狀態的 units（order 依 video_order）。"""
    async with TestSessionFactory() as db:
        path = LearningPath(user_id=user_id, title="C++ 完整課程")
        db.add(path)
        await db.flush()
        unit_ids: dict[str, uuid.UUID] = {}
        for order, tag in enumerate(["vars", "cond", "funcs", "recursion"]):
            unit = LearningUnit(
                path_id=path.id,
                concept_id=ids[tag],
                order_index=order,
                content={},
                status=statuses.get(tag, LearningUnitStatus.LOCKED.value),
                completed_at=(
                    datetime(2026, 7, 1, tzinfo=timezone.utc)
                    if statuses.get(tag) == LearningUnitStatus.COMPLETED.value
                    else None
                ),
            )
            db.add(unit)
            await db.flush()
            unit_ids[tag] = unit.id
        await db.commit()
        return unit_ids


# === service 層 ===

@pytest.mark.asyncio
async def test_open_remedial_reopens_completed_and_locked():
    """completed / locked → available（completed_at 清空）；available 不動。"""
    ids = await _seed_graph_and_user()
    await _seed_path_with_units(ids["user_id"], ids, {
        "vars": "available",
        "cond": "locked",
        "funcs": "completed",
    })

    async with TestSessionFactory() as db:
        results = await open_remedial_units(
            db, ids["user_id"], [ids["funcs"], ids["cond"], ids["vars"]]
        )

    by_tag = {r.concept_tag: r for r in results}
    assert by_tag["funcs"].previous_status == "completed"
    assert by_tag["funcs"].status == "available"
    assert by_tag["cond"].previous_status == "locked"
    assert by_tag["cond"].status == "available"
    assert by_tag["vars"].previous_status == "available"
    assert by_tag["vars"].status == "available"

    # order_index 升冪 = 建議學習順序（vars → cond → funcs）
    assert [r.concept_tag for r in results] == ["vars", "cond", "funcs"]

    # completed_at 已清空
    async with TestSessionFactory() as db:
        from sqlalchemy import select
        unit = (
            await db.execute(
                select(LearningUnit).where(LearningUnit.id == by_tag["funcs"].unit_id)
            )
        ).scalar_one()
        assert unit.status == "available"
        assert unit.completed_at is None


@pytest.mark.asyncio
async def test_open_remedial_empty_suspects_noop():
    ids = await _seed_graph_and_user()
    async with TestSessionFactory() as db:
        assert await open_remedial_units(db, ids["user_id"], []) == []


# === API route ===

@pytest.mark.asyncio
async def test_remediate_route_conflict_when_not_triggered(client: AsyncClient):
    """未達連續失敗門檻 → 409 DIAGNOSIS_NOT_TRIGGERED。"""
    ids = await _seed_graph_and_user()
    await _seed_answers(ids["user_id"], "recursion", [False])  # 只失敗 1 次

    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.post(
        "/concepts/recursion/diagnosis/remediate",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "DIAGNOSIS_NOT_TRIGGERED"


@pytest.mark.asyncio
async def test_remediate_route_unknown_tag_404(client: AsyncClient):
    await _seed_graph_and_user()
    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.post(
        "/concepts/no-such/diagnosis/remediate",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_remediate_route_reopens_suspect_units(client: AsyncClient):
    """觸發後：嫌疑概念（funcs/cond/vars 皆盲區）的 units 全部開放。"""
    ids = await _seed_graph_and_user()
    await _seed_answers(ids["user_id"], "recursion", [False, False, False])
    await _seed_path_with_units(ids["user_id"], ids, {
        "vars": "completed",
        "cond": "locked",
        "funcs": "locked",
    })

    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.post(
        "/concepts/recursion/diagnosis/remediate",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["target_tag"] == "recursion"
    tags = [u["concept_tag"] for u in body["remedial_units"]]
    assert tags == ["vars", "cond", "funcs"]
    assert all(u["status"] == "available" for u in body["remedial_units"])
