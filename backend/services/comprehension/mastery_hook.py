"""Comprehension → BKT 精熟度更新 hook（roadmap 2-6e）。

設計：
- 通過（passed=True）→ Evidence(error_type=NONE) → BKT 視為「答對」上調 confidence
- 不通過（passed=False）→ Evidence(error_type=LOGIC) → BKT 視為「答錯」下調 confidence
- 評分失敗（passed=None，例如 EPL LLM fallback）→ 不更新（無有效信號，避免噪音影響 mastery）

容錯（與 quiz/orchestrator.submit_answer 同哲學）：
- update_mastery 內部失敗 → swallow，不擋 comprehension 寫入流程
- 不 commit；caller 在自己的 transaction 末尾 commit 一次
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.quiz import Question
from services.edf.models import BloomLevel, ErrorType, EvidenceResult
from services.mastery import update_mastery


async def apply_comprehension_mastery(
    db: AsyncSession,
    user_id: UUID,
    question: Question,
    passed: bool | None,
) -> None:
    """以 comprehension 結果驅動 BKT 更新。passed=None → no-op。

    Args:
        db: 與 caller 共用的 async session（不 commit）
        user_id: 學生
        question: comprehension 對應的原題（提供 concept_tags + bloom_level）
        passed: comprehension 是否通過（None → 不更新）
    """
    if passed is None:
        return

    evidence = EvidenceResult(
        error_type=ErrorType.NONE if passed else ErrorType.LOGIC,
        error_message="",
        concept_tags=list(question.concept_tags),
        bloom_level=BloomLevel(question.bloom_level),
        bloom_reasoning="from comprehension check",
        code_analysis="",
    )
    try:
        await update_mastery(db, user_id, evidence)
    except Exception:
        # mastery 失敗不阻擋 comprehension 寫入（與 quiz/submit 容錯一致）
        pass
