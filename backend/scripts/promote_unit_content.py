"""U2g CLI：staging 批次 approve + promote → learning_units.content。

背景（2026-07-06 晚間決策）：6-4a 正式抽查移除，改由使用者實際操作回饋；
staging 內容直接全量上線。promote 前剝除已下架 section 的殘留 key
（U2b summary / U2g code_examples），learning_units 只收概念說明。

用法：
    cd backend
    .venv/bin/python -m scripts.promote_unit_content              # 全部
    .venv/bin/python -m scripts.promote_unit_content --only 47    # 單一 video
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone

from sqlalchemy import select

from core.database import async_session
from models.concept import Concept
from models.unit_content_staging import StagingStatus, UnitContentStaging
from services.learning.unit_content_promote import promote_concept

_REMOVED_SECTIONS = ("summary", "code_examples")


async def _run(only: int | None) -> int:
    async with async_session() as db:
        stmt = (
            select(UnitContentStaging, Concept)
            .join(Concept, Concept.id == UnitContentStaging.concept_id)
            .order_by(Concept.video_order)
        )
        if only is not None:
            stmt = stmt.where(Concept.video_order == only)
        rows = (await db.execute(stmt)).all()

        promoted = 0
        units_touched = 0
        for staging, concept in rows:
            content = {
                k: v for k, v in (staging.content or {}).items()
                if k not in _REMOVED_SECTIONS
            }
            staging.content = content
            staging.status = StagingStatus.APPROVED.value
            staging.reviewed_at = datetime.now(timezone.utc)
            await db.commit()

            count = await promote_concept(db, staging.concept_id)
            promoted += 1
            units_touched += count
            print(f"  v{concept.video_order:02d} {concept.tag}: {count} unit(s)")

    print(f"\npromoted {promoted} concept(s) → {units_touched} learning_unit(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", type=int, default=None, help="僅處理指定 video_order")
    args = parser.parse_args()
    return asyncio.run(_run(args.only))


if __name__ == "__main__":
    sys.exit(main())
