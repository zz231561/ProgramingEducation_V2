"""使用者 Model。"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, String, Enum, DateTime, false, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class UserRole(str, enum.Enum):
    """使用者角色。"""

    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(Base):
    """使用者資料表 — 對應 Module 1: Auth。"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(String(500), default=None)
    role: Mapped[UserRole] = mapped_column(
        # values_callable：把 enum.value（小寫 "student"）寫入 Postgres，
        # 而非預設的 enum.name（"STUDENT"）— 與 alembic migration 建的 ENUM 對齊。
        Enum(UserRole, name="user_role", values_callable=lambda x: [e.value for e in x]),
        default=UserRole.STUDENT,
    )
    # 使用者是否已在 onboarding 主動選擇身分（False = 首登預設，需引導選擇）
    role_selected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
    )
    google_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )
