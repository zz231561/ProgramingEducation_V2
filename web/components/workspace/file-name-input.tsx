"use client";

/**
 * 檔名輸入框（U2e 驗收修訂）— `.cpp` 為鎖定尾綴，使用者只編輯主檔名。
 * 平台一律以 C++ 編譯，讓副檔名可自由輸入會誤導（`main.md` 也能執行）。
 */

import { forwardRef } from "react";

import { CODE_FILE_SUFFIX } from "@/lib/code-files";

export const FileNameInput = forwardRef<
  HTMLInputElement,
  {
    /** 主檔名（不含副檔名） */
    stem: string;
    onStemChange: (stem: string) => void;
    /** sm = 對話框 / 改名列；xs = 側邊欄表單 */
    size?: "sm" | "xs";
    ariaLabel: string;
    onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>) => void;
    onBlur?: () => void;
  }
>(function FileNameInput(
  { stem, onStemChange, size = "sm", ariaLabel, onKeyDown, onBlur },
  ref,
) {
  const text = size === "sm" ? "text-sm" : "text-xs";
  return (
    <div
      className={`flex ${size === "sm" ? "h-8" : "h-7"} min-w-0 flex-1 items-center gap-0.5 rounded-md border border-border-default bg-bg-canvas px-2 focus-within:border-accent-blue`}
    >
      <input
        ref={ref}
        value={stem}
        onChange={(e) => onStemChange(e.target.value)}
        onKeyDown={onKeyDown}
        onBlur={onBlur}
        maxLength={100 - CODE_FILE_SUFFIX.length}
        placeholder="檔名"
        aria-label={ariaLabel}
        className={`min-w-0 flex-1 bg-transparent ${text} text-text-primary placeholder:text-text-muted focus:outline-none`}
      />
      {/* 點到固定尾綴不該讓輸入框失焦（改名是 blur 取消） */}
      <span
        className={`shrink-0 ${text} text-text-muted`}
        onMouseDown={(e) => e.preventDefault()}
        aria-hidden
      >
        {CODE_FILE_SUFFIX}
      </span>
    </div>
  );
});
