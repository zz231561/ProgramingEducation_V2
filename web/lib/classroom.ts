/**
 * 教師端班級管理 API wrappers（5-1c-1）。
 * 對應後端 /classes 與 /classes/{id}/members（roadmap 5-1b-2/3）。
 */

import { api } from "./api";

export interface ClassInfo {
  id: string;
  name: string;
  invite_code: string;
  is_active: boolean;
  member_count: number;
  created_at: string;
}

export interface ClassMember {
  user_id: string;
  email: string;
  real_name: string | null;
  school: string | null;
  department: string | null;
  student_id: string | null;
}

/** 列出教師自己的班級（含成員數，建立時間新到舊）。 */
export function listClasses(): Promise<ClassInfo[]> {
  return api<ClassInfo[]>("/classes");
}

/** 建立班級，回傳含 6 位數字邀請碼的班級資料。 */
export function createClass(name: string): Promise<ClassInfo> {
  return api<ClassInfo>("/classes", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

/** 更新班級名稱 / 啟用狀態。 */
export function updateClass(
  id: string,
  patch: { name?: string; is_active?: boolean },
): Promise<ClassInfo> {
  return api<ClassInfo>(`/classes/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

/** 取得班級名冊（學生 profile + email）。 */
export function getClassMembers(id: string): Promise<ClassMember[]> {
  return api<ClassMember[]>(`/classes/${id}/members`);
}

// === 學生端（加入班級 UI）===

export interface MyClassInfo {
  id: string;
  name: string;
  teacher_name: string;
  joined_at: string;
}

/** 學生列出自己已加入的班級。 */
export function listMyClasses(): Promise<MyClassInfo[]> {
  return api<MyClassInfo[]>("/classes/mine");
}

/** 學生以 6 位邀請碼加入班級（idempotent；未填 profile 回 409）。 */
export function joinClass(inviteCode: string): Promise<{ name: string }> {
  return api<{ name: string }>("/classes/join", {
    method: "POST",
    body: JSON.stringify({ invite_code: inviteCode }),
  });
}
