"use client";

import { Play } from "lucide-react";

interface ToolbarProps {
  /** 當前檔案名稱 */
  fileName?: string;
  /** 點擊 Run 按鈕 */
  onRun?: () => void;
  /** 是否正在執行 */
  isRunning?: boolean;
}

/**
 * Workspace Toolbar — 檔名、語言標籤、Run 按鈕
 */
export function Toolbar({
  fileName = "main.cpp",
  onRun,
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
