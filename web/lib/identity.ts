/**
 * 身分自選 / 切換 API wrapper（5-1d）。
 * 對應後端 POST /users/role（roadmap 5-1d-2）。
 */

import { api } from "./api";

export type Role = "student" | "teacher";

export interface SelectRoleResult {
  role: string;
  role_selected: boolean;
  did_reset: boolean;
}

/**
 * 自選 / 切換身分。首次選擇僅設定；已選過再改＝後端全清該帳號資料。
 */
export function selectRole(role: Role): Promise<SelectRoleResult> {
  return api<SelectRoleResult>("/users/role", {
    method: "POST",
    body: JSON.stringify({ role }),
  });
}
