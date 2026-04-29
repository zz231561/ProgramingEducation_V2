"use client";

import { useEffect, useRef } from "react";
import { MessageSquare, Loader2 } from "lucide-react";
import { MessageBubble } from "./message-bubble";
import { RunResultCard } from "./run-result-card";
import type { ChatItem } from "@/lib/chat-types";

interface MessageListProps {
  items: ChatItem[];
  isLoading: boolean;
}

/**
 * 可捲動的訊息列表 — 支援一般訊息和執行結果卡片。
 */
export function MessageList({ items, isLoading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [items.length, isLoading]);

  if (items.length === 0 && !isLoading) {
    return <EmptyState />;
  }

  return (
    <div className="flex-1 overflow-y-auto p-3 space-y-3">
      {items.map((item) =>
        item.type === "execution" ? (
          <RunResultCard key={item.id} result={item.result} />
        ) : (
          <MessageBubble key={item.id} message={item} />
        ),
      )}
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
