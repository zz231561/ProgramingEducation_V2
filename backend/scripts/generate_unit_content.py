"""Phase 6-2b CLI：批次生成 unit content → unit_content_staging。

用法：
    cd backend
    .venv/bin/python -m scripts.generate_unit_content              # 全部 59 concept
    .venv/bin/python -m scripts.generate_unit_content --only 47    # 單一 video
    .venv/bin/python -m scripts.generate_unit_content --force      # 連 approved 也重生
    .venv/bin/python -m scripts.generate_unit_content --dry-run    # 列出將處理 concept

成本估計：59 concept × 3 LLM call × ~3-5k token = ~150-300k token
gpt-4o ~$5-10 USD（依 retry 次數）。建議先 `--only` 抽 1-2 部驗證。
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from core.database import async_session
from services.learning.batch_generator import (
    GenerationResult,
    generate_all,
    list_target_concepts,
)


def _print_summary(results: list[GenerationResult]) -> int:
    """印出批次摘要 + failed 明細；回傳 exit code（失敗時 != 0）。"""
    success = sum(
        1 for r in results if r.success and r.error != "SKIPPED_APPROVED"
    )
    skipped = sum(1 for r in results if r.error == "SKIPPED_APPROVED")
    needs_more = sum(1 for r in results if r.needs_more_source)
    failed = [r for r in results if not r.success]

    print("\n=== Phase 6-2b batch generation summary ===")
    print(f"  total: {len(results)}")
    print(f"  success: {success}")
    print(f"  skipped (approved): {skipped}")
    print(f"  needs_more_source: {needs_more}")
    print(f"  failed: {len(failed)}")
    if failed:
        print("\nFailed:")
        for r in failed:
            print(f"  v{r.video_order:02d} {r.concept_tag}: {r.error}")
    if needs_more:
        print("\nNeeds more source (review in 6-4):")
        for r in results:
            if r.needs_more_source:
                print(f"  v{r.video_order:02d} {r.concept_tag}")

    return 1 if failed else 0


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
        marker = "✅" if r.success and r.error != "SKIPPED_APPROVED" else (
            "⏭️ " if r.error == "SKIPPED_APPROVED" else "❌"
        )
        flag = " ⚠ needs_more_source" if r.needs_more_source else ""
        print(
            f"  {marker} v{r.video_order:02d} {r.concept_tag} "
            f"(chunks={r.chunks_count}, attempts={r.attempt_count}){flag}"
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
        help="連 staging.status='approved' 也重新生成（預設跳過避免覆蓋）",
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
