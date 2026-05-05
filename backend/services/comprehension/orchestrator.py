"""Comprehension orchestrator — 整合 LLM (epl/predict_output) 與 DB (crud)。

EPL（roadmap 2-6b）：
- start_epl_for_answer / submit_epl_for_answer

Predict Output（roadmap 2-6c）：
- start_predict_for_answer：限 coding 題型；LLM 生新測資 → JSON 存 prompt（input + expected）
- submit_predict_for_answer：兩階段比對 → 寫 answer/passed

設計取捨：
- generate 採「重置」語意：每次重新生成都清空 answer/passed，避免新題搭配舊答案
- grade 必須先 generate（缺 prompt → 400 *_NOT_STARTED）
- LLM 失敗：generate → 503（前端可重試）；grade → 200 + passed 反映退化結果
- predict 的 expected_output 存在 comprehension_prompt 的 JSON 結構中，不洩漏給前端 generate response
"""

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.quiz import ComprehensionType, Question, QuestionType, StudentAnswer
from services.comprehension.crud import _get_owned_answer
from services.comprehension.epl import (
    EplGenerationResult,
    EplGradeResult,
    generate_epl_prompt,
    grade_epl_answer,
)
from services.comprehension.mastery_hook import apply_comprehension_mastery
from services.comprehension.predict_output import (
    PredictGradeResult,
    generate_predict_test,
    grade_predict_answer,
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

    # 2-6e：通過/不通過驅動 BKT；passed=None 跳過（無有效信號）
    await apply_comprehension_mastery(db, user_id, question, result.passed)

    await db.commit()
    await db.refresh(answer)
    return answer, result


# === Predict Output (roadmap 2-6c) ===


def _extract_student_code(answer: StudentAnswer) -> str:
    """從 student_answer.answer 取出學生程式碼。"""
    return (answer.answer or {}).get("code", "")


async def start_predict_for_answer(
    db: AsyncSession, user_id: UUID, student_answer_id: UUID
) -> tuple[StudentAnswer, str]:
    """LLM 生成新測資，回 (updated_answer, test_input_for_display)。

    expected_output 與 input 一起 JSON 編碼後存入 comprehension_prompt，但回給前端時只露 input。

    Raises:
        AppError 404 STUDENT_ANSWER_NOT_FOUND
        AppError 422 PREDICT_OUTPUT_NOT_APPLICABLE — 非 coding 題型
        AppError 503 PREDICT_GENERATION_FAILED — LLM 失敗
    """
    answer = await _get_owned_answer(db, student_answer_id, user_id)
    question = await _load_question(db, answer.question_id)
    if question.type != QuestionType.CODING.value:
        raise AppError(
            422,
            "PREDICT_OUTPUT_NOT_APPLICABLE",
            f"預測輸出驗證僅支援 coding 題型，當前題型：{question.type}",
        )

    student_code = _extract_student_code(answer)
    result = await generate_predict_test(question, student_code)
    if result.test_input is None or result.expected_output is None:
        raise AppError(
            503,
            "PREDICT_GENERATION_FAILED",
            "AI 生成測資暫時不可用，請稍後再試",
        )

    answer.comprehension_type = ComprehensionType.PREDICT_OUTPUT.value
    answer.comprehension_prompt = json.dumps(
        {"input": result.test_input, "expected": result.expected_output},
        ensure_ascii=False,
    )
    # 重新生成 → 清空舊回答 / 通過狀態
    answer.comprehension_answer = None
    answer.comprehension_passed = None

    await db.commit()
    await db.refresh(answer)
    return answer, result.test_input


async def submit_predict_for_answer(
    db: AsyncSession,
    user_id: UUID,
    student_answer_id: UUID,
    student_predicted: str,
) -> tuple[StudentAnswer, PredictGradeResult]:
    """比對學生預測 vs 預存 expected_output。

    Raises:
        AppError 404 STUDENT_ANSWER_NOT_FOUND
        AppError 400 PREDICT_NOT_STARTED — 未先 generate（無 prompt 或 type 不符）
        AppError 500 PREDICT_PROMPT_CORRUPT — prompt 不是合法 JSON（理論上不該發生）
    """
    answer = await _get_owned_answer(db, student_answer_id, user_id)
    if (
        answer.comprehension_type != ComprehensionType.PREDICT_OUTPUT.value
        or not answer.comprehension_prompt
    ):
        raise AppError(
            400,
            "PREDICT_NOT_STARTED",
            "尚未生成預測測資，請先呼叫 generate",
        )

    try:
        prompt_data = json.loads(answer.comprehension_prompt)
        test_input = prompt_data["input"]
        expected_output = prompt_data["expected"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise AppError(
            500,
            "PREDICT_PROMPT_CORRUPT",
            "預測測資資料格式損壞，請重新生成",
        ) from exc

    student_code = _extract_student_code(answer)
    result = await grade_predict_answer(
        student_code, test_input, expected_output, student_predicted
    )

    answer.comprehension_answer = student_predicted
    answer.comprehension_passed = result.passed

    # 2-6e：predict 永遠回 bool（無 None fallback），一律驅動 BKT
    question = await _load_question(db, answer.question_id)
    await apply_comprehension_mastery(db, user_id, question, result.passed)

    await db.commit()
    await db.refresh(answer)
    return answer, result
