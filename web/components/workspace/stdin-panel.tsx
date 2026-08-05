"use client";

/**
 * 標準輸入面板（2026-08-05 驗收回饋：學生寫了 `cin` 卻沒有地方輸入）。
 *
 * Judge0 是**批次執行**（roadmap 已確認的決策，非即時互動 terminal）：程式送出後
 * 無法再互動，`cin` 讀的是送出當下附帶的 stdin。所以輸入必須**事先填好**，
 * 一行對應程式的一次讀取。
 */

import { useState } from "react";
import { ChevronDown, ChevronRight, Keyboard } from "lucide-react";

import { useWorkspace } from "./workspace-context";

/** 程式是否會讀取輸入 — 用於提示學生先填 stdin（純字串比對，零成本） */
export function codeNeedsInput(code: string): boolean {
  return /\bcin\s*>>|\bgetline\s*\(|\bscanf\s*\(|\bcin\.get/.test(code);
}

export function StdinPanel({
  /** 最近一次執行的程式需要輸入 → 預設展開並提示 */
  hintNeeded,
}: {
  hintNeeded: boolean;
}) {
  const { getStdin, setStdin } = useWorkspace();
  const [value, setValue] = useState(getStdin);
  // null = 還沒手動開合過，交給 hint 決定
  const [manualOpen, setManualOpen] = useState<boolean | null>(null);
  const showHint = hintNeeded && value === "";
  const open = manualOpen ?? showHint;

  const change = (next: string) => {
    setValue(next);
    setStdin(next);
  };

  return (
    <div className="border-b border-border-muted">
      <button
        type="button"
        onClick={() => setManualOpen(!open)}
        aria-expanded={open}
        className="flex h-7 w-full items-center gap-1.5 px-3 text-xs text-text-muted transition-colors hover:text-text-primary body-ui"
      >
        {open ? (
          <ChevronDown className="size-3" />
        ) : (
          <ChevronRight className="size-3" />
        )}
        <Keyboard className="size-3" />
        <span>輸入</span>
        {value !== "" && (
          <span className="rounded-pill bg-surface-2 px-1.5 text-[10px] text-text-muted">
            {value.split("\n").filter((l) => l !== "").length} 行
          </span>
        )}
        {showHint && (
          <span className="text-accent-orange">程式在等待輸入</span>
        )}
      </button>

      {open && (
        <div className="px-3 pb-2">
          <textarea
            value={value}
            onChange={(e) => change(e.target.value)}
            rows={3}
            maxLength={10_000}
            spellCheck={false}
            placeholder={"每行對應程式的一次讀取，例如：\nAlice\n25"}
            className="w-full resize-y rounded-md border border-border-default bg-bg-inset px-2 py-1.5 font-mono text-xs text-text-primary placeholder:text-text-muted focus:border-accent-blue focus:outline-none"
          />
          <p className="mt-1 text-[10px] text-text-muted">
            程式是一次跑完的，不能邊跑邊打字——請先在這裡填好所有 `cin` 要讀的內容，再按 Run。
          </p>
        </div>
      )}
    </div>
  );
}
