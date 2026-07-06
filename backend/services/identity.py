"""身分選擇 / 切換 service（roadmap 5-1d-2）。

- Onboarding 首次選擇（role_selected=False → True）：僅設定身分，不清資料。
- 之後於設定頁切換身分（role_selected 已 True）：視為「重置」，全清該使用者
  的學習資料 + profile + 班級關係（教師擁有的班級一併刪，含成員）後再設身分。

顯式刪子表（不依賴 DB FK cascade）以與 SQLite 測試行為一致，比照 dev_tools。
"""

import logging
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.classroom import ClassMember, Classroom
from models.student_profile import StudentProfile
from models.user import User, UserRole
from services.dev_tools import RESET_CATEGORIES, reset_user_data

logger = logging.getLogger(__name__)


async def _wipe_identity_data(db: AsyncSession, user_id: uuid.UUID) -> None:
    """清除使用者所有學習資料 + profile + 班級關係（切換身分用）。"""
    # 學習資料（mastery / progress / quiz / chat）；此函式內部會 commit
    await reset_user_data(db, user_id, set(RESET_CATEGORIES))

    # 教師擁有的班級：先刪成員再刪班級（顯式，不靠 FK cascade）
    owned = select(Classroom.id).where(Classroom.teacher_id == user_id)
    await db.execute(delete(ClassMember).where(ClassMember.class_id.in_(owned)))
    await db.execute(delete(Classroom).where(Classroom.teacher_id == user_id))
    # 學生身分的班級成員關係
    await db.execute(delete(ClassMember).where(ClassMember.user_id == user_id))
    # 身分 profile
    await db.execute(delete(StudentProfile).where(StudentProfile.user_id == user_id))


async def select_role(
    db: AsyncSession, user: User, new_role: UserRole
) -> tuple[User, bool]:
    """設定使用者身分。已選過身分則視為重置（全清資料）。

    回傳 (user, did_reset)；did_reset=True 代表本次清空了既有資料。
    """
    did_reset = user.role_selected
    if did_reset:
        await _wipe_identity_data(db, user.id)

    user.role = new_role
    user.role_selected = True
    await db.commit()
    await db.refresh(user)
    logger.info(
        "[identity] user=%s role=%s reset=%s", user.id, new_role.value, did_reset
    )
    return user, did_reset
