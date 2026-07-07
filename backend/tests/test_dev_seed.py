"""假學生 seeder 測試（DEV-E）— seed / purge / 可重現 / 與 5-2d 聚合整合。"""

import uuid

import pytest
from sqlalchemy import func, select

from models.chat import ChatMessage, ChatSession
from models.classroom import ClassMember, Classroom
from models.coding_event import CodingEvent
from models.concept import Concept
from models.mastery import StudentMastery
from models.student_profile import StudentProfile
from models.user import User, UserRole
from services.analytics import aggregate_user_behavior
from services.dev_seed import (
    SEED_EMAIL_DOMAIN,
    purge_seed_students,
    seed_fake_students,
)
from tests.helpers import TestSessionFactory


async def _seed_concepts(n: int = 6) -> None:
    async with TestSessionFactory() as db:
        for i in range(n):
            db.add(
                Concept(
                    tag=f"seed-concept-{i}", name_zh=f"概念{i}", name_en=f"concept{i}",
                    difficulty_level=1, category="測試", video_order=i + 1,
                )
            )
        await db.commit()


async def _seed_user_ids() -> list[uuid.UUID]:
    async with TestSessionFactory() as db:
        return list(
            (
                await db.execute(
                    select(User.id).where(
                        User.email.like(f"%@{SEED_EMAIL_DOMAIN}"),
                        User.role == UserRole.STUDENT,
                    )
                )
            ).scalars()
        )


async def test_seed_creates_students_and_data():
    await _seed_concepts()
    async with TestSessionFactory() as db:
        summary = await seed_fake_students(db, count=3, seed=1)

    assert summary["created"] == 3
    assert sum(summary["archetypes"].values()) == 3

    ids = await _seed_user_ids()
    assert len(ids) == 3

    async with TestSessionFactory() as db:
        for uid in ids:
            prof = (
                await db.execute(
                    select(StudentProfile).where(StudentProfile.user_id == uid)
                )
            ).scalar_one_or_none()
            assert prof is not None and prof.real_name
            members = (
                await db.execute(
                    select(func.count()).select_from(ClassMember).where(
                        ClassMember.user_id == uid
                    )
                )
            ).scalar_one()
            assert members == 1
            events = (
                await db.execute(
                    select(func.count()).select_from(CodingEvent).where(
                        CodingEvent.user_id == uid
                    )
                )
            ).scalar_one()
            assert events > 0
            mastery = (
                await db.execute(
                    select(func.count()).select_from(StudentMastery).where(
                        StudentMastery.user_id == uid
                    )
                )
            ).scalar_one()
            assert mastery > 0


async def test_seed_is_reproducible_and_idempotent():
    await _seed_concepts()
    async with TestSessionFactory() as db:
        await seed_fake_students(db, count=4, seed=7)
    async with TestSessionFactory() as db:
        summary2 = await seed_fake_students(db, count=4, seed=7)
    # 第二次一律 purge → 仍是 4 位，不累加、email 不撞號
    assert summary2["purged"] == 4
    assert len(await _seed_user_ids()) == 4


async def test_purge_removes_students_keeps_teacher_and_class():
    async with TestSessionFactory() as db:
        summary = await seed_fake_students(db, count=3, seed=2)
    class_id = uuid.UUID(summary["class_id"])

    async with TestSessionFactory() as db:
        removed = await purge_seed_students(db)
    assert removed == 3
    assert await _seed_user_ids() == []

    async with TestSessionFactory() as db:
        cls = (
            await db.execute(select(Classroom).where(Classroom.id == class_id))
        ).scalar_one_or_none()
        teacher = (
            await db.execute(
                select(User).where(User.email == f"seed-teacher@{SEED_EMAIL_DOMAIN}")
            )
        ).scalar_one_or_none()
    assert cls is not None  # 班級保留
    assert teacher is not None  # demo 教師保留


async def test_seeded_data_aggregates():
    await _seed_concepts()
    async with TestSessionFactory() as db:
        await seed_fake_students(db, count=3, seed=5)
    ids = await _seed_user_ids()

    async with TestSessionFactory() as db:
        # 至少一位學生有可聚合的執行事件 + dialogue_act 分布
        any_exec = False
        any_dialogue = False
        for uid in ids:
            m = await aggregate_user_behavior(db, uid)
            any_exec = any_exec or m.execution_count > 0
            any_dialogue = any_dialogue or bool(m.dialogue_act_distribution)
    assert any_exec
    assert any_dialogue
