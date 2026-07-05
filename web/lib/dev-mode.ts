/**
 * 開發者模式前端 helpers（DEV-2~6）— API wrappers + 幽靈解鎖開關。
 *
 * is_dev 由後端 `/dev/status` 判定（module 級快取，整個 session 只打一次）；
 * 幽靈解鎖是純前端便利開關（unit 內容本就屬於本人、後端讀取無鎖），
 * 存 localStorage 並以 CustomEvent 通知同分頁的訂閱者。
 */

import { api } from "./api";

export type ResetCategory = "mastery" | "progress" | "quiz" | "chat";

export const RESET_CATEGORY_LABEL: Record<ResetCategory, string> = {
  mastery: "熟練度",
  progress: "課程進度",
  quiz: "測驗紀錄",
  chat: "對話紀錄",
};

let statusPromise: Promise<boolean> | null = null;

/** 查詢當前帳號是否為 dev（快取；失敗一律視為 false）。 */
export function fetchIsDev(): Promise<boolean> {
  statusPromise ??= api<{ is_dev: boolean }>("/dev/status")
    .then((r) => r.is_dev)
    .catch(() => false);
  return statusPromise;
}

/** 分類重置學習資料，回傳各類別刪除列數。 */
export function devReset(
  categories: ResetCategory[],
): Promise<{ deleted: Record<string, number> }> {
  return api("/dev/reset", {
    method: "POST",
    body: JSON.stringify({ categories }),
  });
}

/** 覆寫熟練度（tags 或整章 category 擇一），回傳影響筆數。 */
export function devSetMastery(
  target: { tags?: string[]; category?: string },
  confidence: number,
): Promise<{ updated: number }> {
  return api("/dev/mastery", {
    method: "PUT",
    body: JSON.stringify({ ...target, confidence }),
  });
}

/** 切換 student ⇄ teacher 身分（真改 DB role）。 */
export function devSetRole(
  role: "student" | "teacher",
): Promise<{ role: string }> {
  return api("/dev/role", { method: "PUT", body: JSON.stringify({ role }) });
}

// === 幽靈解鎖（DEV-4）===

const GHOST_KEY = "dev-ghost-unlock";
export const GHOST_UNLOCK_EVENT = "dev-ghost-unlock-change";

export function getGhostUnlockFlag(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(GHOST_KEY) === "1";
}

export function setGhostUnlockFlag(on: boolean): void {
  window.localStorage.setItem(GHOST_KEY, on ? "1" : "0");
  window.dispatchEvent(new CustomEvent(GHOST_UNLOCK_EVENT));
}
