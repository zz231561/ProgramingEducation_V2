"""作業指派 service（roadmap 5-5，TronClass 式文件繳交）。

crud：教師端作業 CRUD（含 due_at 編輯）；attachments：附件上傳驗證 / 下載授權 / 刪除。
"""

from services.assignment.attachments import (
    ALLOWED_EXTENSIONS,
    add_assignment_attachment,
    delete_attachment,
    get_attachment_for_download,
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

__all__ = [
    "ALLOWED_EXTENSIONS",
    "UNSET",
    "add_assignment_attachment",
    "create_assignment",
    "delete_assignment",
    "delete_attachment",
    "get_assignment",
    "get_attachment_for_download",
    "list_assignments",
    "update_assignment",
    "validate_upload",
]
