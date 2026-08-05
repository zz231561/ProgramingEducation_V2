"""Workspace 程式碼存檔 Model（roadmap U2e）。

單表兩用：`name IS NULL` 為自動草稿（每人一份）；有 name 為命名檔案
（UNIQUE(user_id, name)，同名儲存＝覆蓋）。Schema 對齊 migration `r4a5b6c7d8e9`。
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base

# 單檔程式碼長度上限（字元）；與 migration CHECK 一致
MAX_CODE_CHARS = 100_000
# 每人命名檔案數量上限（service 層把關）
MAX_FILES_PER_USER = 50
# 檔名長度上限（與 String(100) 一致）
MAX_NAME_CHARS = 100
# 命名檔案固定副檔名（平台只編譯 C++；service 層正規化把關）
CODE_FILE_SUFFIX = ".cpp"


class CodeFile(Base):
    """使用者的 Workspace 程式碼（草稿或命名檔案）。"""

    __tablename__ = "code_files"

    # ⚠ 這些約束原本只寫在 migration `r4a5b6c7d8e9`，model 未宣告 → 測試的
    # `Base.metadata.create_all` 建不出來，於是 save_draft 的併發保護
    # （靠 IntegrityError 接住較慢的 INSERT）在測試中從未真正執行過。
    # 2026-08-06 補宣告，讓測試 schema 與生產一致。dialect 條件兩者都給：
    # partial index 在 Postgres 與 SQLite 語法不同，SQLAlchemy 需分別指定。
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_code_files_user_name"),
        # migration 用 Postgres 專有的 char_length()；此處用 length()，
        # 兩者在 Postgres 對 text 等價，且 SQLite 只認得 length()
        CheckConstraint(
            f"length(code) <= {MAX_CODE_CHARS}", name="ck_code_files_code_len"
        ),
        Index(
            "uq_code_files_draft",
            "user_id",
            unique=True,
            postgresql_where=text("name IS NULL"),
            sqlite_where=text("name IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(100), default=None)
    code: Mapped[str] = mapped_column(Text, default="")
    # 僅草稿列使用：記錄目前開啟的命名檔案（重整/再登入後還原檔名關聯）
    opened_name: Mapped[str | None] = mapped_column(String(100), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
