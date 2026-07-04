"""K-Graph state prompt 封裝測試（roadmap K4a）。"""

import uuid

import pytest

from models.concept import Concept
from models.mastery import StudentMastery
from services.edf.kgraph_context import (
    fetch_kgraph_block_safe,
    format_kgraph_block,
    _MasteryEntry,
)
from services.edf.models import BloomLevel, ErrorType, EvidenceResult
from tests.helpers import TestSessionFactory


def _evidence(tags: list[str]) -> EvidenceResult:
    return EvidenceResult(
        error_type=ErrorType.LOGIC,
        error_message="",
        concept_tags=tags,
        bloom_level=BloomLevel.APPLY,
        bloom_reasoning="",
        code_analysis="",
    )


def _entry(name: str, conf: float, exposure: int = 3) -> _MasteryEntry:
    return _MasteryEntry(
        name_zh=name, tag=name, confidence=conf, exposure_count=exposure
    )


# === format_kgraph_block：鷹架分級 ===

def test_format_empty_entries_returns_empty_string():
    assert format_kgraph_block([]) == ""


def test_format_low_confidence_gives_scaffold_low():
    """最弱概念 < 0.4 → 填空 / 拆解鷹架。"""
    block = format_kgraph_block([_entry("while 迴圈", 0.2), _entry("for 迴圈", 0.8)])
    assert "學生知識狀態" in block
    assert "0.20" in block
    assert "填空" in block or "拆" in block


def test_format_mid_confidence_gives_scaffold_mid():
    block = format_kgraph_block([_entry("for 迴圈", 0.5)])
    assert "引導式提問" in block


def test_format_high_confidence_gives_scaffold_high():
    """全部 > 0.7 → 只點 edge case。"""
    block = format_kgraph_block([_entry("for 迴圈", 0.9)])
    assert "edge case" in block


# === fetch_kgraph_block_safe：DB 解析 ===

async def _seed(user_id: uuid.UUID) -> None:
    async with TestSessionFactory() as db:
        direct = Concept(
            tag="cpp-29-for", name_zh="for迴圈", name_en="for",
            description="", difficulty_level=2, category="迴圈",
            video_order=29, edf_parent_tag="control-flow",
        )
        grouped = Concept(
            tag="cpp-30-while", name_zh="while迴圈", name_en="while",
            description="", difficulty_level=2, category="迴圈",
            video_order=30, edf_parent_tag="control-flow",
        )
        unexposed = Concept(
            tag="cpp-25-if", name_zh="if-else", name_en="if",
            description="", difficulty_level=2, category="流程控制",
            video_order=25, edf_parent_tag="control-flow",
        )
        db.add_all([direct, grouped, unexposed])
        await db.flush()
        db.add_all([
            StudentMastery(
                user_id=user_id, concept_id=direct.id,
                confidence=0.3, exposure_count=4, success_count=1, error_count=3,
            ),
            StudentMastery(
                user_id=user_id, concept_id=grouped.id,
                confidence=0.8, exposure_count=5, success_count=5, error_count=0,
            ),
        ])
        await db.commit()


@pytest.mark.asyncio
async def test_fetch_resolves_direct_and_parent_group_exposed_only():
    """直接命中 + parent group 已曝光成員入列；未曝光 concept 不出現。"""
    user_id = uuid.uuid4()
    await _seed(user_id)

    async with TestSessionFactory() as db:
        block = await fetch_kgraph_block_safe(db, user_id, _evidence(["control-flow"]))

    assert "for迴圈" in block
    assert "while迴圈" in block
    assert "if-else" not in block
    # 最弱 0.3 < 0.4 → 低熟練鷹架
    assert "填空" in block or "拆" in block


@pytest.mark.asyncio
async def test_fetch_returns_empty_without_mastery_data():
    """該生無任何 mastery row → 空字串（prompt 維持原行為）。"""
    user_id = uuid.uuid4()
    await _seed(uuid.uuid4())  # 別人的資料

    async with TestSessionFactory() as db:
        block = await fetch_kgraph_block_safe(db, user_id, _evidence(["control-flow"]))

    assert block == ""


@pytest.mark.asyncio
async def test_fetch_returns_empty_for_no_tags():
    async with TestSessionFactory() as db:
        assert await fetch_kgraph_block_safe(db, uuid.uuid4(), _evidence([])) == ""
