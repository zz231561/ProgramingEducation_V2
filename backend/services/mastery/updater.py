"""精熟度更新 — BKT 線上 Bayes 更新 + EDF Evidence 整合。

設計原則（CLAUDE.md 守則 #7）：
- 使用 pyBKT 套件（已 `uv pip install pyBKT`）— 但 pyBKT 的 Model/Roster 需要先用真實學生資料 fit
- Cold-start 階段（無歷史資料）改用標準 BKT Bayes 公式（Corbett & Anderson 1995，公開數學）
- 未來 Phase 5 行為分析有真實資料後，跑 `pyBKT.Model.fit(df)` 學出 per-concept 參數，
  把學到的 P(L0)/P(T)/P(S)/P(G) 餵入此處的 BKTParams 即可，**演算法本身不需改**
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.concept import Concept
from models.mastery import StudentMastery
from services.edf.models import ErrorType, EvidenceResult


@dataclass(frozen=True)
class BKTParams:
    """單一概念的 BKT 四參數。"""

    prior: float    # P(L0)：學生在初次互動前已掌握此概念的機率
    learn: float    # P(T)：每次互動後從「未掌握」轉為「掌握」的機率
    slip: float     # P(S)：已掌握但答錯的機率
    guess: float    # P(G)：未掌握但答對的機率


# Cold-start 預設參數（pyBKT 範例 + 教育文獻常用值）
# 之後 Phase 5 用 pyBKT.fit() 學出 per-concept 參數覆蓋此預設
BKT_DEFAULT_PARAMS = BKTParams(prior=0.3, learn=0.3, slip=0.1, guess=0.2)


def bkt_online_update(
    prior: float,
    correct: bool,
    params: BKTParams = BKT_DEFAULT_PARAMS,
) -> float:
    """以單一觀察更新 BKT 精熟機率。

    步驟（兩階段）：
    1. **Bayes update**：給定觀察（correct/incorrect），更新「學生此刻已掌握」的後驗機率
    2. **Learning transition**：套用 P(T) — 即使答錯仍有機率新學會

    Args:
        prior: 觀察前的精熟機率 P(L_t)
        correct: 此次互動是否答對
        params: BKT 四參數（預設 BKT_DEFAULT_PARAMS）

    Returns:
        觀察+學習後的新機率 P(L_t+1)，clamp 至 [0, 1]
    """
    if correct:
        numerator = prior * (1 - params.slip)
        denominator = numerator + (1 - prior) * params.guess
    else:
        numerator = prior * params.slip
        denominator = numerator + (1 - prior) * (1 - params.guess)

    posterior = numerator / denominator if denominator > 0 else prior
    new_state = posterior + (1 - posterior) * params.learn
    return max(0.0, min(1.0, new_state))


async def _get_concept_id_by_tag(db: AsyncSession, tag: str) -> UUID | None:
    """以 tag 取 concept.id；找不到回傳 None（容錯：跳過該 tag 不擲錯）。"""
    return (
        await db.execute(select(Concept.id).where(Concept.tag == tag))
    ).scalar_one_or_none()


async def _upsert_mastery(
    db: AsyncSession,
    user_id: UUID,
    concept_id: UUID,
    correct: bool,
    bloom_level: int,
) -> StudentMastery:
    """Lazy-create 或更新 (user, concept) 的 mastery row。"""
    stmt = select(StudentMastery).where(
        StudentMastery.user_id == user_id,
        StudentMastery.concept_id == concept_id,
    )
    mastery = (await db.execute(stmt)).scalar_one_or_none()

    if mastery is None:
        # 首次互動：以 BKT prior 為 P(L_t)，套一次更新
        new_confidence = bkt_online_update(BKT_DEFAULT_PARAMS.prior, correct)
        mastery = StudentMastery(
            user_id=user_id,
            concept_id=concept_id,
            confidence=new_confidence,
            exposure_count=1,
            success_count=1 if correct else 0,
            error_count=0 if correct else 1,
            bloom_level=bloom_level,
            last_practiced_at=datetime.now(timezone.utc),
        )
        db.add(mastery)
    else:
        mastery.confidence = bkt_online_update(mastery.confidence, correct)
        mastery.exposure_count += 1
        if correct:
            mastery.success_count += 1
        else:
            mastery.error_count += 1
        # 取已達到的最高 Bloom 等級
        if mastery.bloom_level is None or bloom_level > mastery.bloom_level:
            mastery.bloom_level = bloom_level
        mastery.last_practiced_at = datetime.now(timezone.utc)

    return mastery


async def update_mastery(
    db: AsyncSession,
    user_id: UUID,
    evidence: EvidenceResult,
) -> list[StudentMastery]:
    """依 EDF Evidence 結果更新所有相關 concept 的精熟度。

    correct 信號：`evidence.error_type == ErrorType.NONE`（程式碼無錯）。
    對 evidence.concept_tags 中每個 tag，lazy-fetch/create mastery row 並套 BKT 更新。
    呼叫端負責 commit（本函式只 add/modify，不 commit）。

    Args:
        db: SQLAlchemy async session（與呼叫端共用 transaction）
        user_id: 互動的學生
        evidence: EDF Evidence 層輸出

    Returns:
        本次更新的 StudentMastery 列表（順序對應 evidence.concept_tags 中找得到 concept 的 tags）
    """
    correct = evidence.error_type == ErrorType.NONE
    bloom = int(evidence.bloom_level)

    updated: list[StudentMastery] = []
    for tag in evidence.concept_tags:
        concept_id = await _get_concept_id_by_tag(db, tag)
        if concept_id is None:
            continue  # tag 不在 concepts 表（例如 LLM 產生的非標準 tag）— 跳過
        mastery = await _upsert_mastery(db, user_id, concept_id, correct, bloom)
        updated.append(mastery)

    return updated
