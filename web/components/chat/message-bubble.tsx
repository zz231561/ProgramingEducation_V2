"use client";

import { Bot, User } from "lucide-react";
import type { MessageItem } from "@/lib/chat-types";
import { BloomBadge, extractBloomLevel } from "./bloom-badge";
import { EdfTimeline } from "./edf-timeline";

interface MessageBubbleProps {
  message: MessageItem;
}

/**
 * 單則訊息氣泡（design-plan §2.4 統一視覺協議）：
 * - User / AI 同 surface-1 背景；以 border 顏色區分角色
 * - User: border-default（灰）；AI: border-ai（GitHub Dark purple 25% alpha）
 * - radius 12px、line-height 1.6（中文可讀性）
 * - AI 訊息上方顯示 EDF Pipeline mini timeline（design-plan §2.1）
 * - AI 訊息底部顯示 Bloom 等級 badge（若有 evidence.bloom_level）
 */
export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const bloomLevel = isUser ? null : extractBloomLevel(message.evidence);
  const showTimeline = !isUser && message.evidence !== undefined;

  return (
    <div className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      <Avatar isUser={isUser} />
      <div className="max-w-[80%]">
        {showTimeline && <EdfTimeline />}
        <div
          className={`rounded-xl border bg-surface-1 px-3 py-2 text-sm body-reading ${
            isUser ? "border-border-default" : "border-ai"
          }`}
        >
          <div className="text-text-primary">
            {message.content.split("\n").map((line, i) => (
              <p key={i} className={i > 0 ? "mt-1.5" : ""}>
                {line || " "}
              </p>
            ))}
          </div>
          {bloomLevel !== null && (
            <div className="mt-2 pt-2 border-t border-border-muted">
              <BloomBadge level={bloomLevel} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Avatar({ isUser }: { isUser: boolean }) {
  return (
    <div
      className={`flex size-7 shrink-0 items-center justify-center rounded-full ${
        isUser
          ? "bg-accent-blue/20 text-accent-blue"
          : "bg-accent-purple/20 text-accent-purple"
      }`}
    >
      {isUser ? <User className="size-3.5" /> : <Bot className="size-3.5" />}
    </div>
  );
}
