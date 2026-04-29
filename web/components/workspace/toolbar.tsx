"use client";

import { Play } from "lucide-react";

interface ToolbarProps {
  fileName?: string;
  /** 程式碼自上次成功執行後是否已修改 */
  isDirty?: boolean;
  onRun?: () => void;
  isRunning?: boolean;
}

/**
 * Workspace 頁面 Toolbar — 檔名 + 修改狀態 dot + 語言 badge + Run 按鈕。
 * Chat Toggle 移至 GlobalNav（design-plan §2.5）。
 */
export function Toolbar({
  fileName = "main.cpp",
  isDirty = false,
  onRun,
  isRunning = false,
}: ToolbarProps) {
  return (
    <div className="flex h-10 shrink-0 items-center gap-2 border-b border-border-muted bg-bg-canvas px-3 body-ui">
      <div className="flex items-center gap-1.5">
        {/* 修改狀態 dot：黃色＝有未執行的變更；隱形佔位＝乾淨 */}
        <span
          className={`size-1.5 rounded-pill ${
            isDirty ? "bg-accent-orange" : "bg-transparent"
          }`}
          title={isDirty ? "尚未執行此版本" : "已是最新執行版本"}
          aria-hidden
        />
        <span className="text-sm text-text-primary">{fileName}</span>
      </div>

      <span className="rounded-pill border border-border-default px-2 py-0.5 text-xs text-text-secondary font-medium">
        C++
      </span>

      <div className="flex-1" />

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
