"use client";

import { MessageSquare, PanelRightClose, Trash2 } from "lucide-react";
import { MessageList } from "@/components/chat/message-list";
import { ChatInput } from "@/components/chat/chat-input";
import { useChat } from "@/hooks/use-chat";
import { useWorkspace } from "@/components/workspace/workspace-context";

interface ChatPanelProps {
  onCollapse: () => void;
}

/**
 * AI 導師 Chat Panel — 整合訊息列表 + 輸入框。
 * 從 WorkspaceContext 取得程式碼，傳給 /chat/interact API。
 */
export function ChatPanel({ onCollapse }: ChatPanelProps) {
  const { getCode, getExecutionResult } = useWorkspace();
  const { messages, isLoading, sendMessage, clearMessages } = useChat({
    getCode,
    getExecutionResult,
  });

  return (
    <div className="flex h-full flex-col bg-bg-default">
      <Header
        onClear={clearMessages}
        onCollapse={onCollapse}
        hasMessages={messages.length > 0}
      />
      <MessageList messages={messages} isLoading={isLoading} />
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}

function Header({
  onClear,
  onCollapse,
  hasMessages,
}: {
  onClear: () => void;
  onCollapse: () => void;
  hasMessages: boolean;
}) {
  return (
    <div className="flex h-10 shrink-0 items-center justify-between border-b border-border-default px-3">
      <div className="flex items-center gap-2">
        <MessageSquare className="size-4 text-accent-blue" />
        <span className="text-sm font-medium text-text-primary">AI 導師</span>
      </div>
      <div className="flex items-center gap-1">
        {hasMessages && (
          <button
            onClick={onClear}
            className="flex size-7 items-center justify-center rounded-md text-text-muted hover:text-text-secondary hover:bg-bg-subtle transition-colors"
            title="清除對話"
          >
            <Trash2 className="size-3.5" />
          </button>
        )}
        <button
          onClick={onCollapse}
          className="flex size-7 items-center justify-center rounded-md text-text-muted hover:text-text-secondary hover:bg-bg-subtle transition-colors"
          title="收合面板"
        >
          <PanelRightClose className="size-3.5" />
        </button>
      </div>
    </div>
  );
}
