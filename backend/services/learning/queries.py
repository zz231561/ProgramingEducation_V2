"""學習路徑查詢 service — list / get / delete / 自動建立預設（roadmap 3-1c+）。

擁有權檢查：非本人擁有的路徑一律回 404（避免列舉攻擊揭露存在性，
與 reflection / comprehension 服務一致）。

3-1c+ 設計轉變：原 generate_learning_path 預期學生會手動建立多條路徑（含 category
filter / 弱項補強），但 concept graph 重建為固定 59 影片線性鏈後，每位學生「生成」
結果都相同 → 改為 onboarding 自動 seed 預設「C++ 完整課程」一條。
手動 generate / list / delete API 仍保留供未來教師端使用，前端不暴露。
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.concept import Concept
from models.learning import LearningPath, LearningUnit, LearningUnitStatus
from services.learning.generator import generate_learning_path

DEFAULT_PATH_TITLE = "C++ 完整課程"
DEFAULT_PATH_DESCRIPTION = (
    "教授整理的 62 部 C++ 教學影片中，排除前 3 部介紹後共 59 個學習單元，"
    "依教學順序組成完整課程。"
)


@dataclass(frozen=True)
class PathProgress:
    """單一路徑的進度概覽（list 用）。"""

    path: LearningPath
    total_units: int
    completed_units: int
    available_units: int


@dataclass(frozen=True)
class UnitWithConcept:
    """單元 + 對應 concept 資訊（detail 用，避免前端再 join）。

    6-2c 起加入 video_youtube_id / video_duration_seconds — 概念說明 tab
    需要在前端嵌入 YT IFrame player 與計算 timestamp citation 跳轉位置。
    """

    unit: LearningUnit
    concept_tag: str
    concept_name_zh: str
    concept_difficulty: int
    video_youtube_id: str | None
    video_duration_seconds: int | None
    # U2c：前端依「課程介紹」分類隱藏範例程式 tab
    concept_category: str | None


async def _get_owned_path(
    db: AsyncSession, path_id: UUID, user_id: UUID
) -> LearningPath:
    """取屬於 user_id 的 path；不存在或非本人 → 404。"""
    path = (
        await db.execute(select(LearningPath).where(LearningPath.id == path_id))
    ).scalar_one_or_none()
    if path is None or path.user_id != user_id:
        raise AppError(
            404,
            "LEARNING_PATH_NOT_FOUND",
            f"找不到學習路徑：{path_id}",
        )
    return path


async def list_paths_for_user(
    db: AsyncSession, user_id: UUID
) -> list[PathProgress]:
    """列出該使用者所有路徑（按 created_at 降冪）+ 進度概覽。"""
    paths = list(
        (
            await db.execute(
                select(LearningPath)
                .where(LearningPath.user_id == user_id)
                .order_by(LearningPath.created_at.desc())
            )
        ).scalars().all()
    )
    if not paths:
        return []

    # 一次取所有相關 units，避免 N+1
    path_ids = [p.id for p in paths]
    units = list(
        (
            await db.execute(
                select(LearningUnit).where(LearningUnit.path_id.in_(path_ids))
            )
        ).scalars().all()
    )

    summaries: list[PathProgress] = []
    for p in paths:
        path_units = [u for u in units if u.path_id == p.id]
        total = len(path_units)
        completed = sum(
            1 for u in path_units
            if u.status == LearningUnitStatus.COMPLETED.value
        )
        available = sum(
            1 for u in path_units
            if u.status == LearningUnitStatus.AVAILABLE.value
        )
        summaries.append(
            PathProgress(
                path=p,
                total_units=total,
                completed_units=completed,
                available_units=available,
            )
        )
    return summaries


async def get_path_with_units(
    db: AsyncSession, path_id: UUID, user_id: UUID
) -> tuple[LearningPath, list[UnitWithConcept]]:
    """取單一路徑詳細 + units（按 order_index 升冪 + 對應 concept 資訊）。"""
    path = await _get_owned_path(db, path_id, user_id)

    rows = list(
        (
            await db.execute(
                select(LearningUnit, Concept)
                .join(Concept, Concept.id == LearningUnit.concept_id)
                .where(LearningUnit.path_id == path.id)
                .order_by(LearningUnit.order_index)
            )
        ).all()
    )
    units = [
        UnitWithConcept(
            unit=unit,
            concept_tag=concept.tag,
            concept_name_zh=concept.name_zh,
            concept_difficulty=concept.difficulty_level,
            video_youtube_id=concept.video_youtube_id,
            video_duration_seconds=concept.video_duration_seconds,
            concept_category=concept.category,
        )
        for unit, concept in rows
    ]
    return path, units


async def delete_path(db: AsyncSession, path_id: UUID, user_id: UUID) -> None:
    """刪除路徑（CASCADE 連動 units）。非本人 → 404。"""
    path = await _get_owned_path(db, path_id, user_id)
    await db.delete(path)
    await db.commit()


async def ensure_default_path_exists(
    db: AsyncSession, user_id: UUID
) -> LearningPath:
    """確保使用者有預設路徑；無則 lazy seed。

    語意：
    - 使用者第一次進 Learn 頁 → 後端自動建立「C++ 完整課程」一條
    - 已有任何路徑（不論 title）→ 回傳最早建立的那條（按 created_at 升冪取首位）
    - 全 nullable concept seed 失敗 → 由 generate_learning_path 拋 422 LEARNING_PATH_EMPTY

    這個 helper 純粹保證「使用者有路徑可看」，不檢驗是否為「預設」title。
    """
    existing = (
        await db.execute(
            select(LearningPath)
            .where(LearningPath.user_id == user_id)
            .order_by(LearningPath.created_at)
            .limit(1)
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    return await generate_learning_path(
        db,
        user_id=user_id,
        title=DEFAULT_PATH_TITLE,
        description=DEFAULT_PATH_DESCRIPTION,
    )
