"use client";

import { Bot, User } from "lucide-react";
import type { MessageItem } from "@/lib/chat-types";

interface MessageBubbleProps {
  message: MessageItem;
}

/**
 * 單則訊息氣泡 — user 靠右、assistant 靠左。
 * 內容以純文字段落渲染（未來可擴充 markdown）。
 */
export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      <Avatar isUser={isUser} />
      <div
        className={`max-w-[80%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
          isUser
            ? "bg-accent-blue/15 text-text-primary"
            : "bg-bg-subtle text-text-primary"
        }`}
      >
        {message.content.split("\n").map((line, i) => (
          <p key={i} className={i > 0 ? "mt-1.5" : ""}>
            {line || "\u00A0"}
          </p>
        ))}
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
          : "bg-accent-green/20 text-accent-green"
      }`}
    >
      {isUser ? <User className="size-3.5" /> : <Bot className="size-3.5" />}
    </div>
  );
}
