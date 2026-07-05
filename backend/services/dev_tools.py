"""開發者模式 service（DEV-3/5/6）— 分類重置 / 熟練度覆寫 / 身分切換。

僅供 `/dev/*` 端點使用（入口一律掛 `require_dev_user`）。
bulk delete 繞過 ORM cascade，子表一律顯式先刪（不依賴 DB FK cascade，
SQLite 測試與 Postgres 行為才一致）。
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.chat import ChatMessage, ChatSession
from models.concept import Concept
from models.learning import LearningPath, LearningUnit
from models.mastery import StudentMastery
from models.quiz import StudentAnswer
from models.reflection import Reflection, ReflectionSourceType
from models.user import User, UserRole

logger = logging.getLogger(__name__)

# 重置類別 → 中文名（log 與 API 回應共用）
RESET_CATEGORIES = ("mastery", "progress", "quiz", "chat")


async def reset_user_data(
    db: AsyncSession,
    user_id: uuid.UUID,
    categories: set[str],
) -> dict[str, int]:
    """分類刪除使用者學習資料，回傳各類別刪除列數。

    - mastery: student_mastery
    - progress: learning_paths + learning_units + learning_unit 反思
    - quiz: student_answers + quiz 反思
    - chat: chat_sessions + chat_messages
    """
    deleted: dict[str, int] = {}

    if "mastery" in categories:
        result = await db.execute(
            delete(StudentMastery).where(StudentMastery.user_id == user_id)
        )
        deleted["mastery"] = result.rowcount

    if "progress" in categories:
        path_ids = select(LearningPath.id).where(LearningPath.user_id == user_id)
        await db.execute(
            delete(LearningUnit).where(LearningUnit.path_id.in_(path_ids))
        )
        result = await db.execute(
            delete(LearningPath).where(LearningPath.user_id == user_id)
        )
        await db.execute(
            delete(Reflection).where(
                Reflection.user_id == user_id,
                Reflection.source_type == ReflectionSourceType.LEARNING_UNIT.value,
            )
        )
        deleted["progress"] = result.rowcount

    if "quiz" in categories:
        result = await db.execute(
            delete(StudentAnswer).where(StudentAnswer.user_id == user_id)
        )
        await db.execute(
            delete(Reflection).where(
                Reflection.user_id == user_id,
                Reflection.source_type == ReflectionSourceType.QUIZ.value,
            )
        )
        deleted["quiz"] = result.rowcount

    if "chat" in categories:
        session_ids = select(ChatSession.id).where(ChatSession.user_id == user_id)
        await db.execute(
            delete(ChatMessage).where(ChatMessage.session_id.in_(session_ids))
        )
        result = await db.execute(
            delete(ChatSession).where(ChatSession.user_id == user_id)
        )
        deleted["chat"] = result.rowcount

    await db.commit()
    logger.info("[dev] reset user=%s categories=%s deleted=%s", user_id, sorted(categories), deleted)
    return deleted


async def set_mastery(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    tags: list[str] | None,
    category: str | None,
    confidence: float,
) -> int:
    """覆寫指定 concepts（tags 或整章 category 擇一）的熟練度，回傳影響筆數。

    upsert：已有記錄只改 confidence / last_practiced_at；新記錄 exposure_count=1
    （讓前端 mastery band 視為「已互動」而非 unseen）。
    """
    stmt = select(Concept.id)
    if tags is not None:
        stmt = stmt.where(Concept.tag.in_(tags))
    else:
        stmt = stmt.where(Concept.category == category)
    concept_ids = list((await db.execute(stmt)).scalars())
    if not concept_ids:
        return 0

    now = datetime.now(timezone.utc)
    existing = {
        m.concept_id: m
        for m in (
            await db.execute(
                select(StudentMastery).where(
                    StudentMastery.user_id == user_id,
                    StudentMastery.concept_id.in_(concept_ids),
                )
            )
        ).scalars()
    }
    for cid in concept_ids:
        row = existing.get(cid)
        if row is not None:
            row.confidence = confidence
            row.last_practiced_at = now
        else:
            db.add(
                StudentMastery(
                    user_id=user_id,
                    concept_id=cid,
                    confidence=confidence,
                    exposure_count=1,
                    last_practiced_at=now,
                )
            )
    await db.commit()
    logger.info(
        "[dev] set_mastery user=%s targets=%s confidence=%.2f count=%d",
        user_id, tags if tags is not None else f"category:{category}", confidence, len(concept_ids),
    )
    return len(concept_ids)


async def set_role(db: AsyncSession, user: User, role: UserRole) -> User:
    """切換使用者角色（student ⇄ teacher；真改 DB，行為與真實帳號一致）。"""
    await db.execute(update(User).where(User.id == user.id).values(role=role))
    await db.commit()
    user.role = role
    logger.info("[dev] set_role user=%s role=%s", user.id, role.value)
    return user
