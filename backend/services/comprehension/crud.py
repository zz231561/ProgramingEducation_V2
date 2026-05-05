"""Comprehension CRUD service — student_answers 擴充欄位讀寫（roadmap 2-6a）。

職責邊界：
- 本層僅做 schema 驗證 + DB 讀寫，不做 LLM 生成 / 評分（屬 2-6b/c/d）。
- 擁有權檢查：非本人之 student_answer 一律回 404，避免列舉攻擊揭露存在性。
- upsert 而非 create：comprehension 是 student_answer 的擴充欄位，同一作答只會有一份結果，
  覆寫現有值（例如學生重做變體題）由 caller 透過 partial 欄位控制。
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.quiz import ComprehensionType, StudentAnswer


@dataclass(slots=True)
class ComprehensionUpdate:
    """upsert 時可寫入的欄位（皆為 nullable，未提供者保留原值）。"""

    comprehension_type: ComprehensionType | None = None
    comprehension_prompt: str | None = None
    comprehension_answer: str | None = None
    comprehension_passed: bool | None = None


async def _get_owned_answer(
    db: AsyncSession, student_answer_id: UUID, user_id: UUID
) -> StudentAnswer:
    """取得當前使用者擁有的 student_answer；不存在或非本人 → 404。"""
    answer = (
        await db.execute(
            select(StudentAnswer).where(StudentAnswer.id == student_answer_id)
        )
    ).scalar_one_or_none()
    if answer is None or answer.user_id != user_id:
        raise AppError(
            404,
            "STUDENT_ANSWER_NOT_FOUND",
            f"找不到作答紀錄：{student_answer_id}",
        )
    return answer


async def get_comprehension(
    db: AsyncSession, student_answer_id: UUID, user_id: UUID
) -> StudentAnswer:
    """讀取 comprehension 狀態；回傳完整 StudentAnswer 由 caller 取需要的欄位。"""
    return await _get_owned_answer(db, student_answer_id, user_id)


async def upsert_comprehension(
    db: AsyncSession,
    student_answer_id: UUID,
    user_id: UUID,
    payload: ComprehensionUpdate,
) -> StudentAnswer:
    """寫入或更新 comprehension 欄位。提供者覆寫，未提供者保留原值。

    Raises:
        AppError 404 STUDENT_ANSWER_NOT_FOUND — 作答不存在或非本人擁有
    """
    answer = await _get_owned_answer(db, student_answer_id, user_id)

    if payload.comprehension_type is not None:
        answer.comprehension_type = payload.comprehension_type.value
    if payload.comprehension_prompt is not None:
        answer.comprehension_prompt = payload.comprehension_prompt
    if payload.comprehension_answer is not None:
        answer.comprehension_answer = payload.comprehension_answer
    if payload.comprehension_passed is not None:
        answer.comprehension_passed = payload.comprehension_passed

    await db.commit()
    await db.refresh(answer)
    return answer
