"""學生身分 Profile Model — 對應 Module 8: 教師端（roadmap 5-1b-1）。

Google OAuth 的顯示名不一定是真實姓名，故學生首次登入需補填校名 / 系所 /
學號 / 姓名以確認身分；email 沿用 `users.email` 不重複儲存。

Schema 對齊 alembic migration `m9b0c1d2e3f4`。
- 1:1 對應 users：以 `user_id` 當主鍵，天然保證每位學生至多一份 profile。
- 學號不設 unique（校名可能跨校，全系統唯一會誤擋跨校撞號 — 使用者決策）。
- 僅 role=student 需填寫；gating 由前端在首次登入時執行（5-1c）。
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class StudentProfile(Base):
    """學生自填的身分資料（校名 / 系所 / 學號 / 姓名）。"""

    __tablename__ = "student_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    school: Mapped[str] = mapped_column(String(100))
    department: Mapped[str] = mapped_column(String(100))
    student_id: Mapped[str] = mapped_column(String(50))
    real_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
