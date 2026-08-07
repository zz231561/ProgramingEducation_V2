"""Workspace 程式碼存檔 service（roadmap U2e）。

- 草稿（name IS NULL）：每人一份，PUT 即 upsert；進 Workspace 自動還原。
- 命名檔案：同名儲存＝覆蓋（upsert by (user, name)）；每人上限 MAX_FILES_PER_USER。
- 授權：一律限本人；他人檔案回 404（不洩漏存在性）。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.code_file import (
    CODE_FILE_SUFFIX,
    MAX_FILES_PER_USER,
    MAX_NAME_CHARS,
    CodeFile,
)


def normalize_file_name(raw: str) -> str:
    """檔名一律以 .cpp 收尾。

    副檔名對執行沒有任何作用（Judge0 一律以 C++ 編譯），鎖定收尾純粹是
    避免「main.md 也能跑」這種誤導；前端輸入框同樣把 .cpp 鎖成固定尾綴。
    """
    name = raw.strip()
    if not name:
        raise AppError(422, "VALIDATION_ERROR", "檔名不可為空白")
    if not name.lower().endswith(CODE_FILE_SUFFIX):
        name += CODE_FILE_SUFFIX
    if len(name) > MAX_NAME_CHARS:
        raise AppError(
            422, "VALIDATION_ERROR", f"檔名過長（含 {CODE_FILE_SUFFIX} 上限 {MAX_NAME_CHARS} 字）"
        )
    return name


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
    opened_name: str | object | None = KEEP_OPENED_NAME,
) -> CodeFile:
    """upsert 草稿（每人一份）；opened_name 未提供時保留現值。

    首次建立時可能有兩個請求同時 INSERT（自動存檔與 handoff 開檔並行），
    partial unique index 會擋下較慢的那個 → 改用對方建立的那列繼續更新。
    """
    draft = await get_draft(db, user_id)
    if draft is None:
        draft = CodeFile(user_id=user_id, code=code)
        if opened_name is not KEEP_OPENED_NAME:
            draft.opened_name = opened_name  # type: ignore[assignment] -- sentinel guard 已排除 object
        db.add(draft)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            draft = await get_draft(db, user_id)
            if draft is None:  # 不是草稿唯一索引造成的衝突
                raise
        else:
            await db.refresh(draft)
            return draft
    draft.code = code
    if opened_name is not KEEP_OPENED_NAME:
        draft.opened_name = opened_name  # type: ignore[assignment] -- sentinel guard 已排除 object
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
    name = normalize_file_name(name)
    existing = await _find_by_name(db, user_id, name)
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


async def _find_by_name(
    db: AsyncSession, user_id: uuid.UUID, name: str
) -> CodeFile | None:
    return (
        await db.execute(
            select(CodeFile).where(
                CodeFile.user_id == user_id, CodeFile.name == name
            )
        )
    ).scalar_one_or_none()


async def rename_file(
    db: AsyncSession, user_id: uuid.UUID, old_name: str, new_name: str
) -> CodeFile:
    """重新命名（同一份檔案改名，不複製）；草稿的檔名關聯一併跟著改。"""
    new_name = normalize_file_name(new_name)
    file = await _find_by_name(db, user_id, old_name)
    if file is None:
        raise AppError(404, "CODE_FILE_NOT_FOUND", "檔案不存在")
    if new_name == old_name:
        return file
    if await _find_by_name(db, user_id, new_name) is not None:
        raise AppError(409, "CODE_FILE_NAME_TAKEN", f"「{new_name}」已存在")

    file.name = new_name
    draft = await get_draft(db, user_id)
    if draft is not None and draft.opened_name == old_name:
        draft.opened_name = new_name
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
