"use client";

import { useCallback, useEffect } from "react";
import { MessageSquare, PanelRightClose } from "lucide-react";
import { MessageList } from "@/components/chat/message-list";
import { ChatInput } from "@/components/chat/chat-input";
import { SessionList } from "@/components/chat/session-list";
import { useChat } from "@/hooks/use-chat";
import { useSessions } from "@/hooks/use-sessions";
import { useWorkspace } from "@/components/workspace/workspace-context";

interface ChatPanelProps {
  onCollapse: () => void;
}

/**
 * AI 導師 Chat Panel — 整合訊息列表 + 輸入框 + session 管理 + 執行結果注入。
 */
export function ChatPanel({ onCollapse }: ChatPanelProps) {
  const { getCode, getExecutionResult, onExecutionComplete, onChatInjectionRequest } = useWorkspace();
  const { sessions, activeId, setActiveId, deleteSession, addSession } = useSessions();

  const { items, isLoading, sendMessage, loadSession, startNewSession, injectExecutionResult } =
    useChat({ getCode, getExecutionResult, onSessionCreated: addSession });

  /* Run 完成時自動注入執行結果卡片 */
  useEffect(() => {
    return onExecutionComplete((result) => {
      injectExecutionResult(result);
    });
  }, [onExecutionComplete, injectExecutionResult]);

  /* 從 Output block「💬 詢問 AI」按鈕手動注入（含掛載前 queue drain） */
  useEffect(() => {
    return onChatInjectionRequest((result) => {
      injectExecutionResult(result);
    });
  }, [onChatInjectionRequest, injectExecutionResult]);

  const handleSelectSession = useCallback(
    async (id: string) => { setActiveId(id); await loadSession(id); },
    [setActiveId, loadSession],
  );

  const handleNewChat = useCallback(() => {
    setActiveId(null);
    startNewSession();
  }, [setActiveId, startNewSession]);

  const handleDeleteSession = useCallback(
    async (id: string) => {
      await deleteSession(id);
      if (activeId === id) startNewSession();
    },
    [deleteSession, activeId, startNewSession],
  );

  return (
    <div className="flex h-full flex-col bg-bg-default">
      <Header
        sessions={sessions}
        activeId={activeId}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        onNewChat={handleNewChat}
        onCollapse={onCollapse}
      />
      <MessageList items={items} isLoading={isLoading} />
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}

function Header({
  sessions,
  activeId,
  onSelectSession,
  onDeleteSession,
  onNewChat,
  onCollapse,
}: {
  sessions: ReturnType<typeof useSessions>["sessions"];
  activeId: string | null;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  onNewChat: () => void;
  onCollapse: () => void;
}) {
  return (
    <div className="flex h-10 shrink-0 items-center justify-between border-b border-border-default px-3">
      <div className="flex items-center gap-2">
        <MessageSquare className="size-4 text-accent-blue" />
        <span className="text-sm font-medium text-text-primary">AI 導師</span>
      </div>
      <div className="flex items-center gap-1">
        <SessionList
          sessions={sessions}
          activeId={activeId}
          onSelect={onSelectSession}
          onDelete={onDeleteSession}
          onNewChat={onNewChat}
        />
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
