"use client";

import { useCallback, useEffect, useRef } from "react";
import { PanelRightClose } from "lucide-react";
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
 * 編譯錯誤的去重簽章：取前兩行並抹掉行號欄位。
 * 學生改了程式碼但錯誤本質相同（同一行號漂移）時視為同一個錯誤，避免重複花配額。
 */
function errorSignature(compileOutput: string): string {
  return compileOutput
    .split("\n")
    .slice(0, 2)
    .join(" ")
    .replace(/:\d+:\d+:/g, ":")
    .replace(/^\s*\d+\s*\|/gm, "")
    .trim();
}

/**
 * Coddy Chat Panel — 整合訊息列表 + 輸入框 + session 管理 + 執行結果注入。
 */
export function ChatPanel({ onCollapse }: ChatPanelProps) {
  const {
    getCode, getExecutionResult, onExecutionComplete,
    onChatInjectionRequest, onReflectionKickoff,
  } = useWorkspace();
  const { sessions, activeId, setActiveId, deleteSession, addSession } = useSessions();

  const {
    items, isLoading, sendMessage, loadKickoff, loadSession,
    startNewSession, injectExecutionResult, requestCompileErrorHelp,
  } = useChat({ getCode, getExecutionResult, onSessionCreated: addSession });

  // 已主動說明過的編譯錯誤（正規化簽章）——學生沒改就重跑不再重複花配額
  const explainedRef = useRef<Set<string>>(new Set());

  /* Run 完成：注入結果卡片；編譯失敗時 Coddy 主動說明 */
  useEffect(() => {
    return onExecutionComplete((result) => {
      injectExecutionResult(result);
      const output = result.compile_output;
      const status = result.status_description ?? "";
      const timedOut = status.toLowerCase().includes("time limit");
      if (!output && !timedOut) return;
      // 逾時沒有編譯訊息，以狀態當簽章
      const signature = output ? errorSignature(output) : status;
      if (explainedRef.current.has(signature)) return;
      explainedRef.current.add(signature);
      void requestCompileErrorHelp(output, status);
    });
  }, [onExecutionComplete, injectExecutionResult, requestCompileErrorHelp]);

  /* 從 Output block「💬 詢問 AI」按鈕手動注入（含掛載前 queue drain） */
  useEffect(() => {
    return onChatInjectionRequest((result) => {
      injectExecutionResult(result);
    });
  }, [onChatInjectionRequest, injectExecutionResult]);

  /* 實作題 handoff → Coddy 反思開場（含掛載前 queue drain） */
  useEffect(() => {
    return onReflectionKickoff((reflectionId) => {
      void loadKickoff(reflectionId);
    });
  }, [onReflectionKickoff, loadKickoff]);

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
