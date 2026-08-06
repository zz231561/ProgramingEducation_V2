"""需要 API 前置的三型 persona：P2 反思流、P5 進階型、P7 Quiz+診斷流。"""

from typing import Any

from sqlalchemy import text

from scripts.eval_coddy.client import PersonaClient
from scripts.eval_coddy.personas import LEAP_YEAR_PARTIAL, OVERFLOW_CODE
from scripts.eval_coddy.probe import Session, shift_last_practiced, user_id_by_email

TAG = "cpp-25-if-else"


async def question_answer_info(question_id: str) -> dict:
    """從 DB 取 MC 題正解（模擬「刻意答錯」用）。"""
    async with Session() as db:
        row = (
            await db.execute(
                text("SELECT content FROM questions WHERE id = :i"),
                {"i": question_id},
            )
        ).first()
    content = row[0]
    return {
        "answer_index": content.get("answer_index"),
        "n_options": len(content.get("options", [])),
    }


async def p2_reflection_flow(client: PersonaClient, dialogue) -> dict[str, Any]:
    """按部就班型：題庫抽 coding 題 → 反思 → kickoff → 帶反思提問。"""
    steps: dict[str, Any] = {}
    q = await client.api(
        "GET", "/quiz/from-bank",
        params={"concept_tag": TAG, "question_type": "coding"},
    )
    steps["question"] = {"id": q.get("id"), "type": q.get("type")}

    reflection = await client.api(
        "POST", "/reflection",
        json={
            "source_type": "quiz",
            "source_id": q["id"],
            "problem_understanding": "要判斷輸入的年份是不是閏年，輸出 yes 或 no",
            "planned_steps": ["用 cin 讀入年份", "用 if-else 判斷能否被 4 整除", "輸出結果"],
            "expected_concepts": "if-else 條件判斷、模數運算",
        },
    )
    steps["reflection"] = {
        "id": reflection.get("id"),
        "quality_score": reflection.get("quality_score"),
        "followup_question": reflection.get("followup_question"),
    }

    kickoff = await client.api(
        "POST", "/chat/reflection-kickoff",
        json={"reflection_id": reflection["id"]},
    )
    client.session_id = kickoff.get("session_id")
    steps["kickoff_message"] = (kickoff.get("assistant_message") or {}).get("content")

    steps["turns"] = await dialogue(
        client,
        [
            {
                "message": "我照計畫寫了一版，閏年判斷除了被4整除還有什麼要注意的嗎？",
                "code": LEAP_YEAR_PARTIAL,
                "execution_result": None,
                "reflection_id": reflection["id"],
                "expect": "reflection_injected=true；可引用學生計畫；RAG 命中 if-else 章節",
            },
            {
                "message": "懂了，那 % 運算子在老師影片的哪一段有講？",
                "code": LEAP_YEAR_PARTIAL,
                "execution_result": None,
                "reflection_id": reflection["id"],
                "expect": "7-C2a 起致謝不再歸零（只有成功執行歸零）→ reveal 隨追問累加；模數章節 RAG 命中；不捏造時間點",
            },
        ],
    )
    return steps


async def p5_advanced_flow(client: PersonaClient, dialogue) -> dict[str, Any]:
    """進階挑戰型：DEV 調高熟練 + 撥回練習時間（驗 K6b 衰減）→ edge case 提問。"""
    steps: dict[str, Any] = {}
    seed = await client.api(
        "PUT", "/dev/mastery",
        json={"tags": [TAG, "cpp-15-arithmetic", "cpp-16-modulo"], "confidence": 0.9},
    )
    steps["mastery_seed"] = seed

    uid = await user_id_by_email(client.email)
    shifted = await shift_last_practiced(uid, "cpp-16-modulo", 30)
    steps["decay_shift"] = {"tag": "cpp-16-modulo", "days": 30, "rows": shifted}

    steps["turns"] = await dialogue(
        client,
        [
            {
                "message": "這段相加會 overflow，我想確認 C++ 標準對 signed integer overflow 的行為定義是什麼？",
                "code": OVERFLOW_CODE,
                "execution_result": None,
                "expect": "高熟練鷹架：只點 edge case 不手把手；bloom 應偏高",
            },
            {
                "message": "老師影片裡有講到 overflow 嗎？有的話幫我附影片時間點",
                "code": OVERFLOW_CODE,
                "execution_result": None,
                "expect": "檢索無命中則誠實說沒有；citations_stripped 應攔下任何捏造連結",
            },
        ],
    )
    return steps


async def p7_quiz_diagnosis_flow(client: PersonaClient) -> dict[str, Any]:
    """Quiz+診斷型：連錯 3 題 → K3 診斷 → 嫌疑鏈 → 補救開放。"""
    steps: dict[str, Any] = {"submissions": []}
    steps["path"] = {
        "status": (await client.api("GET", "/learning/paths/default")).get(
            "_status", "ok"
        )
    }

    for i in range(3):
        q = await client.api(
            "GET", "/quiz/from-bank",
            params={"concept_tag": TAG, "question_type": "multiple_choice"},
        )
        if "_status" in q:
            steps["submissions"].append({"round": i + 1, "error": q})
            break
        info = await question_answer_info(q["id"])
        wrong = (info["answer_index"] + 1) % max(info["n_options"], 2)
        sub = await client.api(
            "POST", "/quiz/submit",
            json={"question_id": q["id"], "answer": {"selected_index": wrong}},
        )
        steps["submissions"].append(
            {
                "round": i + 1,
                "question_id": q["id"],
                "is_correct": sub.get("is_correct"),
                "feedback_head": (sub.get("feedback") or "")[:120],
            }
        )

    steps["diagnosis"] = await client.api("GET", f"/concepts/{TAG}/diagnosis")
    steps["remediate"] = await client.api(
        "POST", f"/concepts/{TAG}/diagnosis/remediate"
    )
    return steps
