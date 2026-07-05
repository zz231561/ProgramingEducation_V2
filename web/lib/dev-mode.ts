/**
 * 開發者模式前端 helpers（DEV-2~6）— API wrappers + 幽靈解鎖開關。
 *
 * is_dev 由後端 `/dev/status` 判定（module 級快取，整個 session 只打一次）；
 * 幽靈解鎖是純前端便利開關（unit 內容本就屬於本人、後端讀取無鎖），
 * 存 localStorage 並以 CustomEvent 通知同分頁的訂閱者。
 */

import type { GraphData } from "@/components/knowledge/knowledge-graph-types";

import { api } from "./api";

export type ResetCategory = "mastery" | "progress" | "quiz" | "chat";

export type DevBankQuestion = {
  id: string;
  type: string;
  bloom_level: number;
  difficulty: number;
  source: string;
  validated: boolean;
  stem: string;
};

export type DevSimulateResult = {
  injected: number;
  streak: number;
  triggered: boolean;
  suspect_tags: string[];
};

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

/** 注入指定 concept 連續答錯 N 次，回傳診斷摘要（DEV-8）。 */
export function devSimulateFailures(
  tag: string,
  count = 3,
): Promise<DevSimulateResult> {
  return api("/dev/simulate-failures", {
    method: "POST",
    body: JSON.stringify({ tag, count }),
  });
}

/** 列出指定 concept 的題庫題目（DEV-9）。 */
export function devListQuestions(
  tag: string,
): Promise<{ questions: DevBankQuestion[] }> {
  return api(`/dev/questions?tag=${encodeURIComponent(tag)}`);
}

let graphPromise: Promise<GraphData> | null = null;

/** 概念圖快取（多張 dev 卡共用下拉選單資料，整個 session 只打一次）。 */
export function fetchConceptGraph(): Promise<GraphData> {
  graphPromise ??= api<GraphData>("/concepts/graph");
  return graphPromise;
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
