/**
 * 作業指派 API wrappers（5-5a）。對應後端 /assignments 與 /attachments。
 */

import { api } from "./api";

/** 附件白名單與大小上限（與後端 services/assignment/attachments.py 一致）。 */
export const ALLOWED_EXTENSIONS = [
  ".pdf", ".doc", ".docx", ".ppt", ".pptx",
  ".py", ".c", ".cpp", ".cc", ".h", ".hpp", ".java", ".js", ".ts",
  ".txt", ".md", ".zip",
];
export const MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024;

/** 上傳前的即時檢查（型別 + 大小）；通過回 null，否則回錯誤訊息。 */
export function validateFile(file: File): string | null {
  const dot = file.name.lastIndexOf(".");
  const ext = dot === -1 ? "" : file.name.slice(dot).toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) return "不支援的檔案類型";
  if (file.size <= 0) return "檔案內容為空";
  if (file.size > MAX_ATTACHMENT_BYTES) return "檔案超過 10MB";
  return null;
}

export interface AttachmentInfo {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export interface AssignmentInfo {
  id: string;
  class_id: string;
  title: string;
  description: string;
  due_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AssignmentDetail extends AssignmentInfo {
  attachments: AttachmentInfo[];
}

export interface CreateAssignmentInput {
  class_id: string;
  title: string;
  description?: string;
  due_at?: string | null;
}

/** 教師端可編輯欄位；due_at 傳 null = 清除截止，省略 = 保留。 */
export interface PatchAssignmentInput {
  title?: string;
  description?: string;
  due_at?: string | null;
  is_active?: boolean;
}

/** 列出教師自己的作業（可選班級過濾）。 */
export function listAssignments(classId?: string): Promise<AssignmentInfo[]> {
  const q = classId ? `?class_id=${encodeURIComponent(classId)}` : "";
  return api<AssignmentInfo[]>(`/assignments${q}`);
}

/** 取得單一作業（含附件中繼資料）。 */
export function getAssignment(id: string): Promise<AssignmentDetail> {
  return api<AssignmentDetail>(`/assignments/${id}`);
}

export function createAssignment(
  input: CreateAssignmentInput,
): Promise<AssignmentInfo> {
  return api<AssignmentInfo>("/assignments", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateAssignment(
  id: string,
  patch: PatchAssignmentInput,
): Promise<AssignmentInfo> {
  return api<AssignmentInfo>(`/assignments/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function deleteAssignment(id: string): Promise<void> {
  return api<void>(`/assignments/${id}`, { method: "DELETE" });
}

/** 上傳單一附件（multipart）；由瀏覽器自帶 Content-Type boundary。 */
export function uploadAttachment(
  assignmentId: string,
  file: File,
): Promise<AttachmentInfo> {
  const form = new FormData();
  form.append("file", file);
  return api<AttachmentInfo>(`/assignments/${assignmentId}/attachments`, {
    method: "POST",
    body: form,
  });
}

export function deleteAttachment(attachmentId: string): Promise<void> {
  return api<void>(`/attachments/${attachmentId}`, { method: "DELETE" });
}

/** 附件下載連結（走 proxy，帶 Content-Disposition attachment）。 */
export function attachmentDownloadUrl(attachmentId: string): string {
  return `/api/attachments/${attachmentId}`;
}
