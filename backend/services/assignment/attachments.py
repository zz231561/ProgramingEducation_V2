"""作業附件 service（5-5a-2）— 上傳驗證 / 下載授權 / 刪除。

安全：白名單副檔名（word/pdf/pptx/程式碼/文字/壓縮）+ 單檔 ≤ 10MB；下載一律授權檢查
（作業附件＝教師或班級成員；繳交附件＝繳交本人或該作業教師）。檔名去路徑防目錄穿越。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.assignment import (
    MAX_ATTACHMENT_BYTES,
    Assignment,
    AssignmentSubmission,
    Attachment,
    AttachmentOwner,
)
from models.classroom import ClassMember

# 允許的副檔名白名單（word / pdf / pptx / 程式碼 / 純文字 / 壓縮）
ALLOWED_EXTENSIONS = frozenset({
    ".pdf", ".doc", ".docx", ".ppt", ".pptx",
    ".py", ".c", ".cpp", ".cc", ".h", ".hpp", ".java", ".js", ".ts",
    ".txt", ".md", ".zip",
})


def _ext(filename: str) -> str:
    dot = filename.rfind(".")
    return filename[dot:].lower() if dot != -1 else ""


def _safe_name(filename: str) -> str:
    """去除路徑成分（防目錄穿越）並截長。"""
    base = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].strip()
    return (base or "file")[:255]


def validate_upload(filename: str, size: int) -> None:
    """驗證副檔名白名單與大小上限；違反拋對應 AppError。"""
    if not filename or _ext(filename) not in ALLOWED_EXTENSIONS:
        raise AppError(415, "UNSUPPORTED_FILE_TYPE", "不支援的檔案類型")
    if size <= 0:
        raise AppError(422, "EMPTY_FILE", "檔案內容為空")
    if size > MAX_ATTACHMENT_BYTES:
        raise AppError(413, "FILE_TOO_LARGE", "檔案超過 10MB 上限")


def build_attachment(
    *,
    owner_type: str,
    owner_id: uuid.UUID,
    filename: str,
    content_type: str,
    content: bytes,
    uploaded_by: uuid.UUID,
) -> Attachment:
    """驗證後建構 Attachment（未 commit）；作業/繳交附件共用。"""
    validate_upload(filename, len(content))
    return Attachment(
        owner_type=owner_type, owner_id=owner_id, filename=_safe_name(filename),
        content_type=(content_type or "application/octet-stream")[:100],
        size_bytes=len(content), content=content, uploaded_by=uploaded_by,
    )


async def add_assignment_attachment(
    db: AsyncSession,
    *,
    teacher_id: uuid.UUID,
    assignment_id: uuid.UUID,
    filename: str,
    content_type: str,
    content: bytes,
) -> Attachment:
    """教師為自己的作業新增附件。"""
    a = await db.get(Assignment, assignment_id)
    if a is None or a.teacher_id != teacher_id:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "作業不存在")
    att = build_attachment(
        owner_type=AttachmentOwner.ASSIGNMENT.value, owner_id=assignment_id,
        filename=filename, content_type=content_type, content=content,
        uploaded_by=teacher_id,
    )
    db.add(att)
    await db.commit()
    await db.refresh(att)
    return att


async def list_attachment_meta(
    db: AsyncSession, *, owner_type: str, owner_id: uuid.UUID
) -> list:
    """列出某 owner 的附件中繼資料（不載入 content bytes，避免載大 blob）。"""
    stmt = (
        select(
            Attachment.id, Attachment.filename, Attachment.content_type,
            Attachment.size_bytes, Attachment.created_at,
        )
        .where(Attachment.owner_type == owner_type, Attachment.owner_id == owner_id)
        .order_by(Attachment.created_at)
    )
    return list((await db.execute(stmt)).all())


async def get_attachment_for_download(
    db: AsyncSession, *, user_id: uuid.UUID, attachment_id: uuid.UUID
) -> Attachment:
    """取得附件並檢查存取權（授權見 _authorize_access）。"""
    att = await db.get(Attachment, attachment_id)
    if att is None:
        raise AppError(404, "ATTACHMENT_NOT_FOUND", "附件不存在")
    await _authorize_access(db, att, user_id)
    return att


async def _authorize_access(
    db: AsyncSession, att: Attachment, user_id: uuid.UUID
) -> None:
    """作業附件＝教師或班級成員；繳交附件＝繳交本人或該作業教師。否則 403。"""
    if att.owner_type == AttachmentOwner.ASSIGNMENT.value:
        a = await db.get(Assignment, att.owner_id)
        if a is None:
            raise AppError(404, "ATTACHMENT_NOT_FOUND", "附件不存在")
        if a.teacher_id == user_id:
            return
        member = await db.get(
            ClassMember, {"class_id": a.class_id, "user_id": user_id}
        )
        if member is not None:
            return
    elif att.owner_type == AttachmentOwner.SUBMISSION.value:
        sub = await db.get(AssignmentSubmission, att.owner_id)
        if sub is None:
            raise AppError(404, "ATTACHMENT_NOT_FOUND", "附件不存在")
        if sub.student_id == user_id:
            return
        a = await db.get(Assignment, sub.assignment_id)
        if a is not None and a.teacher_id == user_id:
            return
    raise AppError(403, "FORBIDDEN", "無權存取此附件")


async def delete_attachment(
    db: AsyncSession, *, user_id: uuid.UUID, attachment_id: uuid.UUID
) -> None:
    """刪除附件——作業附件限該作業教師；繳交附件限繳交本人（5-5b）。"""
    att = await db.get(Attachment, attachment_id)
    if att is None:
        raise AppError(404, "ATTACHMENT_NOT_FOUND", "附件不存在")
    if att.owner_type == AttachmentOwner.ASSIGNMENT.value:
        a = await db.get(Assignment, att.owner_id)
        if a is None or a.teacher_id != user_id:
            raise AppError(404, "ATTACHMENT_NOT_FOUND", "附件不存在")
    elif att.owner_type == AttachmentOwner.SUBMISSION.value:
        sub = await db.get(AssignmentSubmission, att.owner_id)
        if sub is None or sub.student_id != user_id:
            raise AppError(404, "ATTACHMENT_NOT_FOUND", "附件不存在")
    else:
        raise AppError(403, "FORBIDDEN", "無權刪除此附件")
    await db.delete(att)
    await db.commit()
