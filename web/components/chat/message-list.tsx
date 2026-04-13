"use client";

import { useEffect, useRef } from "react";
import { MessageSquare, Loader2 } from "lucide-react";
import { MessageBubble } from "./message-bubble";
import type { ChatMessage } from "@/hooks/use-chat";

interface MessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

/**
 * 可捲動的訊息列表 — 新訊息時自動捲到底部。
 */
export function MessageList({ messages, isLoading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return <EmptyState />;
  }

  return (
    <div className="flex-1 overflow-y-auto p-3 space-y-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {isLoading && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}

function EmptyState() {
  return (
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
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 text-text-muted">
      <Loader2 className="size-4 animate-spin" />
      <span className="text-xs">AI 導師思考中…</span>
    </div>
  );
}
