"use client";

/**
 * 執行歷史選單（2026-08-05 驗收回饋：歷史需要有明確入口）。
 * 沿用 Chat 對話歷史（`components/chat/session-list.tsx`）的下拉寫法：
 * 靠右對齊避免溢出、點外面關閉。選一筆即展開該次結果並捲到畫面內。
 */

import { useEffect, useRef, useState } from "react";
import { History } from "lucide-react";

import type { RunRecord } from "./types";
import { classifyStatus, formatTime, STATUS_META } from "./run-block";

export function RunHistoryMenu({
  runs,
  onSelect,
}: {
  runs: RunRecord[];
  onSelect: (id: number) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex h-6 items-center gap-1 rounded px-2 text-xs text-text-muted transition-colors hover:bg-surface-2 hover:text-text-primary body-ui"
        title="執行歷史"
      >
        <History className="size-3" />
        歷史
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-1 max-h-72 w-64 max-w-[calc(100vw-2rem)] overflow-y-auto rounded-md border border-border-default bg-bg-default shadow-modal">
          {runs.length === 0 ? (
            <p className="px-3 py-3 text-xs text-text-muted">尚無執行紀錄</p>
          ) : (
            runs.map((run) => {
              const meta = STATUS_META[classifyStatus(run.result)];
              return (
                <button
                  key={run.id}
                  onClick={() => {
                    onSelect(run.id);
                    setOpen(false);
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-xs transition-colors hover:bg-bg-subtle"
                >
                  <meta.Icon className={`size-3 shrink-0 ${meta.textClass}`} />
                  <span className="shrink-0 text-text-secondary">
                    Run #{run.id}
                  </span>
                  <span className={`flex-1 truncate text-left ${meta.textClass}`}>
                    {meta.label}
                  </span>
                  <span className="shrink-0 text-text-muted">
                    {formatTime(run.timestamp)}
                  </span>
                </button>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
