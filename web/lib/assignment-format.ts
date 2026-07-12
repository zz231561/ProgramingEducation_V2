/**
 * 作業顯示格式化 helper（5-5b）— 截止時間 + 繳交狀態徽章。
 */

import { Submission } from "./assignments";

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("zh-TW", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function formatDue(iso: string | null): string {
  return iso ? formatDateTime(iso) : "無截止時間";
}

export function isOverdue(iso: string | null): boolean {
  return iso != null && new Date(iso).getTime() < Date.now();
}

export interface StatusBadge {
  label: string;
  className: string;
}

/** 繳交狀態徽章（顏色僅語意用：綠=已評分 / 藍=已繳 / 灰=未繳）。 */
export function submissionBadge(sub: Submission | null): StatusBadge {
  if (!sub) return { label: "未繳交", className: "text-text-muted" };
  if (sub.score != null)
    return { label: `已評分 ${sub.score}`, className: "text-accent-green" };
  return { label: "已繳交", className: "text-accent-blue" };
}
