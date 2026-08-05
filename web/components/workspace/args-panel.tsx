"use client";

/**
 * 執行參數列（argv，章節 58）。
 *
 * 原 `stdin-panel.tsx` 的殘留職責：互動終端上線後 stdin 預填已無意義而移除，
 * 但 argv 沒有互動替代方案（程式啟動當下就要決定），故保留為單行輸入。
 * 只在程式碼真的用到 `argv` 時出現，其餘情況完全不佔版面。
 */

import { useState } from "react";

import { useWorkspace } from "./workspace-context";

export function ArgsPanel() {
  const { getArgs, setArgs } = useWorkspace();
  const [args, setArgsValue] = useState(getArgs);

  return (
    <div className="flex h-8 shrink-0 items-center gap-2 border-b border-border-muted px-3">
      <label
        className="shrink-0 text-xs text-text-muted body-ui"
        htmlFor="run-args"
      >
        執行參數
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
        placeholder="以空白分隔，例如：hello world（argv[0] 固定是程式名）"
        className="h-6 flex-1 rounded border border-border-default bg-bg-inset px-2 font-mono text-xs text-text-primary placeholder:text-text-muted focus:border-accent-blue focus:outline-none"
      />
    </div>
  );
}
