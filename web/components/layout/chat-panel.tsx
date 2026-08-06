"use client";

import { useCallback } from "react";
import { Lock, PanelRightClose } from "lucide-react";
import { useAiLock } from "@/components/comprehension/ai-lock";
import { MessageList } from "@/components/chat/message-list";
import { ChatInput } from "@/components/chat/chat-input";
import { SessionList } from "@/components/chat/session-list";
import { useChatRuntime } from "@/components/chat/chat-runtime";
import { useSessions } from "@/hooks/use-sessions";

interface ChatPanelProps {
  onCollapse: () => void;
}

/**
 * Coddy Chat Panel — 訊息列表 + 輸入框 + session 管理。
 * 狀態住在 `ChatRuntimeProvider`（永遠掛載），本元件收合被 unmount 也不會丟失對話。
 */
export function ChatPanel({ onCollapse }: ChatPanelProps) {
  const {
    items, isLoading, stage, sendMessage, loadSession, startNewSession,
    sessions, activeId, setActiveId, deleteSession,
  } = useChatRuntime();
  // 變體挑戰進行中禁用 Coddy（2-6d）；非 null 即鎖住並顯示原因
  const { lockedReason } = useAiLock();

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
      <MessageList items={items} isLoading={isLoading} stage={stage} />
      {lockedReason && (
        <div className="flex shrink-0 items-center gap-1.5 border-t border-border-default px-3 py-2 text-xs text-text-secondary">
          <Lock className="size-3.5 shrink-0 text-text-muted" />
          {lockedReason}
        </div>
      )}
      <ChatInput onSend={sendMessage} disabled={isLoading || lockedReason !== null} />
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
      <span className="text-sm font-medium text-text-primary">Coddy</span>
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
