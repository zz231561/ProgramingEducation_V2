"use client";

import { FilePlus, FolderOpen, ListChecks, Play } from "lucide-react";

interface ToolbarProps {
  fileName?: string;
  /** 程式碼自上次成功執行後是否已修改 */
  isDirty?: boolean;
  onRun?: () => void;
  isRunning?: boolean;
  /** 反思側邊欄是否展開（無此 prop 則不顯示 toggle 按鈕）。 */
  reflectionSidebarOpen?: boolean;
  onToggleReflectionSidebar?: () => void;
  /** 是否有 active reflection（用於在 toggle button 上顯示 dot 提示）。 */
  hasActiveReflection?: boolean;
  /** 草稿自動存檔狀態（U2e；無此 prop 則不顯示）。 */
  saveStatus?: "idle" | "saving" | "saved";
  /** 我的程式碼側邊欄是否展開（無此 prop 則不顯示 toggle 按鈕）。 */
  codeFilesSidebarOpen?: boolean;
  onToggleCodeFilesSidebar?: () => void;
  /** 開新檔案（無此 prop 則不顯示按鈕）。 */
  onNewFile?: () => void;
  /** 剛以 Ctrl/Cmd+S 存入我的程式碼（短暫顯示「已儲存」）。 */
  savedFlash?: boolean;
}

/**
 * Workspace 頁面 Toolbar — 檔名 + 修改狀態 dot + 語言 badge + Run 按鈕。
 * Chat Toggle 移至 GlobalNav（design-plan §2.5）。
 * Reflection Sidebar Toggle 在最左側（Phase 2-5d）。
 */
export function Toolbar({
  fileName = "main.cpp",
  isDirty = false,
  onRun,
  isRunning = false,
  reflectionSidebarOpen,
  onToggleReflectionSidebar,
  hasActiveReflection = false,
  saveStatus,
  codeFilesSidebarOpen,
  onToggleCodeFilesSidebar,
  onNewFile,
  savedFlash = false,
}: ToolbarProps) {
  return (
    <div className="flex h-10 shrink-0 items-center gap-2 border-b border-border-muted bg-bg-canvas px-3 body-ui">
      {onToggleCodeFilesSidebar && (
        <button
          onClick={onToggleCodeFilesSidebar}
          aria-pressed={codeFilesSidebarOpen ?? false}
          className="flex size-7 items-center justify-center rounded-md text-text-muted hover:bg-bg-subtle hover:text-text-primary aria-pressed:bg-bg-subtle aria-pressed:text-text-primary"
          title={codeFilesSidebarOpen ? "收合我的程式碼" : "展開我的程式碼"}
        >
          <FolderOpen className="size-4" />
        </button>
      )}

      {onNewFile && (
        <button
          onClick={onNewFile}
          className="flex size-7 items-center justify-center rounded-md text-text-muted hover:bg-bg-subtle hover:text-text-primary"
          title="開新檔案"
        >
          <FilePlus className="size-4" />
        </button>
      )}

      {/* 反思計畫 toggle：僅實作題檔案（handoff 開啟者）才有此按鈕 */}
      {onToggleReflectionSidebar && (
        <button
          onClick={onToggleReflectionSidebar}
          aria-pressed={reflectionSidebarOpen ?? false}
          className="relative flex size-7 items-center justify-center rounded-md text-text-muted hover:bg-bg-subtle hover:text-text-primary aria-pressed:bg-bg-subtle aria-pressed:text-text-primary"
          title={reflectionSidebarOpen ? "收合反思計畫" : "展開反思計畫"}
        >
          <ListChecks className="size-4" />
          {hasActiveReflection && !reflectionSidebarOpen && (
            <span
              className="absolute right-1 top-1 size-1.5 rounded-pill bg-accent-green"
              aria-hidden
            />
          )}
        </button>
      )}

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
        {savedFlash && (
          <span className="text-xs text-accent-green" aria-live="polite">
            已儲存
          </span>
        )}
      </div>

      <span className="rounded-pill border border-border-default px-2 py-0.5 text-xs text-text-secondary font-medium">
        C++
      </span>

      <div className="flex-1" />

      {saveStatus && saveStatus !== "idle" && (
        <span className="text-xs text-text-muted" aria-live="polite">
          {saveStatus === "saving" ? "儲存中…" : "已自動儲存"}
        </span>
      )}

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
