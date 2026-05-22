"""Phase 6-2b 單元 + 整合測試：batch generator + staging upsert + promote。

涵蓋：
- 成功路徑：retrieve chunks → generate → 寫入 staging
- retry 機制：transient error 退避重試
- 非 retryable error 直接拋
- needs_more_source 聚合（任一 section flag → row 標 True）
- skip_existing 跳過已 approved
- list_target_concepts 過濾課程介紹 + 缺 video_order
- promote_concept：approved 才推；否則拋對應 AppError
- UPSERT：重生覆蓋、reviewed_at reset
"""

from __future__ import annotations

import uuid
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from core.errors import AppError
from models.concept import Concept
from models.learning import LearningPath, LearningUnit, LearningUnitStatus
from models.unit_content_staging import StagingStatus, UnitContentStaging
from models.user import User
from services.learning.batch_generator import (
    MAX_RETRIES,
    _aggregate_needs_more_source,
    _flatten_notes,
    _generate_with_retry,
    generate_all,
    generate_for_concept,
    list_target_concepts,
)
from services.learning.content_generator import (
    CodeExamples,
    ConceptExplanation,
    Summary,
    UnitContent,
)
from services.learning.unit_content_promote import promote_concept
from services.rag.retrieve import RetrievedChunk
from tests.helpers import TestSessionFactory


# === 測試用 builders ===


def _good_unit_content() -> UnitContent:
    return UnitContent(
        concept_explanation=ConceptExplanation(
            needs_more_source=False,
            reason="",
            markdown="說明 [00:01]。",
            citations=[],
        ),
        code_examples=CodeExamples(needs_more_source=False, reason="", examples=[]),
        summary=Summary(
            needs_more_source=False, reason="", key_points=["a", "b", "c"],
        ),
    )


def _partial_needs_more_unit_content() -> UnitContent:
    return UnitContent(
        concept_explanation=ConceptExplanation(
            needs_more_source=False, reason="", markdown="x", citations=[],
        ),
        code_examples=CodeExamples(
            needs_more_source=True, reason="字幕無程式碼", examples=[],
        ),
        summary=Summary(
            needs_more_source=False, reason="", key_points=["a", "b", "c"],
        ),
    )


@contextmanager
def patched_generate(side_effect):
    """Patch generate_unit_content；side_effect 可為 UnitContent / Exception / list。"""
    with patch(
        "services.learning.batch_generator.generate_unit_content",
        new=AsyncMock(side_effect=side_effect),
    ) as m:
        yield m


@contextmanager
def patched_chunks(chunks: list[RetrievedChunk]):
    with patch(
        "services.learning.batch_generator.get_chunks_by_video_order",
        new=AsyncMock(return_value=chunks),
    ) as m:
        yield m


def _fake_chunks() -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            text="[00:01] 字幕內容",
            score=1.0,
            doc_id="d1",
            metadata={"video_order": 47},
        ),
    ]


async def _seed_concept(
    *,
    tag: str = "cpp-47-recursion",
    category: str = "函式",
    video_order: int | None = 47,
) -> uuid.UUID:
    async with TestSessionFactory() as db:
        c = Concept(
            tag=tag,
            name_zh=tag,
            name_en=tag,
            description="",
            difficulty_level=3,
            category=category,
            video_order=video_order,
        )
        db.add(c)
        await db.commit()
        await db.refresh(c)
        return c.id


async def _seed_user_path_unit(concept_id: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID]:
    """建一個 user + path + unit 用於 promote 測試。"""
    async with TestSessionFactory() as db:
        u = User(
            email=f"u-{uuid.uuid4().hex[:8]}@t.com",
            name="x",
            google_id=f"g-{uuid.uuid4().hex[:8]}",
        )
        db.add(u)
        await db.flush()
        path = LearningPath(user_id=u.id, title="t")
        db.add(path)
        await db.flush()
        unit = LearningUnit(
            path_id=path.id,
            concept_id=concept_id,
            order_index=0,
            content={},
            status=LearningUnitStatus.AVAILABLE.value,
        )
        db.add(unit)
        await db.commit()
        return path.id, unit.id


# === pure helpers ===


def test_aggregate_needs_more_source_any_section():
    assert _aggregate_needs_more_source(_good_unit_content()) is False
    assert _aggregate_needs_more_source(_partial_needs_more_unit_content()) is True


def test_flatten_notes_only_failing_sections():
    notes = _flatten_notes(_partial_needs_more_unit_content())
    assert "examples" in notes
    assert "字幕無程式碼" in notes
    assert "concept" not in notes
    assert "summary" not in notes


def test_flatten_notes_empty_when_all_good():
    assert _flatten_notes(_good_unit_content()) == ""


# === retry 機制 ===


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt():
    """第一次 LLM_UNAVAILABLE → 第二次成功。"""
    transient = AppError(503, "LLM_UNAVAILABLE", "boom")
    with patched_generate([transient, _good_unit_content()]):
        concept = Concept(
            tag="x", name_zh="x", name_en="x", description="",
            difficulty_level=1, category="x", video_order=1,
        )
        content, attempt = await _generate_with_retry(concept, _fake_chunks())
    assert attempt == 2
    assert content.summary.key_points == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_retry_exhausts_then_raises():
    """連 max_retries 次 transient → 最後一次直接 raise（不再退避）。"""
    transient = AppError(502, "LLM_PARSE_ERROR", "bad json")
    with patched_generate([transient] * MAX_RETRIES):
        concept = Concept(
            tag="x", name_zh="x", name_en="x", description="",
            difficulty_level=1, category="x", video_order=1,
        )
        with pytest.raises(AppError) as exc:
            await _generate_with_retry(concept, _fake_chunks())
    assert exc.value.error == "LLM_PARSE_ERROR"


@pytest.mark.asyncio
async def test_non_retryable_error_does_not_retry():
    """非 LLM_UNAVAILABLE/LLM_PARSE_ERROR 的 AppError 直接拋（不退避）。"""
    fatal = AppError(500, "INTERNAL_ERROR", "fatal")
    mock = AsyncMock(side_effect=[fatal, _good_unit_content()])
    with patch(
        "services.learning.batch_generator.generate_unit_content", new=mock,
    ):
        concept = Concept(
            tag="x", name_zh="x", name_en="x", description="",
            difficulty_level=1, category="x", video_order=1,
        )
        with pytest.raises(AppError) as exc:
            await _generate_with_retry(concept, _fake_chunks())
    assert exc.value.error == "INTERNAL_ERROR"
    # 第一次失敗就拋，不應呼叫第二次
    assert mock.call_count == 1


# === generate_for_concept（含 staging 寫入）===


@pytest.mark.asyncio
async def test_generate_for_concept_writes_staging():
    cid = await _seed_concept()
    with patched_chunks(_fake_chunks()), patched_generate([_good_unit_content()]):
        async with TestSessionFactory() as db:
            concept = (
                await db.execute(select(Concept).where(Concept.id == cid))
            ).scalar_one()
            result = await generate_for_concept(db, concept)

    assert result.success is True
    assert result.needs_more_source is False
    assert result.attempt_count == 1
    assert result.chunks_count == 1

    async with TestSessionFactory() as db:
        row = (
            await db.execute(
                select(UnitContentStaging).where(
                    UnitContentStaging.concept_id == cid
                )
            )
        ).scalar_one()
    assert row.status == StagingStatus.PENDING.value
    assert row.needs_more_source is False
    assert row.content["summary"]["key_points"] == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_generate_for_concept_failure_returns_result_no_staging():
    """LLM 失敗應回 success=False，不寫 staging。"""
    cid = await _seed_concept(tag="cpp-48")
    fatal = AppError(503, "LLM_UNAVAILABLE", "down")
    with patched_chunks(_fake_chunks()), patched_generate([fatal] * MAX_RETRIES):
        async with TestSessionFactory() as db:
            concept = (
                await db.execute(select(Concept).where(Concept.id == cid))
            ).scalar_one()
            result = await generate_for_concept(db, concept)

    assert result.success is False
    assert "LLM_UNAVAILABLE" in (result.error or "")

    async with TestSessionFactory() as db:
        row = (
            await db.execute(
                select(UnitContentStaging).where(
                    UnitContentStaging.concept_id == cid
                )
            )
        ).scalar_one_or_none()
    assert row is None


@pytest.mark.asyncio
async def test_generate_for_concept_no_video_order_raises_422():
    cid = await _seed_concept(tag="cpp-no-video", video_order=None)
    async with TestSessionFactory() as db:
        concept = (
            await db.execute(select(Concept).where(Concept.id == cid))
        ).scalar_one()
        with pytest.raises(AppError) as exc:
            await generate_for_concept(db, concept)
    assert exc.value.status_code == 422
    assert exc.value.error == "NO_VIDEO_ORDER"


@pytest.mark.asyncio
async def test_generate_partial_needs_more_source_aggregated_to_row():
    cid = await _seed_concept(tag="cpp-49")
    with patched_chunks(_fake_chunks()), patched_generate(
        [_partial_needs_more_unit_content()]
    ):
        async with TestSessionFactory() as db:
            concept = (
                await db.execute(select(Concept).where(Concept.id == cid))
            ).scalar_one()
            await generate_for_concept(db, concept)

    async with TestSessionFactory() as db:
        row = (
            await db.execute(
                select(UnitContentStaging).where(
                    UnitContentStaging.concept_id == cid
                )
            )
        ).scalar_one()
    assert row.needs_more_source is True
    assert "字幕無程式碼" in row.notes


@pytest.mark.asyncio
async def test_upsert_overwrites_existing_resets_review():
    """已有 staging row（approved + reviewed_at）→ 重生時 reset 為 pending + reviewed_at=NULL。"""
    cid = await _seed_concept(tag="cpp-50")
    # 先放一個 approved + reviewed
    async with TestSessionFactory() as db:
        from datetime import datetime, timezone
        existing = UnitContentStaging(
            concept_id=cid, content={"old": True},
            status=StagingStatus.APPROVED.value,
            reviewed_at=datetime.now(timezone.utc),
        )
        db.add(existing)
        await db.commit()

    with patched_chunks(_fake_chunks()), patched_generate([_good_unit_content()]):
        async with TestSessionFactory() as db:
            concept = (
                await db.execute(select(Concept).where(Concept.id == cid))
            ).scalar_one()
            # 顯式不 skip → 強制重生
            await generate_for_concept(db, concept)

    async with TestSessionFactory() as db:
        row = (
            await db.execute(
                select(UnitContentStaging).where(
                    UnitContentStaging.concept_id == cid
                )
            )
        ).scalar_one()
    assert row.status == StagingStatus.PENDING.value
    assert row.reviewed_at is None
    assert "old" not in row.content


# === list_target_concepts / generate_all 過濾邏輯 ===


@pytest.mark.asyncio
async def test_list_target_concepts_includes_intro_filters_no_video_order():
    """2026-05-22 反轉：課程介紹也應生成（已加 PREREQUISITE 邊 1→2→3→4 入路徑）。

    過濾條件只剩「video_order 必須有值」。
    """
    await _seed_concept(tag="cpp-04", video_order=4, category="基礎語法")
    await _seed_concept(tag="cpp-01-intro", video_order=1, category="課程介紹")
    await _seed_concept(tag="cpp-no-video", video_order=None, category="基礎語法")

    async with TestSessionFactory() as db:
        targets = await list_target_concepts(db)

    tags = [c.tag for c in targets]
    assert "cpp-04" in tags
    assert "cpp-01-intro" in tags
    assert "cpp-no-video" not in tags


@pytest.mark.asyncio
async def test_list_target_concepts_only_filter():
    await _seed_concept(tag="cpp-04", video_order=4, category="基礎語法")
    await _seed_concept(tag="cpp-05", video_order=5, category="基礎語法")

    async with TestSessionFactory() as db:
        targets = await list_target_concepts(db, only=5)

    assert len(targets) == 1
    assert targets[0].tag == "cpp-05"


@pytest.mark.asyncio
async def test_generate_all_skips_approved_when_default():
    cid = await _seed_concept(tag="cpp-04", video_order=4)
    async with TestSessionFactory() as db:
        db.add(
            UnitContentStaging(
                concept_id=cid,
                content={"old": True},
                status=StagingStatus.APPROVED.value,
            )
        )
        await db.commit()

    with patched_chunks(_fake_chunks()), patched_generate([_good_unit_content()]) as gen:
        async with TestSessionFactory() as db:
            results = await generate_all(db, skip_existing=True)

    assert len(results) == 1
    assert results[0].error == "SKIPPED_APPROVED"
    gen.assert_not_called()


@pytest.mark.asyncio
async def test_generate_all_force_regenerates_approved():
    cid = await _seed_concept(tag="cpp-04", video_order=4)
    async with TestSessionFactory() as db:
        db.add(
            UnitContentStaging(
                concept_id=cid,
                content={"old": True},
                status=StagingStatus.APPROVED.value,
            )
        )
        await db.commit()

    with patched_chunks(_fake_chunks()), patched_generate([_good_unit_content()]):
        async with TestSessionFactory() as db:
            results = await generate_all(db, skip_existing=False)

    assert results[0].success is True
    async with TestSessionFactory() as db:
        row = (
            await db.execute(
                select(UnitContentStaging).where(
                    UnitContentStaging.concept_id == cid
                )
            )
        ).scalar_one()
    assert row.status == StagingStatus.PENDING.value
    assert "old" not in row.content


# === promote_concept ===


@pytest.mark.asyncio
async def test_promote_concept_writes_to_units():
    cid = await _seed_concept(tag="cpp-04")
    _, unit_id = await _seed_user_path_unit(cid)

    async with TestSessionFactory() as db:
        db.add(
            UnitContentStaging(
                concept_id=cid,
                content={"summary": {"key_points": ["a"]}},
                status=StagingStatus.APPROVED.value,
            )
        )
        await db.commit()

    async with TestSessionFactory() as db:
        affected = await promote_concept(db, cid)

    assert affected == 1
    async with TestSessionFactory() as db:
        unit = (
            await db.execute(
                select(LearningUnit).where(LearningUnit.id == unit_id)
            )
        ).scalar_one()
    assert unit.content == {"summary": {"key_points": ["a"]}}


@pytest.mark.asyncio
async def test_promote_concept_pending_raises_422():
    cid = await _seed_concept(tag="cpp-04")
    async with TestSessionFactory() as db:
        db.add(
            UnitContentStaging(
                concept_id=cid,
                content={"x": 1},
                status=StagingStatus.PENDING.value,
            )
        )
        await db.commit()

    async with TestSessionFactory() as db:
        with pytest.raises(AppError) as exc:
            await promote_concept(db, cid)
    assert exc.value.status_code == 422
    assert exc.value.error == "STAGING_NOT_APPROVED"


@pytest.mark.asyncio
async def test_promote_concept_missing_raises_404():
    async with TestSessionFactory() as db:
        with pytest.raises(AppError) as exc:
            await promote_concept(db, uuid.uuid4())
    assert exc.value.status_code == 404
    assert exc.value.error == "STAGING_NOT_FOUND"
