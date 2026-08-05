"use client";

/**
 * 執行歷史（2026-08-05 驗收回饋）— 原本 Run block 存在 OutputPanel 的 local state，
 * 開合側邊欄／收合 Output 會讓元件樹換位置而被 unmount，輸出就整批消失。
 *
 * 改為 module-level store + `useSyncExternalStore`：
 * - 存活於元件樹之外，任何 unmount 都不影響
 * - 寫入 sessionStorage：同分頁重整仍看得到，關掉分頁即清除
 *   （共用電腦不留下他人的程式輸出）
 */

import { useSyncExternalStore } from "react";

import type { ExecutionResult, RunRecord } from "./types";

const STORAGE_KEY = "workspace.runs.v1";
/** 保留最近 N 次執行（避免 sessionStorage 無限膨脹） */
const MAX_RUNS = 20;

/** SSR 快照必須是穩定參考，否則每次 render 都被判定為變更 */
const EMPTY: RunRecord[] = [];

let runs: RunRecord[] = EMPTY;
let hydrated = false;
const listeners = new Set<() => void>();

function persist(): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(runs));
  } catch {
    // 超額或瀏覽器禁用 storage：歷史僅存在記憶體，不打擾使用者
  }
}

function commit(next: RunRecord[]): void {
  runs = next;
  persist();
  listeners.forEach((fn) => fn());
}

function subscribe(fn: () => void): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

/** 首次讀取時才還原，之後回傳同一參考（useSyncExternalStore 要求快照穩定）。 */
function getSnapshot(): RunRecord[] {
  if (!hydrated) {
    hydrated = true;
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) runs = JSON.parse(raw) as RunRecord[];
    } catch {
      // 內容毀損：留空即可，不影響本次執行
    }
  }
  return runs;
}

function getServerSnapshot(): RunRecord[] {
  return EMPTY;
}

export function addRun(result: ExecutionResult): void {
  const current = getSnapshot();
  commit(
    [
      { id: (current[0]?.id ?? 0) + 1, timestamp: Date.now(), result },
      ...current,
    ].slice(0, MAX_RUNS),
  );
}

export function clearRuns(): void {
  commit([]);
}

export function useRunHistory(): RunRecord[] {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
