"use client";

import { MessageSquare, PanelRightClose, Trash2, Send } from "lucide-react";

interface ChatPanelProps {
  onCollapse: () => void;
}

export function ChatPanel({ onCollapse }: ChatPanelProps) {
  return (
    <div className="flex h-full flex-col bg-bg-default">
      {/* Header */}
      <div className="flex h-10 shrink-0 items-center justify-between border-b border-border-default px-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="size-4 text-accent-blue" />
          <span className="text-sm font-medium text-text-primary">
            AI 導師
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            className="flex size-7 items-center justify-center rounded-md text-text-muted hover:text-text-secondary hover:bg-bg-subtle transition-colors"
            title="清除對話"
          >
            <Trash2 className="size-3.5" />
          </button>
          <button
            onClick={onCollapse}
            className="flex size-7 items-center justify-center rounded-md text-text-muted hover:text-text-secondary hover:bg-bg-subtle transition-colors"
            title="收合面板"
          >
            <PanelRightClose className="size-3.5" />
          </button>
        </div>
      </div>

      {/* 訊息區域（佔位） */}
      <div className="flex flex-1 items-center justify-center p-4">
        <div className="text-center">
          <MessageSquare className="mx-auto size-10 text-text-muted/50" />
          <p className="mt-3 text-sm text-text-muted">
            AI 導師隨時為你解答
          </p>
          <p className="mt-1 text-xs text-text-muted/70">
            寫程式遇到問題？在這裡提問吧！
          </p>
        </div>
      </div>

      {/* 輸入區 */}
      <div className="shrink-0 border-t border-border-default p-3">
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="輸入訊息..."
            disabled
            className="h-8 flex-1 rounded-md border border-border-default bg-bg-canvas px-3 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-blue focus:outline-none disabled:opacity-50"
          />
          <button
            disabled
            className="flex size-8 shrink-0 items-center justify-center rounded-md bg-btn-primary-bg text-white hover:bg-btn-primary-hover transition-colors disabled:opacity-50"
          >
            <Send className="size-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
