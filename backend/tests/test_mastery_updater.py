"""精熟度 BKT 線上更新單元測試。

涵蓋：
- bkt_online_update：correct/incorrect 數學正確性、邊界（prior=0/1）
- update_mastery：lazy create、累計計數、bloom_level 取最大、unknown tag 跳過
"""

import uuid

import pytest

from models.concept import Concept
from models.mastery import StudentMastery
from services.edf.models import BloomLevel, ErrorType, EvidenceResult
from services.mastery import (
    BKT_DEFAULT_PARAMS,
    BKTParams,
    bkt_online_update,
    update_mastery,
)
from tests.helpers import TestSessionFactory


# === BKT 數學 ===

def test_bkt_correct_increases_confidence():
    """答對應提升精熟機率。"""
    new = bkt_online_update(prior=0.5, correct=True)
    assert new > 0.5


def test_bkt_incorrect_decreases_confidence_then_relearn_partial():
    """答錯後 Bayes 後驗會降，但加上 P(T) 重新學習仍可能略升或略降；
    與 prior=0.5 / 預設參數比，應低於僅做 Bayes 但比 0 高。"""
    new = bkt_online_update(prior=0.5, correct=False)
    assert 0.0 < new < 0.5  # 整體下降但仍 >0


def test_bkt_clamped_to_unit_interval():
    for prior in (0.0, 0.5, 1.0):
        for correct in (True, False):
            v = bkt_online_update(prior=prior, correct=correct)
            assert 0.0 <= v <= 1.0


def test_bkt_custom_params_no_slip_no_guess_correct_jumps_high():
    """slip=0, guess=0：答對應給出非常高的後驗（接近 1）。"""
    params = BKTParams(prior=0.3, learn=0.0, slip=0.0, guess=0.0)
    new = bkt_online_update(prior=0.3, correct=True, params=params)
    assert new > 0.99


def test_bkt_default_params_sanity():
    p = BKT_DEFAULT_PARAMS
    assert 0 < p.prior < 1
    assert 0 < p.learn < 1
    assert 0 < p.slip < 0.5  # slip 應遠低於 0.5
    assert 0 < p.guess < 0.5  # 同上


# === update_mastery 整合 ===


def _evidence(error: ErrorType, tags: list[str], bloom: BloomLevel) -> EvidenceResult:
    return EvidenceResult(
        error_type=error,
        error_message="",
        concept_tags=tags,
        bloom_level=bloom,
        bloom_reasoning="",
        code_analysis="",
    )


async def _seed_concepts(tags: list[str]) -> None:
    async with TestSessionFactory() as db:
        for tag in tags:
            db.add(
                Concept(
                    tag=tag,
                    name_zh=tag,
                    name_en=tag,
                    description="",
                    difficulty_level=1,
                    category="基礎語法",
                )
            )
        await db.commit()


@pytest.mark.asyncio
async def test_update_mastery_lazy_creates_row():
    await _seed_concepts(["control-flow"])
    user_id = uuid.uuid4()

    async with TestSessionFactory() as db:
        rows = await update_mastery(
            db, user_id,
            _evidence(ErrorType.NONE, ["control-flow"], BloomLevel.APPLY),
        )
        await db.commit()

    assert len(rows) == 1
    async with TestSessionFactory() as db:
        from sqlalchemy import select
        m = (await db.execute(select(StudentMastery))).scalar_one()
        assert m.exposure_count == 1
        assert m.success_count == 1
        assert m.error_count == 0
        assert m.bloom_level == int(BloomLevel.APPLY)
        assert 0 < m.confidence < 1


@pytest.mark.asyncio
async def test_update_mastery_accumulates_counts_and_max_bloom():
    """同 user × concept 連續互動：counts 累加、bloom 取最大、confidence 變化。"""
    await _seed_concepts(["pointer-arithmetic"])
    user_id = uuid.uuid4()

    async with TestSessionFactory() as db:
        # 第一次：答對 + APPLY
        await update_mastery(
            db, user_id,
            _evidence(ErrorType.NONE, ["pointer-arithmetic"], BloomLevel.APPLY),
        )
        # 第二次：答錯 + ANALYZE（更高 bloom）
        await update_mastery(
            db, user_id,
            _evidence(ErrorType.LOGIC, ["pointer-arithmetic"], BloomLevel.ANALYZE),
        )
        await db.commit()

    async with TestSessionFactory() as db:
        from sqlalchemy import select
        m = (await db.execute(select(StudentMastery))).scalar_one()
        assert m.exposure_count == 2
        assert m.success_count == 1
        assert m.error_count == 1
        # bloom 取最大（ANALYZE > APPLY）
        assert m.bloom_level == int(BloomLevel.ANALYZE)


@pytest.mark.asyncio
async def test_update_mastery_skips_unknown_tag():
    """LLM 產生的 tag 若不在 concepts 表中應跳過，不擲錯。"""
    await _seed_concepts(["control-flow"])
    user_id = uuid.uuid4()

    async with TestSessionFactory() as db:
        rows = await update_mastery(
            db, user_id,
            _evidence(
                ErrorType.NONE,
                ["control-flow", "fictional-concept", "another-fake"],
                BloomLevel.APPLY,
            ),
        )
        await db.commit()

    # 只有 control-flow 被處理
    assert len(rows) == 1
    assert rows[0].concept_id is not None


@pytest.mark.asyncio
async def test_update_mastery_multiple_concepts_in_one_call():
    """單次 evidence 含多個 tag → 各自建立 mastery row。"""
    await _seed_concepts(["control-flow", "function-design"])
    user_id = uuid.uuid4()

    async with TestSessionFactory() as db:
        rows = await update_mastery(
            db, user_id,
            _evidence(
                ErrorType.NONE,
                ["control-flow", "function-design"],
                BloomLevel.APPLY,
            ),
        )
        await db.commit()

    assert len(rows) == 2
    async with TestSessionFactory() as db:
        from sqlalchemy import select
        masteries = (await db.execute(select(StudentMastery))).scalars().all()
        assert len(masteries) == 2


@pytest.mark.asyncio
async def test_update_mastery_empty_concept_tags_returns_empty():
    user_id = uuid.uuid4()
    async with TestSessionFactory() as db:
        rows = await update_mastery(
            db, user_id,
            _evidence(ErrorType.NONE, [], BloomLevel.APPLY),
        )
        await db.commit()
    assert rows == []
