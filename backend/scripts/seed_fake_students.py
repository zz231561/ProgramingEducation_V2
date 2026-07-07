"""DEV-E CLI：生成假學生行為資料供教師端 / 行為分析本機開發。

用法：
    cd backend
    .venv/bin/python -m scripts.seed_fake_students                 # 8 位，預設 demo 班級
    .venv/bin/python -m scripts.seed_fake_students --count 20      # 20 位
    .venv/bin/python -m scripts.seed_fake_students --class-id <uuid>  # 併入既有班級

一律先 purge 舊 seed 學生（email 後綴 @seed.dev）再重建，確保可重現、email 不撞號。
demo 教師 seed-teacher@seed.dev + demo 班級為 get-or-create（reuse，不受 purge 影響）。
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid

from core.database import async_session
from services.dev_seed import seed_fake_students


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="生成假學生行為資料（DEV-E）")
    p.add_argument("--count", type=int, default=8, help="假學生數量（預設 8）")
    p.add_argument("--class-id", type=str, default=None, help="併入既有班級 UUID")
    p.add_argument("--seed", type=int, default=42, help="RNG 種子（可重現）")
    return p.parse_args()


async def main() -> int:
    args = _parse_args()
    class_id = uuid.UUID(args.class_id) if args.class_id else None
    async with async_session() as db:
        summary = await seed_fake_students(
            db, count=args.count, class_id=class_id, seed=args.seed
        )
    print("\n=== DEV-E seed summary ===")
    print(f"  purged  : {summary['purged']}")
    print(f"  created : {summary['created']}")
    print(f"  class_id: {summary['class_id']}")
    print(f"  archetypes: {summary['archetypes']}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
