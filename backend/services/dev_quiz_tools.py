"""開發者模式 quiz 工具（DEV-8/9）— 診斷模擬 + 題庫檢視。

僅供 `/dev/*` 端點使用（入口一律掛 `require_dev_user`）。
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.concept import Concept
from models.quiz import Question, QuestionSource, QuestionType, StudentAnswer
from services.diagnosis import diagnose_root_cause
from services.diagnosis.root_cause import DiagnosisResult

logger = logging.getLogger(__name__)

# 模擬答錯用的 stub 題目 stem 前綴（辨識用，避免與真題混淆）
_STUB_STEM_PREFIX = "[dev] 診斷模擬題"


async def list_questions_by_tag(db: AsyncSession, tag: str) -> list[Question]:
    """列出 concept_tags 含指定 tag 的題庫題目（新→舊）。

    concept_tags 為 JSON 陣列，SQLite/PG contains 語法不同 → python 端過濾
    （與 diagnosis 同款作法；dev 工具題量小，全掃可接受）。
    """
    rows = (
        await db.execute(select(Question).order_by(Question.created_at.desc()))
    ).scalars()
    return [q for q in rows if tag in (q.concept_tags or [])]


async def _find_or_create_stub_question(db: AsyncSession, tag: str) -> Question:
    """找一題含此 tag 的既有題目；沒有就建 stub（診斷 streak 需要 question join）。"""
    existing = await list_questions_by_tag(db, tag)
    if existing:
        return existing[0]
    question = Question(
        type=QuestionType.MULTIPLE_CHOICE.value,
        concept_tags=[tag],
        bloom_level=2,
        difficulty=2,
        content={"stem": f"{_STUB_STEM_PREFIX}：{tag}", "options": [], "answer": 0},
        source=QuestionSource.GENERATED.value,
        validated=False,
    )
    db.add(question)
    await db.flush()
    return question


async def simulate_failures(
    db: AsyncSession,
    user_id: uuid.UUID,
    tag: str,
    count: int,
) -> DiagnosisResult:
    """注入指定 concept 連續答錯 N 次的作答紀錄，回傳最新診斷結果。

    answered_at 以毫秒遞增確保排序確定性（streak 依 answered_at desc 計算）。
    """
    concept = (
        await db.execute(select(Concept).where(Concept.tag == tag))
    ).scalar_one_or_none()
    if concept is None:
        raise AppError(404, "CONCEPT_NOT_FOUND", f"找不到 concept: {tag}")

    question = await _find_or_create_stub_question(db, tag)
    now = datetime.now(timezone.utc)
    for i in range(count):
        db.add(
            StudentAnswer(
                user_id=user_id,
                question_id=question.id,
                answer={"dev_simulated": True},
                is_correct=False,
                answered_at=now + timedelta(milliseconds=i),
            )
        )
    await db.commit()
    logger.info("[dev] simulate_failures user=%s tag=%s count=%d", user_id, tag, count)

    result = await diagnose_root_cause(db, user_id, tag)
    if result is None:  # concept 已驗證存在，理論上不會發生
        raise AppError(404, "CONCEPT_NOT_FOUND", f"找不到 concept: {tag}")
    return result
