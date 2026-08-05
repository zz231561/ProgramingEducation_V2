"use client";

/**
 * 複製按鈕（2026-08-05 驗收回饋：複製後沒有任何提示）。
 * 全站唯一的複製入口，確保回饋一致：圖示轉綠勾 + 「已複製」短暫顯示，
 * 沿用 Toolbar「已儲存」的 inline flash 慣例（系統目前無 toast 基礎設施）。
 */

import { useEffect, useRef, useState } from "react";
import { Check, Copy } from "lucide-react";

const FLASH_MS = 1500;

export function CopyButton({
  getText,
  label,
  disabled = false,
  className = "",
}: {
  /** 點擊時才取值，避免大量輸出在每次 render 都組字串 */
  getText: () => string;
  /** 無障礙標籤與 tooltip，例如「複製輸出」 */
  label: string;
  disabled?: boolean;
  className?: string;
}) {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(
    () => () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    },
    [],
  );

  const flash = (next: "copied" | "failed") => {
    setState(next);
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => setState("idle"), FLASH_MS);
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(getText());
      flash("copied");
    } catch {
      // 非 HTTPS 或瀏覽器拒絕授權時會落到這裡，必須讓使用者知道沒複製成功
      flash("failed");
    }
  };

  return (
    <button
      type="button"
      onClick={copy}
      disabled={disabled}
      title={label}
      aria-label={label}
      className={`flex h-6 items-center gap-1 rounded px-1.5 text-xs transition-colors disabled:opacity-40 disabled:hover:bg-transparent ${
        state === "failed"
          ? "text-accent-red"
          : "text-text-muted hover:bg-surface-2 hover:text-text-primary"
      } ${className}`}
    >
      {state === "copied" ? (
        <Check className="size-3.5 text-accent-green" />
      ) : (
        <Copy className="size-3.5" />
      )}
      {state !== "idle" && (
        <span
          className={state === "copied" ? "text-accent-green" : "text-accent-red"}
          aria-live="polite"
        >
          {state === "copied" ? "已複製" : "複製失敗"}
        </span>
      )}
    </button>
  );
}
