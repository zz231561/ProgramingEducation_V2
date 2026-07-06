"""6-3d 弱項綜合測驗組——藍圖與節點選擇（決定「要出什麼」，不呼叫 LLM）。

設計依據（references.md §5.1 待標注）：
- 綜合題比例隨掌握度自適應：掌握度低 → 偏單節點精準補強；回升 → 提高綜合題比例
  （CAT content balancing + 概念圖多跳評測）
- coding 每題 1 弱項目標 + 2 已掌握相連節點當鷹架（ZPD + interleaving，避免全弱項過難）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.concept import Concept
from models.mastery import StudentMastery
from models.quiz import QuestionType
from services.graph.traversal import get_prerequisite_closure
from services.mastery.decay import effective_confidence
from services.quiz.select import WEAK_THRESHOLD

# coding 題數：小組 1 題、大組（>=25）2 題
CODING_SMALL = 1
CODING_LARGE = 2
LARGE_SET_THRESHOLD = 25
# 綜合題比例隨掌握度成長：弱 0.2 → 強 0.6
MULTI_FRACTION_BASE = 0.2
MULTI_FRACTION_SPAN = 0.4
# 已掌握門檻（當 coding 鷹架節點）
MASTERED_THRESHOLD = 0.6
# 綜合 MC 每題附帶的相關節點數；coding 鷹架節點數
MULTI_RELATED = 1
CODING_SCAFFOLD = 2


@dataclass(frozen=True)
class SetBlueprint:
    """一組測驗的題型配額。"""

    single_mc: int
    multi_mc: int
    coding: int

    @property
    def total(self) -> int:
        return self.single_mc + self.multi_mc + self.coding


def compute_blueprint(count: int, overall_mastery: float) -> SetBlueprint:
    """依題數與整體掌握度算配額。掌握度越高 → 綜合題越多。"""
    coding = CODING_LARGE if count >= LARGE_SET_THRESHOLD else CODING_SMALL
    mc = max(0, count - coding)
    m = min(1.0, max(0.0, overall_mastery))
    multi_fraction = MULTI_FRACTION_BASE + MULTI_FRACTION_SPAN * m
    multi_mc = round(mc * multi_fraction)
    single_mc = mc - multi_mc
    return SetBlueprint(single_mc=single_mc, multi_mc=multi_mc, coding=coding)


@dataclass(frozen=True)
class MasterySnapshot:
    """學生掌握度快照（effective confidence 衰減後）。"""

    overall: float  # 已曝光概念的平均 effective confidence（無資料 → 0）
    weak: list[Concept]  # eff < WEAK_THRESHOLD，弱→強排序
    mastered_tags: set[str]  # eff >= MASTERED_THRESHOLD


async def mastery_snapshot(db: AsyncSession, user_id: UUID) -> MasterySnapshot:
    """撈學生已曝光概念，算 effective confidence，分出弱項 / 已掌握。"""
    rows = list(
        (
            await db.execute(
                select(
                    Concept,
                    StudentMastery.confidence,
                    StudentMastery.last_practiced_at,
                    StudentMastery.success_count,
                )
                .join(StudentMastery, StudentMastery.concept_id == Concept.id)
                .where(
                    StudentMastery.user_id == user_id,
                    StudentMastery.exposure_count >= 1,
                )
            )
        ).tuples()
    )
    if not rows:
        return MasterySnapshot(overall=0.0, weak=[], mastered_tags=set())

    effs: list[tuple[Concept, float]] = [
        (c, effective_confidence(conf, last_at, successes))
        for c, conf, last_at, successes in rows
    ]
    overall = sum(e for _, e in effs) / len(effs)
    weak = [c for c, e in sorted(effs, key=lambda x: x[1]) if e < WEAK_THRESHOLD]
    mastered_tags = {c.tag for c, e in effs if e >= MASTERED_THRESHOLD}
    return MasterySnapshot(overall=overall, weak=weak, mastered_tags=mastered_tags)


@dataclass(frozen=True)
class QuestionPlan:
    """單題出題計畫：目標概念 + 相關概念（綜合題 / coding 鷹架）。"""

    question_type: QuestionType
    target: Concept
    extra: list[Concept] = field(default_factory=list)


async def _related_concepts(
    db: AsyncSession, tag: str, limit: int, prefer_tags: set[str] | None = None
) -> list[Concept]:
    """取某概念的相關（前置）概念；prefer_tags 提供時優先選其中的（如已掌握節點）。"""
    closure = await get_prerequisite_closure(db, tag, max_depth=2)
    if closure is None:
        return []
    ancestors = [c for c, _ in closure.ancestors]
    if prefer_tags:
        preferred = [c for c in ancestors if c.tag in prefer_tags]
        others = [c for c in ancestors if c.tag not in prefer_tags]
        ordered = preferred + others
    else:
        ordered = ancestors
    return ordered[:limit]


def _cycle(items: list, n: int) -> list:
    """從 items 循環取 n 個（items 空 → 空 list）。"""
    if not items:
        return []
    return [items[i % len(items)] for i in range(n)]


async def plan_questions(
    db: AsyncSession, snapshot: MasterySnapshot, blueprint: SetBlueprint
) -> list[QuestionPlan]:
    """依藍圖 + 快照產出逐題計畫。

    - 單節點 MC：循環弱項概念
    - 綜合 MC：弱項 + 1 個相關（前置）概念
    - coding：弱項目標 + 2 個已掌握相連節點（鷹架）；不足則補任意相關節點
    """
    weak = snapshot.weak
    plans: list[QuestionPlan] = []

    for target in _cycle(weak, blueprint.single_mc):
        plans.append(QuestionPlan(QuestionType.MULTIPLE_CHOICE, target))

    for target in _cycle(weak, blueprint.multi_mc):
        extra = await _related_concepts(db, target.tag, MULTI_RELATED)
        plans.append(QuestionPlan(QuestionType.MULTIPLE_CHOICE, target, extra))

    for target in _cycle(weak, blueprint.coding):
        scaffold = await _related_concepts(
            db, target.tag, CODING_SCAFFOLD, prefer_tags=snapshot.mastered_tags
        )
        plans.append(QuestionPlan(QuestionType.CODING, target, scaffold))

    return plans
