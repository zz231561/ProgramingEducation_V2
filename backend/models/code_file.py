"""Workspace 程式碼存檔 Model（roadmap U2e）。

單表兩用：`name IS NULL` 為自動草稿（每人一份）；有 name 為命名檔案
（UNIQUE(user_id, name)，同名儲存＝覆蓋）。Schema 對齊 migration `r4a5b6c7d8e9`。
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base

# 單檔程式碼長度上限（字元）；與 migration CHECK 一致
MAX_CODE_CHARS = 100_000
# 每人命名檔案數量上限（service 層把關）
MAX_FILES_PER_USER = 50


class CodeFile(Base):
    """使用者的 Workspace 程式碼（草稿或命名檔案）。"""

    __tablename__ = "code_files"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(100), default=None)
    code: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
