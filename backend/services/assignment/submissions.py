"""作業繳交 service（5-5b）— 學生繳交 + 教師交件檢視/評分。

授權：學生僅能存取自己所屬班級的 active 作業與自己的繳交；教師僅能看/評自己作業的繳交。
繳交每生每作業一份（重繳覆蓋，UNIQUE 約束）。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.assignment import (
    Assignment,
    AssignmentSubmission,
    Attachment,
    AttachmentOwner,
)
from models.classroom import ClassMember
from models.student_profile import StudentProfile
from models.user import User
from services.assignment.attachments import (
    build_attachment,
    list_attachment_meta,
    list_attachment_meta_bulk,
)


async def _assignment_for_member(
    db: AsyncSession, student_id: uuid.UUID, assignment_id: uuid.UUID
) -> Assignment:
    """取 active 作業並確認學生為該班成員；否則 404（不洩漏存在性）。"""
    a = await db.get(Assignment, assignment_id)
    if a is None or not a.is_active:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "作業不存在")
    member = await db.get(
        ClassMember, {"class_id": a.class_id, "user_id": student_id}
    )
    if member is None:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "作業不存在")
    return a


async def _my_submission(
    db: AsyncSession, student_id: uuid.UUID, assignment_id: uuid.UUID
) -> AssignmentSubmission | None:
    return (
        await db.execute(
            select(AssignmentSubmission).where(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.student_id == student_id,
            )
        )
    ).scalar_one_or_none()


async def list_student_assignments(
    db: AsyncSession, student_id: uuid.UUID
) -> list[tuple[Assignment, AssignmentSubmission | None]]:
    """學生所屬班級的 active 作業 + 我的繳交狀態（新到舊）。"""
    class_ids = select(ClassMember.class_id).where(
        ClassMember.user_id == student_id
    )
    assignments = list(
        (
            await db.execute(
                select(Assignment)
                .where(
                    Assignment.class_id.in_(class_ids),
                    Assignment.is_active.is_(True),
                )
                .order_by(Assignment.created_at.desc())
            )
        ).scalars()
    )
    if not assignments:
        return []
    subs = (
        await db.execute(
            select(AssignmentSubmission).where(
                AssignmentSubmission.student_id == student_id,
                AssignmentSubmission.assignment_id.in_([a.id for a in assignments]),
            )
        )
    ).scalars()
    sub_map = {s.assignment_id: s for s in subs}
    return [(a, sub_map.get(a.id)) for a in assignments]


async def get_student_assignment(
    db: AsyncSession, student_id: uuid.UUID, assignment_id: uuid.UUID
) -> tuple[Assignment, list, AssignmentSubmission | None, list]:
    """作業詳情（教師附件）+ 我的繳交（含我的附件）。"""
    a = await _assignment_for_member(db, student_id, assignment_id)
    teacher_atts = await list_attachment_meta(
        db, owner_type=AttachmentOwner.ASSIGNMENT.value, owner_id=a.id
    )
    sub = await _my_submission(db, student_id, a.id)
    sub_atts = (
        await list_attachment_meta(
            db, owner_type=AttachmentOwner.SUBMISSION.value, owner_id=sub.id
        )
        if sub
        else []
    )
    return a, teacher_atts, sub, sub_atts


async def upsert_submission(
    db: AsyncSession, student_id: uuid.UUID, assignment_id: uuid.UUID, text: str
) -> AssignmentSubmission:
    """建立/更新我的繳交文字（截止前可重繳覆蓋；逾期不硬擋）。"""
    a = await _assignment_for_member(db, student_id, assignment_id)
    sub = await _my_submission(db, student_id, a.id)
    if sub is None:
        sub = AssignmentSubmission(
            assignment_id=a.id, student_id=student_id, text=text
        )
        db.add(sub)
    else:
        sub.text = text
    await db.commit()
    await db.refresh(sub)
    return sub


async def add_submission_attachment(
    db: AsyncSession,
    *,
    student_id: uuid.UUID,
    submission_id: uuid.UUID,
    filename: str,
    content_type: str,
    content: bytes,
) -> Attachment:
    """學生為自己的繳交新增附件。"""
    sub = await db.get(AssignmentSubmission, submission_id)
    if sub is None or sub.student_id != student_id:
        raise AppError(404, "SUBMISSION_NOT_FOUND", "繳交不存在")
    att = build_attachment(
        owner_type=AttachmentOwner.SUBMISSION.value, owner_id=submission_id,
        filename=filename, content_type=content_type, content=content,
        uploaded_by=student_id,
    )
    db.add(att)
    await db.commit()
    await db.refresh(att)
    return att


async def list_assignment_submissions(
    db: AsyncSession, teacher_id: uuid.UUID, assignment_id: uuid.UUID
) -> tuple[
    Assignment,
    list[tuple[User, StudentProfile | None, AssignmentSubmission | None, list]],
]:
    """教師交件檢視：班級名冊 × 繳交狀態 + 繳交附件 meta（僅作業擁有者）。"""
    a = await db.get(Assignment, assignment_id)
    if a is None or a.teacher_id != teacher_id:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "作業不存在")
    roster = (
        await db.execute(
            select(User, StudentProfile)
            .join(ClassMember, ClassMember.user_id == User.id)
            .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
            .where(ClassMember.class_id == a.class_id)
            .order_by(ClassMember.joined_at)
        )
    ).all()
    subs = {
        s.student_id: s
        for s in (
            await db.execute(
                select(AssignmentSubmission).where(
                    AssignmentSubmission.assignment_id == a.id
                )
            )
        ).scalars()
    }
    atts = await list_attachment_meta_bulk(
        db,
        owner_type=AttachmentOwner.SUBMISSION.value,
        owner_ids=[s.id for s in subs.values()],
    )
    rows = []
    for u, p in roster:
        s = subs.get(u.id)
        rows.append((u, p, s, atts.get(s.id, []) if s else []))
    return a, rows


async def grade_submission(
    db: AsyncSession,
    teacher_id: uuid.UUID,
    submission_id: uuid.UUID,
    score: float | None,
    feedback: str,
) -> AssignmentSubmission:
    """教師評分 + 評語（僅該作業擁有者）。"""
    sub = await db.get(AssignmentSubmission, submission_id)
    if sub is None:
        raise AppError(404, "SUBMISSION_NOT_FOUND", "繳交不存在")
    a = await db.get(Assignment, sub.assignment_id)
    if a is None or a.teacher_id != teacher_id:
        raise AppError(404, "SUBMISSION_NOT_FOUND", "繳交不存在")
    sub.score = score
    sub.feedback = feedback
    sub.graded_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(sub)
    return sub
