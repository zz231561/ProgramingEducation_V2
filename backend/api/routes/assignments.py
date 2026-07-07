"""作業指派 API — 教師端 CRUD + 附件（roadmap 5-5a-2）。

作業 CRUD 掛 require_roles(TEACHER) + 擁有權；附件下載對已登入使用者開放、授權在 service。
檔案存 bytea；上傳白名單 + 10MB 由 service 把關。下載一律 Content-Disposition: attachment
（防 inline HTML/SVG XSS）。
"""

import uuid
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db, require_roles
from core.rate_limit import rate_limit
from models.assignment import MAX_ATTACHMENT_BYTES, Assignment, Attachment
from models.user import User, UserRole
from services.assignment import (
    UNSET,
    add_assignment_attachment,
    create_assignment,
    delete_assignment,
    delete_attachment,
    get_assignment,
    get_attachment_for_download,
    list_assignments,
    update_assignment,
)

router = APIRouter(prefix="/assignments", tags=["assignments"])
attachments_router = APIRouter(prefix="/attachments", tags=["assignments"])

_teacher = require_roles(UserRole.TEACHER)


# === Schemas ===


class CreateAssignmentRequest(BaseModel):
    class_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=20_000)
    due_at: datetime | None = None


class PatchAssignmentRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20_000)
    due_at: datetime | None = None
    is_active: bool | None = None


class AttachmentOut(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    created_at: str

    @classmethod
    def from_model(cls, a: Attachment) -> "AttachmentOut":
        return cls(
            id=a.id, filename=a.filename, content_type=a.content_type,
            size_bytes=a.size_bytes, created_at=a.created_at.isoformat(),
        )


class AssignmentOut(BaseModel):
    id: uuid.UUID
    class_id: uuid.UUID
    title: str
    description: str
    due_at: str | None
    is_active: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, a: Assignment) -> "AssignmentOut":
        return cls(
            id=a.id, class_id=a.class_id, title=a.title, description=a.description,
            due_at=a.due_at.isoformat() if a.due_at else None,
            is_active=a.is_active, created_at=a.created_at.isoformat(),
            updated_at=a.updated_at.isoformat(),
        )


# === Assignment CRUD（教師）===


@router.post("", response_model=AssignmentOut, status_code=201)
async def create(
    body: CreateAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(_teacher),
) -> AssignmentOut:
    a = await create_assignment(
        db, teacher_id=teacher.id, class_id=body.class_id,
        title=body.title, description=body.description, due_at=body.due_at,
    )
    return AssignmentOut.from_model(a)


@router.get("", response_model=list[AssignmentOut])
async def list_own(
    class_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(_teacher),
) -> list[AssignmentOut]:
    rows = await list_assignments(db, teacher_id=teacher.id, class_id=class_id)
    return [AssignmentOut.from_model(a) for a in rows]


@router.get("/{assignment_id}", response_model=AssignmentOut)
async def get_one(
    assignment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(_teacher),
) -> AssignmentOut:
    a = await get_assignment(db, teacher_id=teacher.id, assignment_id=assignment_id)
    return AssignmentOut.from_model(a)


@router.patch("/{assignment_id}", response_model=AssignmentOut)
async def patch(
    assignment_id: uuid.UUID,
    body: PatchAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(_teacher),
) -> AssignmentOut:
    # due_at 用 model_fields_set 區分「未提供」與「明確清空 null」
    due = body.due_at if "due_at" in body.model_fields_set else UNSET
    a = await update_assignment(
        db, teacher_id=teacher.id, assignment_id=assignment_id,
        title=body.title, description=body.description,
        is_active=body.is_active, due_at=due,
    )
    return AssignmentOut.from_model(a)


@router.delete("/{assignment_id}", status_code=204)
async def remove(
    assignment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(_teacher),
) -> None:
    await delete_assignment(db, teacher_id=teacher.id, assignment_id=assignment_id)


# === 附件（教師上傳 / 刪除；下載開放已登入者，授權在 service）===


@router.post(
    "/{assignment_id}/attachments",
    response_model=AttachmentOut,
    status_code=201,
    dependencies=[Depends(rate_limit("upload", 20))],
)
async def upload_attachment(
    assignment_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(_teacher),
) -> AttachmentOut:
    # 讀取上限+1 bytes 以偵測超標，避免載入超大 body 進記憶體
    content = await file.read(MAX_ATTACHMENT_BYTES + 1)
    att = await add_assignment_attachment(
        db, teacher_id=teacher.id, assignment_id=assignment_id,
        filename=file.filename or "", content_type=file.content_type or "",
        content=content,
    )
    return AttachmentOut.from_model(att)


@attachments_router.get("/{attachment_id}")
async def download_attachment(
    attachment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> Response:
    att = await get_attachment_for_download(
        db, user_id=user.id, attachment_id=attachment_id
    )
    # RFC 5987 檔名編碼支援中文；一律 attachment 強制下載不 inline
    disposition = f"attachment; filename*=UTF-8''{quote(att.filename)}"
    return Response(
        content=att.content,
        media_type=att.content_type,
        headers={"Content-Disposition": disposition},
    )


@attachments_router.delete("/{attachment_id}", status_code=204)
async def remove_attachment(
    attachment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(_teacher),
) -> None:
    await delete_attachment(db, teacher_id=teacher.id, attachment_id=attachment_id)
