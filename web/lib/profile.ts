/**
 * 學生身分 profile API wrappers（5-1c-2）。
 * 對應後端 GET/POST /profile（roadmap 5-1b-3）。
 */

import { api } from "./api";

export interface StudentProfile {
  school: string;
  department: string;
  student_id: string;
  real_name: string;
  email: string;
}

export type ProfileInput = Omit<StudentProfile, "email">;

/** 取得自己的 profile；未填時後端回 404（caller 需自行處理）。 */
export function getMyProfile(): Promise<StudentProfile> {
  return api<StudentProfile>("/profile");
}

/** 提交/更新 profile（upsert）。 */
export function submitProfile(data: ProfileInput): Promise<StudentProfile> {
  return api<StudentProfile>("/profile", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
