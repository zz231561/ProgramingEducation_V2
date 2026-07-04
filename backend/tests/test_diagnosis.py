"""根源弱點定位測試（roadmap K3）。

測試圖（沿用 K1 多對多結構）：

    vars(1) ──→ cond(2) ──→ recursion(4)
      └──→ funcs(3) ────────↗
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from models.concept import Concept, ConceptEdge, EdgeType
from models.mastery import StudentMastery
from models.quiz import Question, StudentAnswer
from models.user import User
from services.diagnosis import diagnose_root_cause
from tests.helpers import TestSessionFactory, encrypt_test_token

STUDENT_PAYLOAD = {
    "sub": "diag-user",
    "email": "diag@test.com",
    "name": "Diag Tester",
    "googleId": "g-diag-user",
}


def _concept(tag: str, order: int) -> Concept:
    return Concept(
        tag=tag, name_zh=f"{tag}-中文", name_en=tag,
        description="", difficulty_level=1, category="test",
        video_order=order,
    )


async def _seed_graph_and_user() -> dict:
    """seed 4 節點 DAG + user，回傳 {tag: concept_id, "user_id": ...}。"""
    async with TestSessionFactory() as db:
        user = User(email="diag@test.com", name="Diag", google_id="g-diag-user")
        nodes = {
            "vars": _concept("vars", 1),
            "cond": _concept("cond", 2),
            "funcs": _concept("funcs", 3),
            "recursion": _concept("recursion", 4),
        }
        db.add(user)
        db.add_all(nodes.values())
        await db.flush()

        def edge(src: str, tgt: str) -> ConceptEdge:
            return ConceptEdge(
                source_id=nodes[src].id, target_id=nodes[tgt].id,
                edge_type=EdgeType.PREREQUISITE, weight=1.0,
            )

        db.add_all([
            edge("vars", "cond"), edge("vars", "funcs"),
            edge("cond", "recursion"), edge("funcs", "recursion"),
        ])
        await db.commit()
        return {**{t: c.id for t, c in nodes.items()}, "user_id": user.id}


async def _seed_answers(
    user_id: uuid.UUID, tag: str, results: list[bool]
) -> None:
    """為指定 concept seed 一串作答（results 由舊到新）。"""
    async with TestSessionFactory() as db:
        base = datetime(2026, 7, 4, 10, 0, tzinfo=timezone.utc)
        for i, correct in enumerate(results):
            q = Question(
                type="multiple_choice", concept_tags=[tag],
                bloom_level=2, difficulty=2,
                content={"stem": "q?", "options": ["a", "b"], "answer_index": 0},
                validated=True,
            )
            db.add(q)
            await db.flush()
            db.add(StudentAnswer(
                user_id=user_id, question_id=q.id,
                answer={"selected_index": 1}, is_correct=correct,
                answered_at=base + timedelta(minutes=i),
            ))
        await db.commit()


@pytest.mark.asyncio
async def test_diagnosis_unknown_tag_returns_none():
    ids = await _seed_graph_and_user()
    async with TestSessionFactory() as db:
        assert await diagnose_root_cause(db, ids["user_id"], "no-such") is None


@pytest.mark.asyncio
async def test_diagnosis_not_triggered_below_threshold():
    """連續失敗 2 次（< 3）→ triggered=False。"""
    ids = await _seed_graph_and_user()
    await _seed_answers(ids["user_id"], "recursion", [False, False])

    async with TestSessionFactory() as db:
        result = await diagnose_root_cause(db, ids["user_id"], "recursion")

    assert result is not None
    assert result.triggered is False
    assert result.recent_failure_streak == 2
    assert result.suspects == []


@pytest.mark.asyncio
async def test_diagnosis_correct_answer_breaks_streak():
    """錯錯對錯錯 → streak=2（答對截斷）→ 不觸發。"""
    ids = await _seed_graph_and_user()
    await _seed_answers(
        ids["user_id"], "recursion", [False, False, True, False, False]
    )

    async with TestSessionFactory() as db:
        result = await diagnose_root_cause(db, ids["user_id"], "recursion")

    assert result is not None
    assert result.recent_failure_streak == 2
    assert result.triggered is False


@pytest.mark.asyncio
async def test_diagnosis_ranks_exposed_weak_before_blind_spots():
    """觸發後：已曝光低 confidence 的 funcs 排最前，未曝光 cond/vars 為盲區在後。"""
    ids = await _seed_graph_and_user()
    await _seed_answers(ids["user_id"], "recursion", [False, False, False])

    async with TestSessionFactory() as db:
        db.add(StudentMastery(
            user_id=ids["user_id"], concept_id=ids["funcs"],
            confidence=0.2, exposure_count=3, success_count=1, error_count=2,
        ))
        await db.commit()

    async with TestSessionFactory() as db:
        result = await diagnose_root_cause(db, ids["user_id"], "recursion")

    assert result is not None
    assert result.triggered is True
    assert result.recent_failure_streak == 3

    tags = [s.concept.tag for s in result.suspects]
    # funcs（已曝光低 conf, depth1）→ cond（盲區 depth1）→ vars（盲區 depth2）
    assert tags == ["funcs", "cond", "vars"]
    assert result.suspects[0].confidence == 0.2
    assert result.suspects[1].confidence is None


@pytest.mark.asyncio
async def test_diagnosis_high_confidence_ancestor_excluded():
    """已曝光且 confidence 高的前置不列入嫌疑。"""
    ids = await _seed_graph_and_user()
    await _seed_answers(ids["user_id"], "recursion", [False, False, False])

    async with TestSessionFactory() as db:
        for tag in ("funcs", "cond", "vars"):
            db.add(StudentMastery(
                user_id=ids["user_id"], concept_id=ids[tag],
                confidence=0.9, exposure_count=5, success_count=5, error_count=0,
            ))
        await db.commit()

    async with TestSessionFactory() as db:
        result = await diagnose_root_cause(db, ids["user_id"], "recursion")

    assert result is not None
    assert result.triggered is True
    assert result.suspects == []


@pytest.mark.asyncio
async def test_diagnosis_attaches_bank_question():
    """嫌疑節點若題庫有 validated 題 → 附 question_id。"""
    ids = await _seed_graph_and_user()
    await _seed_answers(ids["user_id"], "recursion", [False, False, False])

    async with TestSessionFactory() as db:
        q = Question(
            type="multiple_choice", concept_tags=["funcs"],
            bloom_level=2, difficulty=1,
            content={"stem": "fn?", "options": ["a", "b"], "answer_index": 0},
            validated=True,
        )
        db.add(q)
        db.add(StudentMastery(
            user_id=ids["user_id"], concept_id=ids["funcs"],
            confidence=0.1, exposure_count=2, success_count=0, error_count=2,
        ))
        await db.commit()
        bank_question_id = q.id

    async with TestSessionFactory() as db:
        result = await diagnose_root_cause(db, ids["user_id"], "recursion")

    assert result is not None
    by_tag = {s.concept.tag: s for s in result.suspects}
    assert by_tag["funcs"].question_id == bank_question_id
    assert by_tag["cond"].question_id is None  # 題庫無 cond 題


# === API route ===

@pytest.mark.asyncio
async def test_diagnosis_route_requires_auth(client: AsyncClient):
    resp = await client.get("/concepts/recursion/diagnosis")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_diagnosis_route_unknown_tag_404(client: AsyncClient):
    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.get(
        "/concepts/no-such/diagnosis",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_diagnosis_route_returns_suspects(client: AsyncClient):
    """整合：觸發後回傳 suspects JSON（含 name_zh / depth / confidence）。"""
    ids = await _seed_graph_and_user()
    await _seed_answers(ids["user_id"], "recursion", [False, False, False])

    token = encrypt_test_token(STUDENT_PAYLOAD)
    resp = await client.get(
        "/concepts/recursion/diagnosis",
        cookies={"authjs.session-token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["target_tag"] == "recursion"
    assert body["triggered"] is True
    assert body["recent_failure_streak"] == 3
    assert len(body["suspects"]) == 3
    assert body["suspects"][0]["depth"] == 1
    assert body["suspects"][0]["name_zh"].endswith("中文")
