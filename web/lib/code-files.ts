/**
 * Workspace 程式碼存檔 API wrappers（U2e）。對應後端 /code/draft 與 /code/files。
 */

import { api } from "./api";

export interface CodeDraft {
  code: string;
  /** 目前開啟的命名檔案（重整/再登入後還原檔名關聯） */
  opened_name: string | null;
  updated_at: string;
}

export interface CodeFileMeta {
  id: string;
  name: string;
  updated_at: string;
}

export interface CodeFileDetail extends CodeFileMeta {
  code: string;
}

/** 取得自動草稿；尚無草稿時後端回 404（呼叫端自行 catch）。 */
export function getDraft(): Promise<CodeDraft> {
  return api<CodeDraft>("/code/draft");
}

/** 儲存草稿；openedName 省略＝保留現有檔名關聯，傳 null＝清除。 */
export function saveDraft(
  code: string,
  openedName?: string | null,
): Promise<CodeDraft> {
  const body: Record<string, unknown> = { code };
  if (openedName !== undefined) body.opened_name = openedName;
  return api<CodeDraft>("/code/draft", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

/** 頁面卸載前的草稿搶救：keepalive 讓請求在導航後仍送達。 */
export function saveDraftBeacon(code: string): void {
  void fetch("/api/code/draft", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
    keepalive: true,
  }).catch(() => {});
}

export function listCodeFiles(): Promise<CodeFileMeta[]> {
  return api<CodeFileMeta[]>("/code/files");
}

/** 儲存命名檔案（同名覆蓋）。 */
export function saveCodeFile(name: string, code: string): Promise<CodeFileDetail> {
  return api<CodeFileDetail>("/code/files", {
    method: "PUT",
    body: JSON.stringify({ name, code }),
  });
}

export function getCodeFile(id: string): Promise<CodeFileDetail> {
  return api<CodeFileDetail>(`/code/files/${id}`);
}

export function deleteCodeFile(id: string): Promise<void> {
  return api<void>(`/code/files/${id}`, { method: "DELETE" });
}
