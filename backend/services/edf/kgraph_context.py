"""K-Graph 學生知識狀態 → EDF Feedback prompt 封裝（roadmap K4a）。

職責：
- 把 evidence 涉及的 concepts（直接命中或 edf_parent_tag 群組）的 BKT 狀態
  組成 prompt block，並依整體熟練度給出「鷹架指令」：
  低熟練 → 框架填空 / 逐行拆解；高熟練 → 只點 edge case
- best-effort：無資料回空字串（prompt 不變 = 原行為）、異常吞掉不擋教學回應
"""

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.concept import Concept
from models.mastery import StudentMastery
from services.edf.models import EvidenceResult

logger = logging.getLogger(__name__)

# 熟練度分級門檻（與 quiz select / K3 診斷的 0.4 弱項門檻一致）
LOW_CONFIDENCE = 0.4
HIGH_CONFIDENCE = 0.7
# prompt 內最多列出的 concept 數（弱者優先，控制 token）
MAX_ENTRIES = 6

_SCAFFOLD_LOW = (
    "鷹架指令：學生對相關概念熟練度偏低。把問題拆成一小步一小步引導，"
    "可提供含 TODO 的程式碼填空框架或逐行拆解；語氣多肯定學生已做對的部分。"
)
_SCAFFOLD_MID = (
    "鷹架指令：學生對相關概念有基礎但未穩固。用引導式提問確認理解，"
    "先讓學生自己嘗試，卡住再給方向提示。"
)
_SCAFFOLD_HIGH = (
    "鷹架指令：學生對相關概念已相當熟練。不要解釋基礎，"
    "直接點出 edge case、反例或更深入的思考方向；語氣可同儕式簡潔。"
)


@dataclass(frozen=True)
class _MasteryEntry:
    name_zh: str
    tag: str
    confidence: float
    exposure_count: int


def _scaffold_for(min_confidence: float) -> str:
    """以「最弱概念」決定鷹架等級 — 教學遷就短板而非平均值。"""
    if min_confidence < LOW_CONFIDENCE:
        return _SCAFFOLD_LOW
    if min_confidence < HIGH_CONFIDENCE:
        return _SCAFFOLD_MID
    return _SCAFFOLD_HIGH


def format_kgraph_block(entries: list[_MasteryEntry]) -> str:
    """把 mastery entries 渲染為 prompt block；空列表回空字串。"""
    if not entries:
        return ""
    lines = [
        f"- {e.name_zh}：熟練度 {e.confidence:.2f}（練習 {e.exposure_count} 次）"
        for e in entries
    ]
    scaffold = _scaffold_for(min(e.confidence for e in entries))
    return "學生知識狀態（依過往練習紀錄）：\n" + "\n".join(lines) + f"\n{scaffold}"


async def fetch_kgraph_block_safe(
    db: AsyncSession,
    user_id: UUID,
    evidence: EvidenceResult,
) -> str:
    """讀取 evidence 相關 concepts 的學生 mastery，組成 prompt block。

    解析範圍：`concepts.tag` 直接命中或 `edf_parent_tag` 群組命中，
    且該生已有 mastery row（未曝光概念無資料可述）。
    弱者優先排序，取前 MAX_ENTRIES 筆。無資料 / 異常 → 空字串。
    """
    tags = evidence.concept_tags
    if not tags:
        return ""
    try:
        rows = (
            await db.execute(
                select(
                    Concept.name_zh,
                    Concept.tag,
                    StudentMastery.confidence,
                    StudentMastery.exposure_count,
                )
                .join(StudentMastery, StudentMastery.concept_id == Concept.id)
                .where(
                    StudentMastery.user_id == user_id,
                    or_(Concept.tag.in_(tags), Concept.edf_parent_tag.in_(tags)),
                )
                .order_by(StudentMastery.confidence)
                .limit(MAX_ENTRIES)
            )
        ).all()
    except Exception as e:
        logger.warning("K-Graph context fetch failed (non-blocking): %r", e)
        return ""

    entries = [
        _MasteryEntry(
            name_zh=r.name_zh,
            tag=r.tag,
            confidence=r.confidence,
            exposure_count=r.exposure_count,
        )
        for r in rows
    ]
    return format_kgraph_block(entries)
