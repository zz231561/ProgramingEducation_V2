"""6-3c CLI：知識點驅動批次生成 → questions 表（source='batch'，validated=True 才入庫）。

題量依影片知識量：每部影片 LLM 萃取 3-8 個重要知識點 → 每點 1 題觀念選擇題；
非課程介紹單元另加 1 題 coding。

用法：
    cd backend
    .venv/bin/python -m scripts.generate_unit_questions              # 全部 62 concept
    .venv/bin/python -m scripts.generate_unit_questions --only 47    # 單一 video
    .venv/bin/python -m scripts.generate_unit_questions --force      # 連已有 batch 題組也重生
    .venv/bin/python -m scripts.generate_unit_questions --dry-run    # 列出將處理 concept

skip_existing（預設）：已有 batch MC 題組 → 跳過 MC；已有 validated coding → 跳過 coding。
成本估計：62 concept × (知識點萃取 1 + 每題 generate+validate) ≈ $4-8 USD。
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from core.database import async_session
from services.quiz.batch_generator import (
    ConceptBatchResult,
    generate_all,
    list_target_concepts,
)


def _print_summary(results: list[ConceptBatchResult]) -> int:
    """印出批次摘要 + failed / partial 明細；回傳 exit code（任一 concept 全失敗 → != 0）。"""
    total_concepts = len(results)
    # requested=0 且無 error → 全部 skip（既有題組已足）
    skipped = sum(1 for r in results if r.error is None and r.requested == 0)
    concept_failed = sum(1 for r in results if r.error is not None)
    full_success = sum(
        1
        for r in results
        if r.error is None and r.requested > 0 and r.validated_count == r.requested
    )
    partial = sum(
        1
        for r in results
        if r.error is None and 0 < r.validated_count < r.requested
    )
    all_failed = sum(
        1
        for r in results
        if r.error is None and r.validated_count == 0 and r.requested > 0
    )
    total_questions = sum(r.validated_count for r in results)

    print("\n=== 6-3c batch generation summary ===")
    print(f"  concepts: {total_concepts}")
    print(f"  full success: {full_success}")
    print(f"  partial (some questions failed): {partial}")
    print(f"  all-failed: {all_failed}")
    print(f"  concept-level error (e.g. knowledge points): {concept_failed}")
    print(f"  skipped (already has batch set): {skipped}")
    print(f"  total validated questions inserted: {total_questions}")

    if partial or all_failed or concept_failed:
        print("\nFailed / partial details:")
        for r in results:
            if r.error:
                print(f"  v{r.video_order:02d} {r.concept_tag}: {r.error}")
                continue
            if r.requested == 0 or r.validated_count >= r.requested:
                continue
            print(f"  v{r.video_order:02d} {r.concept_tag} ({r.validated_count}/{r.requested}):")
            for a in r.attempts:
                if a.validated:
                    continue
                err = a.error or "; ".join(a.issues) or "unknown"
                print(f"    - {a.question_type}: {err}")

    return 1 if (all_failed or concept_failed) else 0


async def _dry_run(only: int | None) -> int:
    async with async_session() as db:
        concepts = await list_target_concepts(db, only=only)
    print(f"Dry run: {len(concepts)} concept(s) would be processed")
    for c in concepts:
        print(f"  v{c.video_order:02d} {c.tag} ({c.name_zh})")
    return 0


async def _run(only: int | None, force: bool) -> int:
    async with async_session() as db:
        results = await generate_all(db, only=only, skip_existing=not force)
    for r in results:
        if r.error:
            marker = "❌"
        elif r.requested == 0:
            marker = "⏭️ "
        elif r.validated_count == r.requested:
            marker = "✅"
        elif r.validated_count > 0:
            marker = "⚠"
        else:
            marker = "❌"
        print(
            f"  {marker} v{r.video_order:02d} {r.concept_tag} "
            f"({r.validated_count}/{r.requested} validated)"
        )
    return _print_summary(results)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only", type=int, default=None, help="只處理特定 video_order"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="連已有 validated 題的 concept 也重生（預設跳過避免重複）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="列出將處理的 concept，不實際呼叫 LLM",
    )
    args = parser.parse_args()

    if args.dry_run:
        return await _dry_run(args.only)
    return await _run(args.only, args.force)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
