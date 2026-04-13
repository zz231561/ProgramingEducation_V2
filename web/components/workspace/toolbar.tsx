"use client";

import { Play, MessageSquare } from "lucide-react";
import { useWorkspace } from "./workspace-context";

interface ToolbarProps {
  fileName?: string;
  onRun?: () => void;
  isRunning?: boolean;
}

/**
 * Workspace Toolbar — 檔名、語言標籤、Run 按鈕、AI toggle
 */
export function Toolbar({
  fileName = "main.cpp",
  onRun,
  isRunning = false,
}: ToolbarProps) {
  const { chatOpen, toggleChat } = useWorkspace();

  return (
    <div className="flex h-10 items-center gap-2 border-b border-border-default bg-bg-default px-3">
      <span className="text-sm text-text-primary">{fileName}</span>
      <span className="rounded bg-bg-subtle px-2 py-0.5 text-xs text-text-secondary">
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

      <button
        onClick={toggleChat}
        className={`flex h-7 items-center gap-1.5 rounded-md px-2.5 text-xs font-medium transition-colors ${
          chatOpen
            ? "bg-accent-blue/15 text-accent-blue"
            : "bg-btn-default-bg text-text-secondary border border-btn-default-border hover:bg-bg-subtle"
        }`}
        title={`${chatOpen ? "收合" : "展開"} AI 導師 (Ctrl+B)`}
      >
        <MessageSquare className="size-3.5" />
        <span>AI</span>
      </button>
    </div>
  );
}
