"""6-3c：以更新後的審查標準重新複審既有題庫，刪除不合格題。

背景（2026-07-06 使用者回饋）：validate 新增「考點有意義」面向（排除操作細節 /
瑣碎選項，如「左上角/右下角」）。既有題庫在舊標準下入庫，需重新複審。

策略：對每題重跑 validate_question（新標準）；未通過 → 刪除。
LEARN 題組（source='batch'）刪掉的洞由 generate_unit_questions 補回；
QUIZ 大題庫（source='generated'）刪掉即淨化。

用法：
    cd backend
    .venv/bin/python -m scripts.rereview_questions --dry-run   # 只報告不刪
    .venv/bin/python -m scripts.rereview_questions             # 實際刪除不合格題
    .venv/bin/python -m scripts.rereview_questions --only-source generated
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import delete, select

from core.database import async_session
from core.errors import AppError
from models.quiz import Question, StudentAnswer
from services.quiz.validate import validate_question


async def _run(dry_run: bool, only_source: str | None) -> int:
    async with async_session() as db:
        stmt = select(Question).where(Question.validated.is_(True))
        if only_source is not None:
            stmt = stmt.where(Question.source == only_source)
        stmt = stmt.order_by(Question.created_at)
        questions = (await db.execute(stmt)).scalars().all()

    print(f"複審 {len(questions)} 題 validated 題目"
          + (f"（source={only_source}）" if only_source else ""))

    to_delete: list[tuple[Question, str]] = []
    errors = 0
    for i, q in enumerate(questions, 1):
        # 每題獨立 session：validate 會 set validated（複審不入庫，讀完即棄）
        async with async_session() as db:
            merged = await db.get(Question, q.id)
            try:
                report = await validate_question(db, merged)
            except AppError as e:
                errors += 1
                print(f"  [{i}/{len(questions)}] v? {q.type}: 複審 LLM 失敗 {e.error}（保留）")
                await db.rollback()
                continue
            await db.rollback()  # 不保存 validate 的 side effect

        if not report.passed:
            reason = "; ".join(report.issues) or "unknown"
            to_delete.append((q, reason))
            print(f"  ✗ [{i}/{len(questions)}] {q.type} 不合格：{reason}")

    print(f"\n複審完成：{len(questions)} 題中 {len(to_delete)} 題不合格"
          f"（LLM 失敗保留 {errors} 題）")

    if not to_delete:
        return 0
    if dry_run:
        print("dry-run：未刪除。移除 --dry-run 以實際刪除。")
        return 0

    ids = [q.id for q, _ in to_delete]
    async with async_session() as db:
        # 先刪關聯作答（FK ondelete=CASCADE 也會處理，但明確刪避免孤兒）
        await db.execute(delete(StudentAnswer).where(StudentAnswer.question_id.in_(ids)))
        await db.execute(delete(Question).where(Question.id.in_(ids)))
        await db.commit()
    print(f"已刪除 {len(ids)} 題不合格題目。")
    return 0


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="只報告不刪除")
    parser.add_argument(
        "--only-source", default=None, help="僅複審指定 source（generated / batch）"
    )
    args = parser.parse_args()
    return await _run(args.dry_run, args.only_source)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
