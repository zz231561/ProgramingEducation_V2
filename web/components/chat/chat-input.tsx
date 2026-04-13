"use client";

import { useState, useCallback } from "react";
import { Send } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

/**
 * 聊天輸入框 — Enter 發送、Shift+Enter 換行。
 */
export function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }, [value, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit],
  );

  return (
    <div className="shrink-0 border-t border-border-default p-3">
      <div className="flex items-end gap-2">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="輸入訊息..."
          disabled={disabled}
          rows={1}
          className="max-h-24 min-h-8 flex-1 resize-none rounded-md border border-border-default bg-bg-canvas px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-blue focus:outline-none disabled:opacity-50"
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className="flex size-8 shrink-0 items-center justify-center rounded-md bg-btn-primary-bg text-white hover:bg-btn-primary-hover transition-colors disabled:opacity-50"
          title="發送 (Enter)"
        >
          <Send className="size-4" />
        </button>
      </div>
    </div>
  );
}
