"""Comprehension orchestrator — 整合 LLM (epl.py) 與 DB (crud.py)（roadmap 2-6b）。

兩條主流程：
- start_epl_for_answer：取作答 + 題目 → LLM 出 EPL 題 → 寫 type/prompt（清空舊 answer/passed）
- submit_epl_for_answer：取作答 + 題目 + 已存 prompt → LLM 評分 → 寫 answer/passed

設計取捨：
- generate 採「重置」語意：每次重新生成都清空 comprehension_answer/passed，避免新題搭配舊答案
  造成資料錯亂（不走 crud.upsert_comprehension 的 partial 更新，直接改 model）。
- grade 必須先 generate（comprehension_type='epl' + prompt 非空）→ 否則 400 EPL_NOT_STARTED。
- LLM 失敗：generate fallback → 503 EPL_GENERATION_FAILED（前端可重試）；
  grade fallback → 200 但 passed=None（讓前端顯示「評分失敗請重試」，不阻擋學生繼續）。
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.quiz import ComprehensionType, Question, StudentAnswer
from services.comprehension.crud import _get_owned_answer
from services.comprehension.epl import (
    EplGenerationResult,
    EplGradeResult,
    generate_epl_prompt,
    grade_epl_answer,
)


async def _load_question(db: AsyncSession, question_id: UUID) -> Question:
    question = (
        await db.execute(select(Question).where(Question.id == question_id))
    ).scalar_one_or_none()
    if question is None:
        # 通常不會發生（FK ondelete=CASCADE），但防呆
        raise AppError(404, "QUESTION_NOT_FOUND", f"找不到題目：{question_id}")
    return question


async def start_epl_for_answer(
    db: AsyncSession, user_id: UUID, student_answer_id: UUID
) -> tuple[StudentAnswer, EplGenerationResult]:
    """LLM 生成 EPL 題並寫入 student_answers。重新生成會清空舊 answer/passed。

    Raises:
        AppError 404 STUDENT_ANSWER_NOT_FOUND — 不存在或非本人擁有
        AppError 503 EPL_GENERATION_FAILED — LLM 失敗（前端可重試）
    """
    answer = await _get_owned_answer(db, student_answer_id, user_id)
    question = await _load_question(db, answer.question_id)

    result = await generate_epl_prompt(question, answer)
    if result.prompt is None:
        raise AppError(
            503,
            "EPL_GENERATION_FAILED",
            "AI 出題暫時不可用，請稍後再試",
        )

    answer.comprehension_type = ComprehensionType.EPL.value
    answer.comprehension_prompt = result.prompt
    # 重新生成 → 清空舊回答 / 通過狀態
    answer.comprehension_answer = None
    answer.comprehension_passed = None

    await db.commit()
    await db.refresh(answer)
    return answer, result


async def submit_epl_for_answer(
    db: AsyncSession,
    user_id: UUID,
    student_answer_id: UUID,
    epl_answer: str,
) -> tuple[StudentAnswer, EplGradeResult]:
    """LLM 評分學生 EPL 回答並寫入 student_answers。

    Raises:
        AppError 404 STUDENT_ANSWER_NOT_FOUND — 不存在或非本人擁有
        AppError 400 EPL_NOT_STARTED — 尚未呼叫 generate（無 prompt）
    """
    answer = await _get_owned_answer(db, student_answer_id, user_id)
    if (
        answer.comprehension_type != ComprehensionType.EPL.value
        or not answer.comprehension_prompt
    ):
        raise AppError(
            400,
            "EPL_NOT_STARTED",
            "尚未生成 EPL 題目，請先呼叫 generate",
        )

    question = await _load_question(db, answer.question_id)
    result = await grade_epl_answer(
        question, answer, answer.comprehension_prompt, epl_answer
    )

    # 寫入學生回答（即使評分失敗也保留答案，方便重新評分）
    answer.comprehension_answer = epl_answer
    answer.comprehension_passed = result.passed  # 可能為 None（fallback）

    await db.commit()
    await db.refresh(answer)
    return answer, result
