"""Workspace 程式碼存檔 API（roadmap U2e）— 自動草稿 + 命名檔案。

- GET/PUT  /code/draft       — 草稿還原 / 自動存檔（upsert）
- GET      /code/files       — 命名檔案列表（meta，不含 code）
- PUT      /code/files       — 儲存命名檔案（同名覆蓋）
- GET      /code/files/{id}  — 載入檔案內容
- DELETE   /code/files/{id}  — 刪除檔案
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db
from core.errors import AppError
from models.code_file import MAX_CODE_CHARS, CodeFile
from models.user import User
from services.workspace_files import (
    delete_file,
    get_draft,
    get_file,
    list_files,
    save_draft,
    save_file,
)

router = APIRouter(prefix="/code", tags=["code"])


class DraftIn(BaseModel):
    code: str = Field(default="", max_length=MAX_CODE_CHARS)


class SaveFileIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(default="", max_length=MAX_CODE_CHARS)


class CodeFileMetaOut(BaseModel):
    id: uuid.UUID
    name: str
    updated_at: str

    @classmethod
    def from_model(cls, f: CodeFile) -> "CodeFileMetaOut":
        return cls(id=f.id, name=f.name or "", updated_at=f.updated_at.isoformat())


class CodeFileOut(CodeFileMetaOut):
    code: str

    @classmethod
    def from_model(cls, f: CodeFile) -> "CodeFileOut":
        return cls(
            id=f.id, name=f.name or "", code=f.code,
            updated_at=f.updated_at.isoformat(),
        )


class DraftOut(BaseModel):
    code: str
    updated_at: str


@router.get("/draft", response_model=DraftOut)
async def read_draft(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> DraftOut:
    draft = await get_draft(db, user.id)
    if draft is None:
        raise AppError(404, "DRAFT_NOT_FOUND", "尚無草稿")
    return DraftOut(code=draft.code, updated_at=draft.updated_at.isoformat())


@router.put("/draft", response_model=DraftOut)
async def write_draft(
    body: DraftIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> DraftOut:
    draft = await save_draft(db, user.id, body.code)
    return DraftOut(code=draft.code, updated_at=draft.updated_at.isoformat())


@router.get("/files", response_model=list[CodeFileMetaOut])
async def list_code_files(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> list[CodeFileMetaOut]:
    return [CodeFileMetaOut.from_model(f) for f in await list_files(db, user.id)]


@router.put("/files", response_model=CodeFileOut)
async def save_code_file(
    body: SaveFileIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> CodeFileOut:
    file = await save_file(db, user.id, body.name, body.code)
    return CodeFileOut.from_model(file)


@router.get("/files/{file_id}", response_model=CodeFileOut)
async def read_code_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> CodeFileOut:
    return CodeFileOut.from_model(await get_file(db, user.id, file_id))


@router.delete("/files/{file_id}", status_code=204)
async def remove_code_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> None:
    await delete_file(db, user.id, file_id)
