"""Workspace 程式碼存檔 service（roadmap U2e）。

- 草稿（name IS NULL）：每人一份，PUT 即 upsert；進 Workspace 自動還原。
- 命名檔案：同名儲存＝覆蓋（upsert by (user, name)）；每人上限 MAX_FILES_PER_USER。
- 授權：一律限本人；他人檔案回 404（不洩漏存在性）。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.code_file import MAX_FILES_PER_USER, CodeFile


async def get_draft(db: AsyncSession, user_id: uuid.UUID) -> CodeFile | None:
    return (
        await db.execute(
            select(CodeFile).where(
                CodeFile.user_id == user_id, CodeFile.name.is_(None)
            )
        )
    ).scalar_one_or_none()


KEEP_OPENED_NAME = object()  # sentinel：呼叫端未提供 opened_name 時保留現值


async def save_draft(
    db: AsyncSession,
    user_id: uuid.UUID,
    code: str,
    opened_name: str | None | object = KEEP_OPENED_NAME,
) -> CodeFile:
    """upsert 草稿（每人一份）；opened_name 未提供時保留現值。"""
    draft = await get_draft(db, user_id)
    if draft is None:
        draft = CodeFile(user_id=user_id, code=code)
        db.add(draft)
    else:
        draft.code = code
    if opened_name is not KEEP_OPENED_NAME:
        draft.opened_name = opened_name  # type: ignore[assignment]
    await db.commit()
    await db.refresh(draft)
    return draft


async def list_files(db: AsyncSession, user_id: uuid.UUID) -> list[CodeFile]:
    """命名檔案列表（新到舊）；不含草稿。"""
    return list(
        (
            await db.execute(
                select(CodeFile)
                .where(CodeFile.user_id == user_id, CodeFile.name.is_not(None))
                .order_by(CodeFile.updated_at.desc())
            )
        ).scalars()
    )


async def save_file(
    db: AsyncSession, user_id: uuid.UUID, name: str, code: str
) -> CodeFile:
    """命名檔案 upsert：同名覆蓋；新檔受每人數量上限約束。"""
    name = name.strip()
    if not name:
        raise AppError(422, "VALIDATION_ERROR", "檔名不可為空白")
    existing = (
        await db.execute(
            select(CodeFile).where(
                CodeFile.user_id == user_id, CodeFile.name == name
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.code = code
        await db.commit()
        await db.refresh(existing)
        return existing

    count = len(await list_files(db, user_id))
    if count >= MAX_FILES_PER_USER:
        raise AppError(
            409, "CODE_FILE_LIMIT", f"已達檔案數量上限（{MAX_FILES_PER_USER}）"
        )
    file = CodeFile(user_id=user_id, name=name, code=code)
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return file


async def get_file(
    db: AsyncSession, user_id: uuid.UUID, file_id: uuid.UUID
) -> CodeFile:
    file = await db.get(CodeFile, file_id)
    if file is None or file.user_id != user_id or file.name is None:
        raise AppError(404, "CODE_FILE_NOT_FOUND", "檔案不存在")
    return file


async def delete_file(
    db: AsyncSession, user_id: uuid.UUID, file_id: uuid.UUID
) -> None:
    file = await get_file(db, user_id, file_id)
    await db.delete(file)
    await db.commit()
