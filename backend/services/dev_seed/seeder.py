"""假學生資料 seeder — 編排（DEV-E）。

purge（以 email 後綴清舊 seed 學生，顯式刪子表跨 SQLite/PG 一致）+ get-or-create demo
教師/班級（reuse，purge 不動）+ 逐位學生寫入 profile / 成員 / 事件 / 熟練度 / 對話。
純資料產生器見 `generators.py`。僅供本機 dev。
"""

import logging
import random
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.chat import ChatMessage, ChatSession
from models.classroom import ClassMember, Classroom
from models.coding_event import CodingEvent
from models.concept import Concept
from models.mastery import StudentMastery
from models.student_profile import StudentProfile
from models.user import User, UserRole
from services.dev_seed import generators
from services.dev_seed.generators import ARCHETYPES

logger = logging.getLogger(__name__)

SEED_EMAIL_DOMAIN = "seed.dev"
_TEACHER_EMAIL = f"seed-teacher@{SEED_EMAIL_DOMAIN}"
_CLASS_NAME = "Dev 假資料班級"
_CLASS_INVITE_CODE = "DEVSED"


async def purge_seed_students(db: AsyncSession) -> int:
    """清除所有 seed 假學生及其資料（顯式刪子表，回傳刪除學生數）。"""
    ids = list(
        (
            await db.execute(
                select(User.id).where(
                    User.email.like(f"%@{SEED_EMAIL_DOMAIN}"),
                    User.role == UserRole.STUDENT,
                )
            )
        ).scalars()
    )
    if not ids:
        return 0
    sess_ids = list(
        (
            await db.execute(
                select(ChatSession.id).where(ChatSession.user_id.in_(ids))
            )
        ).scalars()
    )
    if sess_ids:
        await db.execute(
            delete(ChatMessage).where(ChatMessage.session_id.in_(sess_ids))
        )
        await db.execute(delete(ChatSession).where(ChatSession.id.in_(sess_ids)))
    await db.execute(delete(CodingEvent).where(CodingEvent.user_id.in_(ids)))
    await db.execute(delete(StudentMastery).where(StudentMastery.user_id.in_(ids)))
    await db.execute(delete(StudentProfile).where(StudentProfile.user_id.in_(ids)))
    await db.execute(delete(ClassMember).where(ClassMember.user_id.in_(ids)))
    await db.execute(delete(User).where(User.id.in_(ids)))
    await db.commit()
    return len(ids)


async def _ensure_demo_class(
    db: AsyncSession, class_id: uuid.UUID | None
) -> Classroom:
    """取得指定班級，或 get-or-create demo 教師 + demo 班級。"""
    if class_id is not None:
        cls = (
            await db.execute(select(Classroom).where(Classroom.id == class_id))
        ).scalar_one_or_none()
        if cls is None:
            raise ValueError(f"class_id {class_id} 不存在")
        return cls

    teacher = (
        await db.execute(select(User).where(User.email == _TEACHER_EMAIL))
    ).scalar_one_or_none()
    if teacher is None:
        teacher = User(
            email=_TEACHER_EMAIL, name="Dev 假教師", role=UserRole.TEACHER,
            role_selected=True, google_id=f"seed-teacher-{uuid.uuid4().hex[:12]}",
        )
        db.add(teacher)
        await db.flush()
    cls = (
        await db.execute(
            select(Classroom).where(Classroom.teacher_id == teacher.id)
        )
    ).scalar_one_or_none()
    if cls is None:
        cls = Classroom(
            name=_CLASS_NAME, teacher_id=teacher.id, invite_code=_CLASS_INVITE_CODE
        )
        db.add(cls)
        await db.flush()
    return cls


async def _seed_one_student(
    db: AsyncSession, cls_id: uuid.UUID, idx: int, seed: int, concept_ids: list
) -> str:
    """建立單一假學生 + 其全部資料，回傳所用原型 key。"""
    rng = random.Random(seed + idx)
    arch = ARCHETYPES[idx % len(ARCHETYPES)]
    user = User(
        email=f"seed-student-{idx}@{SEED_EMAIL_DOMAIN}", name=f"SeedStudent{idx}",
        role=UserRole.STUDENT, role_selected=True,
        google_id=f"seed-student-{uuid.uuid4().hex[:12]}",
    )
    db.add(user)
    await db.flush()
    db.add(generators.make_profile(rng, user.id, idx))
    db.add(ClassMember(class_id=cls_id, user_id=user.id))
    db.add_all(generators.make_events(rng, user.id, arch))
    if concept_ids:
        db.add_all(generators.make_mastery(rng, user.id, arch, concept_ids))
    session = ChatSession(user_id=user.id, title="Dev seed 對話")
    db.add(session)
    await db.flush()
    db.add_all(generators.make_chat_messages(rng, session.id, arch))
    return arch.key


async def seed_fake_students(
    db: AsyncSession,
    *,
    count: int = 8,
    class_id: uuid.UUID | None = None,
    seed: int = 42,
) -> dict:
    """生成 count 位假學生（一律先 purge 舊 seed 學生 → 可重現、email 不撞號）。"""
    purged = await purge_seed_students(db)
    cls = await _ensure_demo_class(db, class_id)
    concept_ids = list(
        (
            await db.execute(
                select(Concept.id).order_by(Concept.video_order).limit(30)
            )
        ).scalars()
    )

    archetypes = [
        await _seed_one_student(db, cls.id, idx, seed, concept_ids)
        for idx in range(count)
    ]
    await db.commit()

    return {
        "purged": purged,
        "created": len(archetypes),
        "class_id": str(cls.id),
        "archetypes": {k: archetypes.count(k) for k in sorted(set(archetypes))},
    }
