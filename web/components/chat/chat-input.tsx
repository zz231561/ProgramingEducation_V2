"use client";

import { useState, useCallback } from "react";
import { LifeBuoy, Send } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string, options?: { explicitHelp?: boolean }) => void;
  disabled?: boolean;
}

// 按下「我卡住了」時代送的訊息：學生仍看得到自己發了什麼，對話不會出現空白輪
const STUCK_MESSAGE = "我卡住了，可以多給我一點提示嗎？";

/**
 * 聊天輸入框 — Enter 發送、Shift+Enter 換行。
 *
 * 「我卡住了」按鈕（7-C2a'）是學生唯一能直接影響提示深度的入口：
 * 後端的 need 估計其餘輸入都是推論，只有這個是使用者的明確動作。
 */
export function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }, [value, disabled, onSend]);

  // 輸入框有字就連同學生自己的問題送出，沒字才用預設句
  const handleStuck = useCallback(() => {
    if (disabled) return;
    onSend(value.trim() || STUCK_MESSAGE, { explicitHelp: true });
    setValue("");
  }, [value, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      // IME（中文注音等）組字中的 Enter 是「確認選字」，不可送出；
      // keyCode 229 為 Safari 在 compositionend 後仍標記 isComposing=false 的相容判斷
      if (e.nativeEvent.isComposing || e.keyCode === 229) return;
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
          onClick={handleStuck}
          disabled={disabled}
          className="flex h-8 shrink-0 items-center gap-1.5 rounded-md border border-border-default bg-btn-default-bg px-2.5 text-xs text-text-secondary transition-colors hover:bg-bg-subtle hover:text-text-primary disabled:opacity-50"
          title="告訴 Coddy 你卡住了，下一則回覆會給更具體的提示"
        >
          <LifeBuoy className="size-3.5" />
          我卡住了
        </button>
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
