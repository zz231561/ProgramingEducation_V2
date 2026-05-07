"""Phase 6-1d PATCH script — 把 CSV 的 video metadata 寫入 concepts 表。

讀取 `data/teaching_content/videos.csv`（由 6-1b fetcher 產），對 `concepts` 表
依 `video_order` 匹配，UPDATE `video_youtube_id` 與 `video_duration_seconds`
兩欄。預設 dry-run，需 `--apply` 才實際寫入。

用法：
    cd backend
    .venv/bin/python -m scripts.patch_video_metadata           # dry-run 預設
    .venv/bin/python -m scripts.patch_video_metadata --apply   # 實際寫入
    .venv/bin/python -m scripts.patch_video_metadata --apply --force  # 覆寫已有

驗收標準（roadmap 6-1d）：
    SELECT count(*) FROM concepts
    WHERE video_order BETWEEN 1 AND 62
      AND video_youtube_id IS NOT NULL
      AND video_duration_seconds IS NOT NULL;
    → 應為 62
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from sqlalchemy import select, update

from core.database import async_session
from models.concept import Concept

# script 位於 backend/scripts/，CSV 位於 project_root/data/teaching_content/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CSV = _PROJECT_ROOT / "data" / "teaching_content" / "videos.csv"


@dataclass(frozen=True)
class UpdatePlan:
    concept_id: UUID
    video_order: int
    db_yt: str | None
    db_dur: int | None
    db_name_zh: str
    new_yt: str
    new_dur: int
    new_title_zh: str


def parse_csv(path: Path) -> list[dict]:
    """讀 CSV → list of dicts；型別轉換 + 必填欄位驗證。"""
    if not path.exists():
        sys.exit(f"❌ CSV not found: {path}")
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):  # header is line 1
            try:
                rows.append(
                    {
                        "video_order": int(row["video_order"]),
                        "youtube_id": row["youtube_id"].strip(),
                        "duration_seconds": int(row["duration_seconds"]),
                        "title_zh": row.get("title_zh", "").strip(),
                    }
                )
            except (KeyError, ValueError) as e:
                sys.exit(f"❌ CSV parse error at line {line_no}: {e}")
    return rows


async def build_plan(
    csv_rows: list[dict], force: bool
) -> tuple[list[UpdatePlan], list[UpdatePlan], list[UpdatePlan], list[dict], list[tuple]]:
    """分類：to_update / no_change / conflicts / missing / title_mismatch。

    title_mismatch 為 sanity check（不影響 update 決策，只 warn）。
    """
    to_update: list[UpdatePlan] = []
    no_change: list[UpdatePlan] = []
    conflicts: list[UpdatePlan] = []
    missing: list[dict] = []
    title_mismatches: list[tuple[int, str, str]] = []  # (order, db_name, csv_title)

    async with async_session() as db:
        rows = (
            await db.execute(
                select(Concept).where(Concept.video_order.is_not(None))
            )
        ).scalars().all()
        db_by_order = {c.video_order: c for c in rows}

    for row in csv_rows:
        order = row["video_order"]
        c = db_by_order.get(order)
        if c is None:
            missing.append(row)
            continue

        # title sanity check
        if row["title_zh"] and row["title_zh"] != c.name_zh:
            title_mismatches.append((order, c.name_zh, row["title_zh"]))

        plan = UpdatePlan(
            concept_id=c.id,
            video_order=order,
            db_yt=c.video_youtube_id,
            db_dur=c.video_duration_seconds,
            db_name_zh=c.name_zh,
            new_yt=row["youtube_id"],
            new_dur=row["duration_seconds"],
            new_title_zh=row["title_zh"],
        )

        same_yt = c.video_youtube_id == row["youtube_id"]
        same_dur = c.video_duration_seconds == row["duration_seconds"]
        if same_yt and same_dur:
            no_change.append(plan)
            continue

        # 衝突偵測：DB 已有非 NULL 值 且與 CSV 不同
        existing_yt_diff = c.video_youtube_id is not None and not same_yt
        existing_dur_diff = c.video_duration_seconds is not None and not same_dur
        if existing_yt_diff or existing_dur_diff:
            if force:
                to_update.append(plan)
            else:
                conflicts.append(plan)
        else:
            to_update.append(plan)

    return to_update, no_change, conflicts, missing, title_mismatches


async def apply_plan(plans: list[UpdatePlan]) -> None:
    """執行 UPDATE。每個 plan 一個 UPDATE statement（簡單可靠）。"""
    async with async_session() as db:
        for p in plans:
            await db.execute(
                update(Concept)
                .where(Concept.id == p.concept_id)
                .values(
                    video_youtube_id=p.new_yt,
                    video_duration_seconds=p.new_dur,
                )
            )
        await db.commit()


def print_report(
    csv_rows: list[dict],
    to_update: list[UpdatePlan],
    no_change: list[UpdatePlan],
    conflicts: list[UpdatePlan],
    missing: list[dict],
    title_mismatches: list[tuple],
    apply_mode: bool,
    force: bool,
) -> None:
    print(f"\n=== Plan (CSV rows: {len(csv_rows)}) ===")
    print(f"  to_update : {len(to_update):3d}")
    print(f"  no_change : {len(no_change):3d}")
    print(f"  conflicts : {len(conflicts):3d} (use --force to overwrite)")
    print(f"  missing   : {len(missing):3d} (in CSV but not in DB)")

    if title_mismatches:
        print(f"\n  ⚠ Title mismatches ({len(title_mismatches)}; not auto-updated):")
        for order, db_name, csv_title in title_mismatches[:5]:
            print(f"    [{order}] DB={db_name!r}  vs  CSV={csv_title!r}")
        if len(title_mismatches) > 5:
            print(f"    ... and {len(title_mismatches) - 5} more")

    if conflicts:
        print(f"\n  Conflicts ({len(conflicts)}):")
        for p in conflicts[:5]:
            print(
                f"    [{p.video_order}] DB={p.db_yt}/{p.db_dur} "
                f"vs CSV={p.new_yt}/{p.new_dur}"
            )
        if len(conflicts) > 5:
            print(f"    ... and {len(conflicts) - 5} more")

    if missing:
        print(
            f"\n  Missing in DB (orders): "
            f"{sorted(r['video_order'] for r in missing)}"
        )

    if to_update and len(to_update) <= 5:
        print(f"\n  Sample updates:")
        for p in to_update[:3]:
            print(f"    [{p.video_order}] {p.db_name_zh} ← {p.new_yt} ({p.new_dur}s)")

    if not apply_mode:
        print("\n[dry-run] No DB writes. Use --apply to actually write.")
    elif conflicts and not force:
        print("\n⚠ Conflicts detected; use --force to overwrite, or fix CSV. Aborting.")


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv", default=str(DEFAULT_CSV),
        help=f"CSV path (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually write to DB (default: dry-run)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite existing non-NULL DB values that differ from CSV",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    csv_rows = parse_csv(csv_path)
    print(f"Read {len(csv_rows)} rows from {csv_path}")

    to_update, no_change, conflicts, missing, title_mismatches = await build_plan(
        csv_rows, args.force
    )

    print_report(
        csv_rows, to_update, no_change, conflicts, missing,
        title_mismatches, args.apply, args.force,
    )

    if not args.apply:
        return 0
    if conflicts and not args.force:
        return 2
    if not to_update:
        print("\n✅ Nothing to update (all rows already in sync)")
        return 0

    await apply_plan(to_update)
    print(f"\n✅ Applied {len(to_update)} updates to DB")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
