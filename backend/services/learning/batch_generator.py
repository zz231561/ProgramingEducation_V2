"""Phase 6-2b：批次生成 unit content → unit_content_staging。

流程：retrieve grounded chunks → generate_unit_content（含 retry max 3）→ UPSERT staging。

設計取捨：
- per-concept 不 per-unit：1 concept N user units 共用 grounded content。
- needs_more_source 聚合：2 section 任一 flag → row 標 True（U2b 移除 summary）。
- 涵蓋全部 62 部（含 video_order 1-3 課程介紹）；只要有 video_order 就生成
  （課程介紹單元的 code_examples 由 content_generator 跳過，見 U2c）。
- promote 與 generate 分離：6-4 抽查通過後才 promote（unit_content_promote.py）。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.errors import AppError
from models.concept import Concept
from models.unit_content_staging import StagingStatus, UnitContentStaging
from services.learning.content_generator import UnitContent, generate_unit_content
from services.rag.retrieve import RetrievedChunk, get_chunks_by_video_order

MAX_RETRIES = 3
_RETRYABLE_ERRORS = ("LLM_UNAVAILABLE", "LLM_PARSE_ERROR")


@dataclass
class GenerationResult:
    """單一 concept 生成結果摘要（caller 用於 logging / dry-run 顯示）。"""

    concept_id: UUID
    concept_tag: str
    video_order: int
    chunks_count: int
    attempt_count: int
    success: bool
    needs_more_source: bool
    error: str | None = None


def _flatten_notes(unit_content: UnitContent) -> str:
    """聚合 2 section 的 reason 字串，給 6-4 審查者一眼看出缺什麼。"""
    parts = []
    if unit_content.concept_explanation.needs_more_source:
        parts.append(f"concept: {unit_content.concept_explanation.reason}")
    if unit_content.code_examples.needs_more_source:
        parts.append(f"examples: {unit_content.code_examples.reason}")
    return " | ".join(parts)


def _aggregate_needs_more_source(unit_content: UnitContent) -> bool:
    """2 section 任一 needs_more_source=True → 整 row 標 True。"""
    return (
        unit_content.concept_explanation.needs_more_source
        or unit_content.code_examples.needs_more_source
    )


async def _generate_with_retry(
    concept: Concept, chunks: list[RetrievedChunk], max_retries: int = MAX_RETRIES
) -> tuple[UnitContent, int]:
    """呼叫 generate_unit_content，遇 transient error 退避重試。

    Returns:
        (unit_content, attempt_count)

    Raises:
        AppError: 連續 max_retries 次失敗或非 transient 錯誤
    """
    last_error: AppError | None = None
    for attempt in range(1, max_retries + 1):
        try:
            content = await generate_unit_content(concept, chunks)
            return content, attempt
        except AppError as e:
            last_error = e
            if e.error not in _RETRYABLE_ERRORS or attempt == max_retries:
                raise
            await asyncio.sleep(1.0 * attempt)
    raise last_error or AppError(500, "INTERNAL_ERROR", "retry loop exited")


async def _upsert_staging(
    db: AsyncSession,
    concept_id: UUID,
    unit_content: UnitContent,
    attempt_count: int,
) -> None:
    """UPSERT 到 unit_content_staging（concept_id UNIQUE）。

    重生時：reset status='pending'、reviewed_at=NULL、generated_at=NOW()。

    用 SELECT-then-INSERT/UPDATE 而非 PG dialect on_conflict，以保持與 SQLite 測試
    DB 相容；UNIQUE(concept_id) 仍由 schema 強制（race condition 在批次腳本場景不存在）。
    """
    needs_more = _aggregate_needs_more_source(unit_content)
    notes = _flatten_notes(unit_content)
    payload = unit_content.model_dump(mode="json")

    existing = (
        await db.execute(
            select(UnitContentStaging).where(
                UnitContentStaging.concept_id == concept_id
            )
        )
    ).scalar_one_or_none()

    if existing is None:
        db.add(
            UnitContentStaging(
                concept_id=concept_id,
                content=payload,
                status=StagingStatus.PENDING.value,
                needs_more_source=needs_more,
                notes=notes,
                attempt_count=attempt_count,
                model_used=settings.llm_model_content,
            )
        )
    else:
        existing.content = payload
        existing.status = StagingStatus.PENDING.value
        existing.needs_more_source = needs_more
        existing.notes = notes
        existing.attempt_count = attempt_count
        existing.model_used = settings.llm_model_content
        existing.generated_at = datetime.now(timezone.utc)
        existing.reviewed_at = None
    await db.commit()


async def _is_concept_approved(db: AsyncSession, concept_id: UUID) -> bool:
    row = (
        await db.execute(
            select(UnitContentStaging.status).where(
                UnitContentStaging.concept_id == concept_id
            )
        )
    ).scalar_one_or_none()
    return row == StagingStatus.APPROVED.value


async def generate_for_concept(
    db: AsyncSession, concept: Concept
) -> GenerationResult:
    """為單一 concept 生成 unit content 並落到 staging。

    Returns:
        GenerationResult；success=False 時 error 含原因（不向上拋例外，由 caller 決定批次行為）

    Raises:
        AppError 422 NO_VIDEO_ORDER — concept 缺 video_order metadata（防呆）
    """
    if concept.video_order is None:
        raise AppError(
            422,
            "NO_VIDEO_ORDER",
            f"concept {concept.tag} 缺 video_order，無法 grounded retrieve",
        )

    chunks = await get_chunks_by_video_order(concept.video_order)

    try:
        unit_content, attempt_count = await _generate_with_retry(concept, chunks)
    except AppError as e:
        return GenerationResult(
            concept_id=concept.id,
            concept_tag=concept.tag,
            video_order=concept.video_order,
            chunks_count=len(chunks),
            attempt_count=MAX_RETRIES,
            success=False,
            needs_more_source=False,
            error=f"{e.error}: {e.message}",
        )

    await _upsert_staging(db, concept.id, unit_content, attempt_count)

    return GenerationResult(
        concept_id=concept.id,
        concept_tag=concept.tag,
        video_order=concept.video_order,
        chunks_count=len(chunks),
        attempt_count=attempt_count,
        success=True,
        needs_more_source=_aggregate_needs_more_source(unit_content),
    )


async def list_target_concepts(
    db: AsyncSession, only: int | None = None
) -> list[Concept]:
    """取出本 phase 應生成的 concepts（凡有 video_order 皆生成；含 1-3 課程介紹）。"""
    stmt = (
        select(Concept)
        .where(Concept.video_order.is_not(None))
        .order_by(Concept.video_order)
    )
    if only is not None:
        stmt = stmt.where(Concept.video_order == only)
    return list((await db.execute(stmt)).scalars().all())


async def generate_all(
    db: AsyncSession,
    only: int | None = None,
    skip_existing: bool = True,
) -> list[GenerationResult]:
    """批次生成入口。

    Args:
        db: SQLAlchemy async session
        only: 僅處理特定 video_order（None = 全部）
        skip_existing: True 時跳過 staging 已 approved 的 concept（避免覆蓋已通過審查內容）；
                       pending/rejected 仍會重生

    Returns:
        每個 concept 一筆 GenerationResult（含成功 / 失敗 / needs_more_source 標記）
    """
    concepts = await list_target_concepts(db, only=only)

    results: list[GenerationResult] = []
    for concept in concepts:
        if skip_existing and await _is_concept_approved(db, concept.id):
            results.append(
                GenerationResult(
                    concept_id=concept.id,
                    concept_tag=concept.tag,
                    video_order=concept.video_order or 0,
                    chunks_count=0,
                    attempt_count=0,
                    success=True,
                    needs_more_source=False,
                    error="SKIPPED_APPROVED",
                )
            )
            continue
        results.append(await generate_for_concept(db, concept))
    return results
