"use client";

/**
 * 分類重置卡（DEV-3）— 熟練度 / 課程進度 / 測驗紀錄 / 對話紀錄 + 全部。
 *
 * 二段確認：第一次點擊進入待確認（3 秒逾時還原），再點一次才執行。
 */

import { useRef, useState } from "react";

import {
  RESET_CATEGORY_LABEL,
  type ResetCategory,
  devReset,
} from "@/lib/dev-mode";

const ALL_CATEGORIES = Object.keys(RESET_CATEGORY_LABEL) as ResetCategory[];
const CONFIRM_TIMEOUT_MS = 3000;

export function DevResetCard() {
  const [armed, setArmed] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleClick = async (key: string, categories: ResetCategory[]) => {
    if (armed !== key) {
      setArmed(key);
      setMessage(null);
      setError(null);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setArmed(null), CONFIRM_TIMEOUT_MS);
      return;
    }
    if (timerRef.current) clearTimeout(timerRef.current);
    setArmed(null);
    setBusy(true);
    try {
      const { deleted } = await devReset(categories);
      const parts = Object.entries(deleted).map(
        ([k, n]) => `${RESET_CATEGORY_LABEL[k as ResetCategory]} ${n} 筆`,
      );
      setMessage(`已刪除：${parts.join("、")}`);
    } catch {
      setError("重置失敗");
    } finally {
      setBusy(false);
    }
  };

  const buttonClass = (key: string) =>
    `inline-flex h-8 items-center rounded-md border px-3 text-sm transition-colors disabled:opacity-50 ${
      armed === key
        ? "border-accent-red bg-surface-2 text-accent-red"
        : "border-btn-default-border bg-btn-default-bg text-text-primary hover:bg-surface-2"
    }`;

  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <h3 className="text-sm font-medium text-text-primary">重置學習資料</h3>
      <p className="mt-1 text-xs text-text-muted">
        分類刪除你帳號的學習資料（不可復原）。點一下待確認、3 秒內再點一次執行。
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        {ALL_CATEGORIES.map((c) => (
          <button
            key={c}
            type="button"
            disabled={busy}
            onClick={() => handleClick(c, [c])}
            className={buttonClass(c)}
          >
            {armed === c ? `確認重置${RESET_CATEGORY_LABEL[c]}？` : RESET_CATEGORY_LABEL[c]}
          </button>
        ))}
        <button
          type="button"
          disabled={busy}
          onClick={() => handleClick("all", ALL_CATEGORIES)}
          className={`${buttonClass("all")} ${armed === "all" ? "" : "border-accent-red text-accent-red"}`}
        >
          {armed === "all" ? "確認全部重置？" : "全部重置"}
        </button>
      </div>
      {message && <p className="mt-2 text-xs text-text-secondary">{message}</p>}
      {error && <p className="mt-2 text-xs text-accent-red">{error}</p>}
    </div>
  );
}
