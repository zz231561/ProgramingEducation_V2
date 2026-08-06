"""診斷輪 orchestrator — `python -m scripts.eval_coddy.run [--only p1,p7] [--out DIR]`。

輸出：每 persona 一份 JSON（逐輪 transcript + debug_sink + DB 探針）。
僅限本機 DB；真實 LLM 呼叫（七型全跑約 25-30 次 interact）。
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from scripts._db_guard import require_local_db
from scripts.eval_coddy import flows, probe
from scripts.eval_coddy.client import PersonaClient
from scripts.eval_coddy.personas import DIALOGUE_PERSONAS


def _debug_summary(debug: dict | None) -> dict | None:
    """debug_sink 摘要：只留分析需要的欄位，transcript 不爆量。"""
    if not debug:
        return None
    ev = debug.get("evidence") or {}
    st = debug.get("strategy") or {}
    return {
        "error_type": ev.get("error_type"),
        "bloom": ev.get("bloom_level"),
        "concept_tags": ev.get("concept_tags"),
        "is_on_topic": ev.get("is_on_topic"),
        "persistence": debug.get("persistence"),
        "reveal_level": st.get("reveal_level"),
        "allow_code": st.get("allow_code_snippet"),
        "bloom_guidance": st.get("bloom_guidance"),
        "kgraph_head": (debug.get("kgraph_block") or "")[:200] or None,
        "reflection_injected": debug.get("reflection_injected"),
        "rag": [
            {"score": c["score"], "doc": c["doc_id"]}
            for c in (debug.get("rag_chunks") or [])
        ],
        "citations_stripped": debug.get("citations_stripped"),
    }


async def run_dialogue(client: PersonaClient, turns: list[dict]) -> list[dict]:
    """共用對話迴圈：逐輪送出訊息 + 每輪後探針。

    7-C2a 後揭露等級由後端從對話歷史自算，harness 不再模擬前端階梯。
    """
    uid = await probe.user_id_by_email(client.email)
    records: list[dict] = []
    for turn in turns:
        before = await probe.mastery_snapshot(uid) if uid else {}
        res = await client.interact(
            question=turn["message"],
            code=turn.get("code", ""),
            execution_result=turn.get("execution_result"),
            reflection_id=turn.get("reflection_id"),
        )
        if uid is None:
            uid = await probe.user_id_by_email(client.email)
        after = await probe.mastery_snapshot(uid) if uid else {}
        act = (
            await probe.dialogue_act_of(res["user_message_id"])
            if res.get("user_message_id")
            else None
        )
        records.append(
            {
                "message": turn["message"],
                "expect": turn.get("expect"),
                "stages": res.get("stages"),
                "response": res.get("response"),
                "error": res.get("error"),
                "debug": _debug_summary(res.get("debug")),
                "dialogue_act": act,
                "mastery_diff": probe.mastery_diff(before, after),
            }
        )
    return records


async def run_persona(p: dict, out_dir: Path) -> None:
    client = PersonaClient(p["email"], p["name"])
    try:
        # 觸發 get_or_create_user（首個認證請求）
        await client.api("GET", "/users/me")
        result: dict = {"persona": p["name"], "goal": p["goal"], "email": p["email"]}
        result["turns"] = await run_dialogue(client, p["turns"])
        uid = await probe.user_id_by_email(p["email"])
        result["coding_events"] = await probe.coding_events_of(uid) if uid else []
        _write(out_dir, p["key"], result)
    finally:
        await client.close()


async def run_flow(key: str, name: str, email: str, fn, out_dir: Path) -> None:
    client = PersonaClient(email, name)
    try:
        await client.api("GET", "/users/me")
        result = {"persona": name, "email": email}
        result["flow"] = await fn(client)
        uid = await probe.user_id_by_email(email)
        result["coding_events"] = await probe.coding_events_of(uid) if uid else []
        _write(out_dir, key, result)
    finally:
        await client.close()


def _write(out_dir: Path, key: str, result: dict) -> None:
    path = out_dir / f"{key}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"[{key}] {result['persona']} → {path}")


async def main() -> None:
    require_local_db("Coddy 多型學生模擬（產生假使用者與對話）")
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="", help="逗號分隔 persona key（p1..p7）")
    parser.add_argument("--out", default="", help="輸出目錄")
    args = parser.parse_args()
    only = set(filter(None, args.only.split(",")))
    out_dir = Path(args.out or f"eval_out_{datetime.now():%m%d_%H%M}")
    out_dir.mkdir(parents=True, exist_ok=True)

    for p in DIALOGUE_PERSONAS:
        if not only or p["key"] in only:
            await run_persona(p, out_dir)

    async def _p2(c):
        return await flows.p2_reflection_flow(c, run_dialogue)

    async def _p5(c):
        return await flows.p5_advanced_flow(c, run_dialogue)

    specials = [
        ("p2", "按部就班型", "p2@eval.local", _p2),
        ("p5", "進階挑戰型", "p5@eval.local", _p5),
        ("p7", "Quiz診斷型", "p7@eval.local", flows.p7_quiz_diagnosis_flow),
    ]
    for key, name, email, fn in specials:
        if not only or key in only:
            await run_flow(key, name, email, fn, out_dir)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
