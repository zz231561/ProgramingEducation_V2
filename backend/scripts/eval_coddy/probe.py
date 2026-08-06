"""DB 探針 — 從資料庫直接讀取每輪互動的後台落地狀態。"""

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings
from services.dev_tools import RESET_CATEGORIES, reset_user_data

_engine = create_async_engine(settings.DATABASE_URL, echo=False)
Session = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


async def user_id_by_email(email: str) -> uuid.UUID | None:
    async with Session() as db:
        row = (
            await db.execute(
                text("SELECT id FROM users WHERE email = :e"), {"e": email}
            )
        ).first()
        return row[0] if row else None


async def reset_persona_state(email: str) -> dict[str, int]:
    """把 persona 的學習資料清乾淨，讓每次模擬都從同一個起點開始。

    沒有這一步，harness 的結果會被上一輪殘留污染，而且是**沉默地**污染：
    - 反思對 (user, source) 唯一 → P2 第二次跑必然 409
    - 「未答過且 validated」的題目被答光 → P7 第三輪 QUESTION_BANK_EMPTY
    - mastery / coding_events 跨輪累積 → 改動前後的對照數字不可比

    只清 `@eval.local` 假帳號；`require_local_db` 已擋掉指向生產 DB 的情況。
    """
    if not email.endswith("@eval.local"):
        raise ValueError(f"拒絕重置非模擬帳號：{email}")

    user_id = await user_id_by_email(email)
    if user_id is None:
        return {}

    async with Session() as db:
        deleted = await reset_user_data(db, user_id, set(RESET_CATEGORIES))
        # coding_events 不在 reset_user_data 的類別內（那是行為分析資料），
        # 但它是 harness 的觀測對象之一，跨輪累積會讓事件數斷言失去意義
        result = await db.execute(
            text("DELETE FROM coding_events WHERE user_id = :u"), {"u": user_id}
        )
        deleted["events"] = result.rowcount or 0
        await db.commit()
    return deleted


async def dialogue_act_of(message_id: str) -> str | None:
    """指定 user message 落地的 dialogue_act。"""
    async with Session() as db:
        row = (
            await db.execute(
                text("SELECT dialogue_act FROM chat_messages WHERE id = :i"),
                {"i": message_id},
            )
        ).first()
        return row[0] if row else None


async def mastery_snapshot(user_id: uuid.UUID) -> dict[str, dict[str, Any]]:
    """該生全部 mastery：tag → {confidence, exposure, successes}。"""
    async with Session() as db:
        rows = (
            await db.execute(
                text(
                    "SELECT c.tag, m.confidence, m.exposure_count, m.success_count"
                    " FROM student_mastery m JOIN concepts c ON c.id = m.concept_id"
                    " WHERE m.user_id = :u"
                ),
                {"u": str(user_id)},
            )
        ).all()
        return {
            r[0]: {"confidence": float(r[1]), "exposure": r[2], "successes": r[3]}
            for r in rows
        }


def mastery_diff(before: dict, after: dict) -> dict[str, dict]:
    """兩次快照的差分（新出現或 confidence 變動的 tag）。"""
    out: dict[str, dict] = {}
    for tag, cur in after.items():
        prev = before.get(tag)
        if prev is None:
            out[tag] = {"from": None, "to": round(cur["confidence"], 4)}
        elif abs(cur["confidence"] - prev["confidence"]) > 1e-9:
            out[tag] = {
                "from": round(prev["confidence"], 4),
                "to": round(cur["confidence"], 4),
            }
    return out


async def coding_events_of(user_id: uuid.UUID) -> list[dict]:
    async with Session() as db:
        rows = (
            await db.execute(
                text(
                    "SELECT event_type, hint_level, concept_tags FROM coding_events"
                    " WHERE user_id = :u ORDER BY created_at"
                ),
                {"u": str(user_id)},
            )
        ).all()
        return [
            {"type": r[0], "hint_level": r[1], "tags": r[2]} for r in rows
        ]


async def shift_last_practiced(user_id: uuid.UUID, tag: str, days: int) -> int:
    """把某 concept 的 last_practiced_at 往回撥 N 天（驗證 K6b 衰減用）。"""
    async with Session() as db:
        res = await db.execute(
            text(
                "UPDATE student_mastery SET last_practiced_at ="
                " last_practiced_at - make_interval(days => :d)"
                " WHERE user_id = :u AND concept_id ="
                " (SELECT id FROM concepts WHERE tag = :t)"
            ),
            {"d": days, "u": str(user_id), "t": tag},
        )
        await db.commit()
        return res.rowcount
