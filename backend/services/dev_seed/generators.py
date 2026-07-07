"""假學生資料 seeder — 純資料產生器（DEV-E）。

行為原型定義 + 各表列的 pure builder（無 DB I/O，吃 seeded Random 保證可重現）。
編排（purge / 建教師班級 / commit）見 `seeder.py`。
"""

import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from models.chat import ChatMessage, DialogueAct, MessageRole
from models.coding_event import CodingEvent, CodingEventType
from models.mastery import StudentMastery
from models.student_profile import StudentProfile

_SCHOOLS = ("台灣科大", "成功大學", "中央大學", "逢甲大學")
_DEPARTMENTS = ("資工系", "電機系", "資管系")
_SURNAMES = ("陳", "林", "黃", "張", "李", "王", "吳", "劉")
_GIVEN = ("承翰", "宗霖", "怡君", "詩涵", "冠宇", "雅婷", "柏翰", "思妤")


@dataclass(frozen=True)
class Archetype:
    """行為原型 — 塑形每位假學生的事件 / 對話 / 熟練度分布。"""

    key: str  # active / passive / struggling
    n_runs: int  # 執行次數
    fail_ratio: float  # 一次執行以錯誤開頭的比例
    hint_ratio: float  # 錯誤後索取 hint 的比例
    mastery_base: float  # 熟練度基準
    acts: tuple[str, ...]  # dialogue_act 取樣池


ARCHETYPES = (
    Archetype(
        "active", 12, 0.25, 0.15, 0.72,
        (DialogueAct.CLARIFICATION_REQUEST.value, DialogueAct.VERIFICATION.value,
         DialogueAct.ACKNOWLEDGMENT.value),
    ),
    Archetype(
        "passive", 5, 0.40, 0.10, 0.45,
        (DialogueAct.ACKNOWLEDGMENT.value, DialogueAct.CLARIFICATION_REQUEST.value),
    ),
    Archetype(
        "struggling", 14, 0.75, 0.60, 0.28,
        (DialogueAct.ASKING_HINT.value, DialogueAct.DEBUGGING.value,
         DialogueAct.CLARIFICATION_REQUEST.value),
    ),
)


def make_profile(rng: random.Random, uid: uuid.UUID, idx: int) -> StudentProfile:
    return StudentProfile(
        user_id=uid,
        school=rng.choice(_SCHOOLS),
        department=rng.choice(_DEPARTMENTS),
        student_id=f"S{10000 + idx}",
        real_name=rng.choice(_SURNAMES) + rng.choice(_GIVEN),
    )


def make_events(
    rng: random.Random, uid: uuid.UUID, arch: Archetype
) -> list[CodingEvent]:
    """依原型生成執行 / 錯誤 / hint / 成功事件（時間散佈於近 14 天）。"""
    now = datetime.now(timezone.utc)
    events: list[CodingEvent] = []
    for _ in range(arch.n_runs):
        ts = now - timedelta(days=rng.uniform(0, 14), minutes=rng.uniform(0, 600))
        if rng.random() >= arch.fail_ratio:
            events.append(_success(uid, ts))
            continue
        kind = rng.choice(
            [CodingEventType.COMPILE_ERROR, CodingEventType.RUNTIME_ERROR]
        )
        events.append(CodingEvent(user_id=uid, event_type=kind.value, created_at=ts))
        if rng.random() < arch.hint_ratio:
            events.append(
                CodingEvent(
                    user_id=uid, event_type=CodingEventType.HINT_REQUEST.value,
                    hint_level=rng.randint(1, 4), created_at=ts + timedelta(minutes=1),
                )
            )
        events.append(_success(uid, ts + timedelta(minutes=rng.uniform(2, 20))))
    return events


def _success(uid: uuid.UUID, ts: datetime) -> CodingEvent:
    return CodingEvent(
        user_id=uid, event_type=CodingEventType.SUCCESS.value, created_at=ts
    )


def make_mastery(
    rng: random.Random,
    uid: uuid.UUID,
    arch: Archetype,
    concept_ids: list[uuid.UUID],
) -> list[StudentMastery]:
    """為取樣 concept 生成熟練度（confidence 以原型基準加 gauss 抖動）。"""
    picked = rng.sample(concept_ids, min(len(concept_ids), 12))
    now = datetime.now(timezone.utc)
    rows: list[StudentMastery] = []
    for cid in picked:
        conf = min(1.0, max(0.0, rng.gauss(arch.mastery_base, 0.12)))
        exposure = rng.randint(1, 8)
        success = round(exposure * conf)
        rows.append(
            StudentMastery(
                user_id=uid, concept_id=cid, confidence=round(conf, 3),
                exposure_count=exposure, success_count=success,
                error_count=exposure - success, bloom_level=rng.randint(1, 4),
                last_practiced_at=now - timedelta(days=rng.uniform(0, 10)),
            )
        )
    return rows


def make_chat_messages(
    rng: random.Random, session_id: uuid.UUID, arch: Archetype
) -> list[ChatMessage]:
    """生成帶 dialogue_act 的假 user 訊息（內容僅標記，不進 LLM）。"""
    return [
        ChatMessage(
            session_id=session_id, role=MessageRole.USER,
            content=f"[seed] {act}", dialogue_act=act,
        )
        for act in (rng.choice(arch.acts) for _ in range(rng.randint(2, 6)))
    ]
