"use client";

import { Play, Terminal } from "lucide-react";

interface ToolbarProps {
  /** 當前檔案名稱 */
  fileName?: string;
  /** 點擊 Run 按鈕 */
  onRun?: () => void;
  /** 點擊 stdin 按鈕 */
  onToggleStdin?: () => void;
  /** 是否正在執行 */
  isRunning?: boolean;
}

/**
 * Workspace Toolbar — 檔名、語言標籤、stdin、Run 按鈕
 */
export function Toolbar({
  fileName = "main.cpp",
  onRun,
  onToggleStdin,
  isRunning = false,
}: ToolbarProps) {
  return (
    <div className="flex h-10 items-center gap-2 border-b border-border-default bg-bg-default px-3">
      {/* 檔案名稱 */}
      <span className="text-sm text-text-primary">{fileName}</span>

      {/* 語言標籤 */}
      <span className="rounded bg-bg-subtle px-2 py-0.5 text-xs text-text-secondary">
        C++
      </span>

      {/* spacer */}
      <div className="flex-1" />

      {/* stdin 按鈕 */}
      <button
        onClick={onToggleStdin}
        className="flex h-7 items-center gap-1.5 rounded-md border border-border-default bg-bg-default px-2.5 text-xs text-text-secondary transition-colors hover:bg-bg-subtle hover:text-text-primary"
        title="標準輸入 (stdin)"
      >
        <Terminal className="size-3.5" />
        <span>stdin</span>
      </button>

      {/* Run 按鈕 */}
      <button
        onClick={onRun}
        disabled={isRunning}
        className="flex h-7 items-center gap-1.5 rounded-md bg-btn-primary-bg px-3 text-xs font-medium text-white transition-colors hover:bg-btn-primary-hover disabled:opacity-50"
        title="執行程式碼"
      >
        <Play className="size-3.5" />
        <span>{isRunning ? "Running..." : "Run"}</span>
      </button>
    </div>
  );
}
