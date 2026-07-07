"""作業繳交 API（5-5b）— 學生繳交 + 教師交件檢視/評分。

路由需在 assignments_router 之前註冊，使 `/assignments/mine` 優先於 `/assignments/{id}`。
附件下載/刪除沿用 /attachments（assignments.py）；此檔僅繳交本體與評分。
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_db_user, get_db, require_roles
from api.routes.assignments import AttachmentOut
from core.rate_limit import rate_limit
from models.assignment import MAX_ATTACHMENT_BYTES, Assignment, AssignmentSubmission
from models.user import User, UserRole
from services.assignment import (
    add_submission_attachment,
    get_student_assignment,
    grade_submission,
    list_assignment_submissions,
    list_student_assignments,
    upsert_submission,
)

router = APIRouter(tags=["assignments"])
_teacher = require_roles(UserRole.TEACHER)


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


class SubmissionOut(BaseModel):
    id: uuid.UUID
    text: str
    score: float | None
    feedback: str
    graded_at: str | None
    submitted_at: str
    updated_at: str

    @classmethod
    def from_model(cls, s: AssignmentSubmission) -> "SubmissionOut":
        return cls(
            id=s.id, text=s.text, score=s.score, feedback=s.feedback,
            graded_at=_iso(s.graded_at), submitted_at=s.submitted_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )


class StudentAssignmentOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    due_at: str | None
    submission: SubmissionOut | None

    @classmethod
    def from_row(
        cls, a: Assignment, s: AssignmentSubmission | None
    ) -> "StudentAssignmentOut":
        return cls(
            id=a.id, title=a.title, description=a.description,
            due_at=_iso(a.due_at),
            submission=SubmissionOut.from_model(s) if s else None,
        )


class StudentAssignmentDetailOut(StudentAssignmentOut):
    teacher_attachments: list[AttachmentOut]
    submission_attachments: list[AttachmentOut]


class SubmissionRowOut(BaseModel):
    student_id: uuid.UUID
    real_name: str | None
    email: str
    submission: SubmissionOut | None


class SubmitIn(BaseModel):
    text: str = Field(default="", max_length=20_000)


class GradeIn(BaseModel):
    score: float | None = Field(default=None, ge=0)
    feedback: str = Field(default="", max_length=5_000)


# === 學生 ===


@router.get("/assignments/mine", response_model=list[StudentAssignmentOut])
async def my_assignments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> list[StudentAssignmentOut]:
    rows = await list_student_assignments(db, user.id)
    return [StudentAssignmentOut.from_row(a, s) for a, s in rows]


@router.get(
    "/assignments/mine/{assignment_id}", response_model=StudentAssignmentDetailOut
)
async def my_assignment_detail(
    assignment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> StudentAssignmentDetailOut:
    a, t_atts, sub, s_atts = await get_student_assignment(db, user.id, assignment_id)
    base = StudentAssignmentOut.from_row(a, sub)
    return StudentAssignmentDetailOut(
        **base.model_dump(),
        teacher_attachments=[AttachmentOut.from_row(r) for r in t_atts],
        submission_attachments=[AttachmentOut.from_row(r) for r in s_atts],
    )


@router.put("/assignments/{assignment_id}/submission", response_model=SubmissionOut)
async def submit(
    assignment_id: uuid.UUID,
    body: SubmitIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> SubmissionOut:
    sub = await upsert_submission(db, user.id, assignment_id, body.text)
    return SubmissionOut.from_model(sub)


@router.post(
    "/submissions/{submission_id}/attachments",
    response_model=AttachmentOut,
    status_code=201,
    dependencies=[Depends(rate_limit("upload", 20))],
)
async def upload_submission_attachment(
    submission_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_db_user),
) -> AttachmentOut:
    content = await file.read(MAX_ATTACHMENT_BYTES + 1)
    att = await add_submission_attachment(
        db, student_id=user.id, submission_id=submission_id,
        filename=file.filename or "", content_type=file.content_type or "",
        content=content,
    )
    return AttachmentOut.from_model(att)


# === 教師 ===


@router.get(
    "/assignments/{assignment_id}/submissions",
    response_model=list[SubmissionRowOut],
)
async def assignment_submissions(
    assignment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(_teacher),
) -> list[SubmissionRowOut]:
    _a, rows = await list_assignment_submissions(db, teacher.id, assignment_id)
    return [
        SubmissionRowOut(
            student_id=u.id,
            real_name=p.real_name if p else None,
            email=u.email,
            submission=SubmissionOut.from_model(s) if s else None,
        )
        for u, p, s in rows
    ]


@router.patch("/submissions/{submission_id}/grade", response_model=SubmissionOut)
async def grade(
    submission_id: uuid.UUID,
    body: GradeIn,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(_teacher),
) -> SubmissionOut:
    sub = await grade_submission(
        db, teacher.id, submission_id, body.score, body.feedback
    )
    return SubmissionOut.from_model(sub)
