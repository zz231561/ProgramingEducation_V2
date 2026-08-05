"use client";

import { useEffect, useRef } from "react";
import { MessageSquare, Loader2 } from "lucide-react";

import { STAGE_LABEL, type InteractStage } from "@/lib/chat-interact";

/** 進度條顯示順序，與後端推播順序一致 */
const STAGE_ORDER: InteractStage[] = ["analyzing", "retrieving", "composing"];
import { MessageBubble } from "./message-bubble";
import { RunResultCard } from "./run-result-card";
import type { ChatItem } from "@/lib/chat-types";

interface MessageListProps {
  items: ChatItem[];
  isLoading: boolean;
  /** EDF 管線階段（7-U6）；null = 尚未收到進度 */
  stage?: InteractStage | null;
}

/**
 * 可捲動的訊息列表 — 支援一般訊息和執行結果卡片。
 */
export function MessageList({ items, isLoading, stage }: MessageListProps) {
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
      {isLoading && <TypingIndicator stage={stage} />}
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
          Coddy隨時為你解答
        </p>
        <p className="mt-1 text-xs text-text-muted/70">
          寫程式遇到問題？在這裡提問吧！
        </p>
      </div>
    </div>
  );
}

/**
 * 等待指示器（7-U6）— 顯示 EDF 管線實際跑到哪一層。
 *
 * 刻意不做假的打字機動畫：後端每進一層就推一次 SSE，這裡顯示的是真實進度，
 * 對學生也更有資訊量（知道它正在查教材，而不只是「在想」）。
 */
function TypingIndicator({ stage }: { stage?: InteractStage | null }) {
  const steps = STAGE_ORDER.map((s) => ({
    key: s,
    done: stage != null && STAGE_ORDER.indexOf(stage) > STAGE_ORDER.indexOf(s),
    active: stage === s,
  }));
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2 text-text-muted">
        <Loader2 className="size-4 animate-spin" />
        <span className="text-xs">
          {stage ? `${STAGE_LABEL[stage]}…` : "Coddy思考中…"}
        </span>
      </div>
      {/* 三段進度：已完成填滿、進行中半亮、未開始留白 */}
      <div className="flex gap-1 pl-6">
        {steps.map(({ key, done, active }) => (
          <span
            key={key}
            className={`h-0.5 w-8 rounded-pill transition-colors ${
              done
                ? "bg-accent-blue"
                : active
                  ? "bg-accent-blue/50"
                  : "bg-border-default"
            }`}
          />
        ))}
      </div>
    </div>
  );
}
