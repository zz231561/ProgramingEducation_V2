"use client";

/**
 * 執行歷史（2026-08-05 起）— 存於元件樹之外，開合側欄／收合 Output 都不會清空。
 *
 * module-level store + `useSyncExternalStore`：
 * - 存活於元件樹之外，任何 unmount 都不影響
 * - 寫入 sessionStorage：同分頁重整仍看得到，關掉分頁即清除
 *   （共用電腦不留下他人的程式輸出）
 *
 * 7-U4（2026-08-06）：改為**每個檔案各自一份歷史**。切換檔案時看到的是那個
 * 檔案自己的執行紀錄，不會混入別支程式的輸出。上限刻意保守以免 sessionStorage
 * 膨脹：每檔 20 次、最多 5 個檔案（LRU 淘汰最久沒用到的）。
 */

import { useSyncExternalStore } from "react";

import type { ExecutionResult, RunRecord } from "./types";

const STORAGE_KEY = "workspace.runs.v2";
/** 每個檔案保留最近 N 次執行 */
const MAX_RUNS_PER_FILE = 20;
/** 最多保留幾個檔案的歷史（超過淘汰最久未使用者） */
const MAX_FILES = 5;
/** 未命名草稿的 key（草稿也是一支程式，該有自己的歷史） */
const DRAFT_KEY = "__draft__";

interface Store {
  /** 最近使用在前，供 LRU 淘汰 */
  order: string[];
  byFile: Record<string, RunRecord[]>;
}

/** SSR 快照必須是穩定參考，否則每次 render 都被判定為變更 */
const EMPTY: RunRecord[] = [];

let store: Store = { order: [], byFile: {} };
let activeKey = DRAFT_KEY;
let hydrated = false;
const listeners = new Set<() => void>();

function persist(): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch {
    // 超額或瀏覽器禁用 storage：歷史僅存在記憶體，不打擾使用者
  }
}

function notify(): void {
  listeners.forEach((fn) => fn());
}

function hydrate(): void {
  if (hydrated) return;
  hydrated = true;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Store;
      if (Array.isArray(parsed?.order) && parsed?.byFile) store = parsed;
    }
  } catch {
    // 內容毀損：留空即可，不影響本次執行
  }
}

/** 把 key 移到最前並淘汰超額檔案 */
function touch(key: string): void {
  store.order = [key, ...store.order.filter((k) => k !== key)];
  for (const stale of store.order.slice(MAX_FILES)) delete store.byFile[stale];
  store.order = store.order.slice(0, MAX_FILES);
}

function subscribe(fn: () => void): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

function getSnapshot(): RunRecord[] {
  hydrate();
  return store.byFile[activeKey] ?? EMPTY;
}

function getServerSnapshot(): RunRecord[] {
  return EMPTY;
}

/**
 * 切換目前程式（載入檔案 / 開新檔 / 另存 / 更名）。
 * `null` = 未命名草稿。切換後 Output 立即顯示該檔自己的歷史。
 */
export function setActiveRunFile(name: string | null): void {
  const key = name ?? DRAFT_KEY;
  if (key === activeKey) return;
  hydrate();
  activeKey = key;
  notify();
}

export function addRun(result: ExecutionResult): void {
  hydrate();
  const current = store.byFile[activeKey] ?? EMPTY;
  store.byFile[activeKey] = [
    { id: (current[0]?.id ?? 0) + 1, timestamp: Date.now(), result },
    ...current,
  ].slice(0, MAX_RUNS_PER_FILE);
  touch(activeKey);
  persist();
  notify();
}

/** 只清空目前檔案的歷史（別的檔案不受影響） */
export function clearRuns(): void {
  hydrate();
  delete store.byFile[activeKey];
  store.order = store.order.filter((k) => k !== activeKey);
  persist();
  notify();
}

export function useRunHistory(): RunRecord[] {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
