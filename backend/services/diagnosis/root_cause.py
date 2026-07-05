"""根源弱點定位 — 沿 K1 多對多依賴圖回溯診斷（roadmap K3a/K3b/K3c）。

流程：
1. 觸發判定（K3a，stateless）：該 concept 最近的作答連續失敗達 N 次
2. 回溯（K3b）：沿 prerequisite closure（限深）找可疑前置節點 —
   「已曝光且 confidence 低」優先（有證據的弱點），其次「從未曝光」（盲區）
3. 抽診斷題（K3c）：對每個嫌疑節點從題庫抽 validated 題做微測驗；
   作答走既有 /quiz/submit 流程自然寫回 mastery，本層不重造判分
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.concept import Concept
from models.mastery import StudentMastery
from models.quiz import Question, StudentAnswer
from services.graph import get_prerequisite_closure
from services.mastery.decay import effective_confidence
from services.quiz.bank import pick_random_validated_question

# 觸發門檻：最近連續失敗次數
CONSECUTIVE_FAILURES_REQUIRED = 3
# 回溯層數 — 診斷聚焦近因，過深的前置留給下一輪診斷遞迴發現
CLOSURE_MAX_DEPTH = 3
# 低 confidence 門檻（與 quiz select 弱項門檻一致）
LOW_CONFIDENCE_THRESHOLD = 0.4
# 最多回報的嫌疑節點數
MAX_SUSPECTS = 3
# 觸發判定往回看的作答筆數上限（跨 concept 混雜，需 Python 過濾）
_RECENT_ANSWERS_WINDOW = 50


@dataclass(frozen=True)
class Suspect:
    """單一嫌疑前置節點。"""

    concept: Concept
    depth: int                  # 距目標 concept 的回溯層數（1 = 直接前置）
    confidence: float | None    # None = 從未曝光（盲區）
    exposure_count: int
    question_id: UUID | None    # 題庫診斷題；題庫無題時 None


@dataclass(frozen=True)
class DiagnosisResult:
    """診斷結果。"""

    target: Concept
    triggered: bool
    recent_failure_streak: int
    suspects: list[Suspect]


async def _recent_failure_streak(
    db: AsyncSession, user_id: UUID, tag: str
) -> int:
    """該 concept 最近的連續失敗筆數（由最新往回數，遇答對即停）。

    concept_tags 為 JSON 陣列，SQLite/PG contains 語法不同 →
    與 quiz/bank.py 同策略：撈最近視窗後 Python 過濾。
    """
    rows = (
        await db.execute(
            select(StudentAnswer.is_correct, Question.concept_tags)
            .join(Question, Question.id == StudentAnswer.question_id)
            .where(StudentAnswer.user_id == user_id)
            .order_by(desc(StudentAnswer.answered_at))
            .limit(_RECENT_ANSWERS_WINDOW)
        )
    ).all()

    streak = 0
    for is_correct, concept_tags in rows:
        if tag not in (concept_tags or []):
            continue
        if is_correct:
            break
        streak += 1
    return streak


async def _rank_suspects(
    db: AsyncSession,
    user_id: UUID,
    ancestors: list[tuple[Concept, int]],
) -> list[tuple[Concept, int, StudentMastery | None]]:
    """嫌疑排序：已曝光低 confidence（depth 淺、confidence 低優先）→ 未曝光盲區。

    已曝光且 confidence 高的前置節點不列入嫌疑（該概念大概率不是根因）。
    """
    ancestor_ids = [c.id for c, _ in ancestors]
    if not ancestor_ids:
        return []

    mastery_rows = (
        await db.execute(
            select(StudentMastery).where(
                StudentMastery.user_id == user_id,
                StudentMastery.concept_id.in_(ancestor_ids),
            )
        )
    ).scalars().all()
    mastery_by_id = {m.concept_id: m for m in mastery_rows}

    exposed_low: list[tuple[Concept, int, StudentMastery]] = []
    unexposed: list[tuple[Concept, int, None]] = []
    for concept, depth in ancestors:
        mastery = mastery_by_id.get(concept.id)
        if mastery is None:
            unexposed.append((concept, depth, None))
        # K6b：以衰減後 effective confidence 判嫌疑——久未練習的前置概念
        # 即使當年學會了，現在也可能是根因
        elif (
            effective_confidence(
                mastery.confidence, mastery.last_practiced_at, mastery.success_count
            )
            < LOW_CONFIDENCE_THRESHOLD
        ):
            exposed_low.append((concept, depth, mastery))

    exposed_low.sort(key=lambda t: (t[1], t[2].confidence))
    unexposed.sort(key=lambda t: (t[1], t[0].video_order or 0))
    return [*exposed_low, *unexposed][:MAX_SUSPECTS]


async def diagnose_root_cause(
    db: AsyncSession,
    user_id: UUID,
    tag: str,
) -> DiagnosisResult | None:
    """對指定 concept 執行根源弱點診斷。

    Returns:
        DiagnosisResult；tag 不存在回傳 None。
        未達觸發門檻時 triggered=False 且 suspects 為空（前端據此隱藏入口）。
    """
    closure = await get_prerequisite_closure(db, tag, max_depth=CLOSURE_MAX_DEPTH)
    if closure is None:
        return None

    streak = await _recent_failure_streak(db, user_id, tag)
    if streak < CONSECUTIVE_FAILURES_REQUIRED:
        return DiagnosisResult(
            target=closure.center,
            triggered=False,
            recent_failure_streak=streak,
            suspects=[],
        )

    suspects: list[Suspect] = []
    for concept, depth, mastery in await _rank_suspects(
        db, user_id, closure.ancestors
    ):
        question = await pick_random_validated_question(db, concept.tag)
        suspects.append(
            Suspect(
                concept=concept,
                depth=depth,
                confidence=mastery.confidence if mastery else None,
                exposure_count=mastery.exposure_count if mastery else 0,
                question_id=question.id if question else None,
            )
        )

    return DiagnosisResult(
        target=closure.center,
        triggered=True,
        recent_failure_streak=streak,
        suspects=suspects,
    )
