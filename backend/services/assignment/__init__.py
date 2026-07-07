"""作業指派 service（roadmap 5-5，TronClass 式文件繳交）。

crud：教師端作業 CRUD（含 due_at 編輯）；attachments：附件上傳驗證 / 下載授權 / 刪除。
"""

from services.assignment.attachments import (
    ALLOWED_EXTENSIONS,
    add_assignment_attachment,
    build_attachment,
    delete_attachment,
    get_attachment_for_download,
    list_attachment_meta,
    validate_upload,
)
from services.assignment.crud import (
    UNSET,
    create_assignment,
    delete_assignment,
    get_assignment,
    list_assignments,
    update_assignment,
)
from services.assignment.submissions import (
    add_submission_attachment,
    get_student_assignment,
    grade_submission,
    list_assignment_submissions,
    list_student_assignments,
    upsert_submission,
)

__all__ = [
    "ALLOWED_EXTENSIONS",
    "UNSET",
    "add_assignment_attachment",
    "add_submission_attachment",
    "build_attachment",
    "create_assignment",
    "delete_assignment",
    "delete_attachment",
    "get_assignment",
    "get_attachment_for_download",
    "get_student_assignment",
    "grade_submission",
    "list_assignment_submissions",
    "list_assignments",
    "list_attachment_meta",
    "list_student_assignments",
    "update_assignment",
    "upsert_submission",
    "validate_upload",
]
