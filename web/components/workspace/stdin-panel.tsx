"use client";

/**
 * 進階：預先餵入（7-R R4 降級）。
 *
 * 執行預設走**互動終端**——程式跑到 `cin` 會真的停下來等你在終端機打字，
 * 不需要事先填任何東西。本面板僅保留給兩種情境：
 * ① 想一次貼完大量測試輸入 ② runner 不可用時自動退回的批次執行路徑。
 * 因此預設收合、不再主動提示（原「程式在等待輸入」提示已無意義）。
 */

import { useState } from "react";
import { ChevronDown, ChevronRight, Keyboard } from "lucide-react";

import { useWorkspace } from "./workspace-context";

/** 程式是否使用 main 的參數（章節 58）— 用於顯示執行參數欄位 */
export function codeUsesArgs(code: string): boolean {
  return /\bmain\s*\([^)]*\bargv\b/.test(code);
}

/** 程式是否會印出「當地時間」（章節 45）— 伺服器時鐘為 UTC，需提醒 */
export function usesLocalTime(code: string): boolean {
  return /\b(localtime|strftime|asctime|ctime)\s*\(/.test(code);
}

export function StdinPanel({
  /** 程式用了 argv → 一併顯示執行參數欄位（章節 58） */
  showArgs,
}: {
  showArgs: boolean;
}) {
  const { getStdin, setStdin, getArgs, setArgs } = useWorkspace();
  const [value, setValue] = useState(getStdin);
  const [args, setArgsValue] = useState(getArgs);
  // null = 還沒手動開合過；有 argv 欄位時預設展開（那是執行前必填的）
  const [manualOpen, setManualOpen] = useState<boolean | null>(null);
  const open = manualOpen ?? showArgs;

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
        <span>進階：預先餵入</span>
        {value !== "" && (
          <span className="rounded-pill bg-surface-2 px-1.5 text-[10px] text-text-muted">
            {value.split("\n").filter((l) => l !== "").length} 行
          </span>
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
            通常不需要填——按 Run 後程式會在終端機停下來等你打字。這裡適合一次貼完大量測試輸入。
          </p>

          {showArgs && (
            <div className="mt-2">
              <label className="text-[10px] text-text-muted" htmlFor="run-args">
                執行參數（argv，以空白分隔；argv[0] 固定是程式名）
              </label>
              <input
                id="run-args"
                value={args}
                onChange={(e) => {
                  setArgsValue(e.target.value);
                  setArgs(e.target.value);
                }}
                maxLength={500}
                spellCheck={false}
                placeholder="例如：hello world"
                className="mt-1 h-7 w-full rounded-md border border-border-default bg-bg-inset px-2 font-mono text-xs text-text-primary placeholder:text-text-muted focus:border-accent-blue focus:outline-none"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
