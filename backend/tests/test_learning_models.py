"""LearningPath / LearningUnit model tests（roadmap 3-1a）。

涵蓋：
- metadata / 欄位 / 索引 / UNIQUE / CHECK 結構
- 實際 INSERT 驗證 default / FK CASCADE / UNIQUE 衝突 / status CHECK 阻擋非法值
"""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from core.database import Base
from models.concept import Concept
from models.learning import LearningPath, LearningUnit, LearningUnitStatus
from models.user import User
from tests.helpers import TestSessionFactory


# === metadata / structure ===


def test_learning_path_in_metadata():
    assert "learning_paths" in Base.metadata.tables


def test_learning_unit_in_metadata():
    assert "learning_units" in Base.metadata.tables


def test_learning_path_columns():
    cols = {c.name for c in LearningPath.__table__.columns}
    assert cols == {"id", "user_id", "title", "description", "created_at", "updated_at"}


def test_learning_unit_columns():
    cols = {c.name for c in LearningUnit.__table__.columns}
    assert cols == {
        "id", "path_id", "concept_id", "order_index",
        "content", "status", "completed_at",
    }


def test_learning_unit_status_enum_values():
    assert {s.value for s in LearningUnitStatus} == {
        "locked", "available", "in_progress", "completed"
    }


# === DB integration ===


async def _seed_user_and_concept() -> tuple[uuid.UUID, uuid.UUID]:
    async with TestSessionFactory() as db:
        u = User(
            email=f"learn-{uuid.uuid4().hex[:8]}@test.com",
            name="Learn",
            google_id=f"g-{uuid.uuid4().hex[:8]}",
        )
        c = Concept(
            tag=f"tag-{uuid.uuid4().hex[:8]}",
            name_zh="X",
            name_en="X",
            description="x",
            difficulty_level=1,
            category="基礎",
        )
        db.add_all([u, c])
        await db.commit()
        await db.refresh(u)
        await db.refresh(c)
        return u.id, c.id


@pytest.mark.asyncio
async def test_insert_learning_path_with_defaults():
    user_id, _ = await _seed_user_and_concept()
    async with TestSessionFactory() as db:
        path = LearningPath(user_id=user_id, title="C++ 入門")
        db.add(path)
        await db.commit()
        await db.refresh(path)
        assert path.description == ""
        assert path.created_at is not None


@pytest.mark.asyncio
async def test_insert_learning_unit_default_status_locked():
    user_id, concept_id = await _seed_user_and_concept()
    async with TestSessionFactory() as db:
        path = LearningPath(user_id=user_id, title="Path")
        db.add(path)
        await db.flush()
        unit = LearningUnit(
            path_id=path.id,
            concept_id=concept_id,
            order_index=0,
            content={"summary": "..."},
        )
        db.add(unit)
        await db.commit()
        await db.refresh(unit)
        assert unit.status == LearningUnitStatus.LOCKED.value
        assert unit.completed_at is None


@pytest.mark.asyncio
async def test_unit_path_order_unique():
    user_id, concept_id = await _seed_user_and_concept()
    async with TestSessionFactory() as db:
        path = LearningPath(user_id=user_id, title="P")
        db.add(path)
        await db.flush()
        db.add(LearningUnit(
            path_id=path.id, concept_id=concept_id,
            order_index=0, content={},
        ))
        db.add(LearningUnit(
            path_id=path.id, concept_id=concept_id,
            order_index=0, content={},
        ))  # 同 path + 同 order → UNIQUE 衝突
        with pytest.raises(IntegrityError):
            await db.commit()


@pytest.mark.asyncio
async def test_unit_status_check_blocks_invalid():
    user_id, concept_id = await _seed_user_and_concept()
    async with TestSessionFactory() as db:
        path = LearningPath(user_id=user_id, title="P")
        db.add(path)
        await db.flush()
        db.add(LearningUnit(
            path_id=path.id, concept_id=concept_id,
            order_index=0, content={}, status="invalid_state",
        ))
        with pytest.raises(IntegrityError):
            await db.commit()


@pytest.mark.asyncio
async def test_unit_order_index_non_negative_check():
    """order_index < 0 違反 CHECK constraint。"""
    user_id, concept_id = await _seed_user_and_concept()
    async with TestSessionFactory() as db:
        path = LearningPath(user_id=user_id, title="P")
        db.add(path)
        await db.flush()
        db.add(LearningUnit(
            path_id=path.id, concept_id=concept_id,
            order_index=-1, content={},
        ))
        with pytest.raises(IntegrityError):
            await db.commit()


def test_path_user_fk_ondelete_cascade_declared():
    """User 刪除 → 學生路徑連動刪除（DB-level 由 PG 強制；本測試僅驗 schema 宣告）。"""
    fk = next(iter(LearningPath.__table__.foreign_keys))
    assert fk.ondelete == "CASCADE"


def test_unit_path_fk_ondelete_cascade_declared():
    """Path 刪除 → units 連動刪除（同上，僅驗宣告）。"""
    path_fk = next(
        fk for fk in LearningUnit.__table__.foreign_keys
        if fk.column.table.name == "learning_paths"
    )
    assert path_fk.ondelete == "CASCADE"
