"use client";

import { useState, useCallback, useEffect } from "react";
import {
  Panel,
  Group as PanelGroup,
  Separator as PanelResizeHandle,
} from "react-resizable-panels";
import { TooltipProvider } from "@/components/ui/tooltip";
import { GlobalNav } from "./global-nav";
import { ChatPanel } from "./chat-panel";
import { StatusBar } from "./status-bar";
import { MobileNav } from "./mobile-nav";
import { TabletHeader } from "./tablet-header";
import { useBreakpoint } from "@/hooks/use-breakpoint";
import { WorkspaceProvider } from "@/components/workspace/workspace-context";
import { ChatRuntimeProvider } from "@/components/chat/chat-runtime";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [chatOpen, setChatOpen] = useState(true);
  const breakpoint = useBreakpoint();
  const toggleChat = useCallback(() => setChatOpen((v) => !v), []);

  /* Ctrl+B 收合/展開 Chat */
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.ctrlKey && e.key === "b") {
        e.preventDefault();
        toggleChat();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [toggleChat]);

  return (
    <WorkspaceProvider chatOpen={chatOpen} toggleChat={toggleChat}>
      {/* Chat 狀態必須在 ShellLayout 之外：ChatPanel 收合會 unmount（A1） */}
      <ChatRuntimeProvider>
        <TooltipProvider delay={400}>
          <ShellLayout
            breakpoint={breakpoint}
            chatOpen={chatOpen}
            toggleChat={toggleChat}
          >
            {children}
          </ShellLayout>
        </TooltipProvider>
      </ChatRuntimeProvider>
    </WorkspaceProvider>
  );
}

interface ShellLayoutProps {
  breakpoint: string;
  chatOpen: boolean;
  toggleChat: () => void;
  children: React.ReactNode;
}

function ShellLayout({ breakpoint, chatOpen, toggleChat, children }: ShellLayoutProps) {
  if (breakpoint === "mobile") {
    return (
      <div className="flex h-full flex-col">
        <main className="flex-1 overflow-auto bg-bg-canvas">{children}</main>
        <MobileNav />
      </div>
    );
  }

  if (breakpoint === "tablet") {
    return (
      <div className="flex h-full flex-col">
        <TabletHeader onToggleChat={toggleChat} />
        <div className="relative flex flex-1 flex-col overflow-hidden">
          <main className="flex-1 overflow-auto bg-bg-canvas">{children}</main>
          {/* frontend.md：平板為 bottom sheet（A2 前補了按鈕卻沒有面板） */}
          {chatOpen && (
            <div className="absolute inset-x-0 bottom-0 z-30 h-[60%] border-t border-border-default shadow-modal">
              <ChatPanel onCollapse={toggleChat} />
            </div>
          )}
        </div>
        <StatusBar />
      </div>
    );
  }

  if (breakpoint === "laptop") {
    return (
      <div className="flex h-full flex-col">
        <GlobalNav chatOpen={chatOpen} onToggleChat={toggleChat} />
        <div className="relative flex flex-1 overflow-hidden">
          <main className="flex-1 overflow-auto bg-bg-canvas">{children}</main>
          {chatOpen && (
            <div className="absolute right-0 top-0 z-30 h-[calc(100%-24px)] w-[400px] border-l border-border-default shadow-modal">
              <ChatPanel onCollapse={toggleChat} />
            </div>
          )}
        </div>
        <StatusBar />
      </div>
    );
  }

  /* Desktop：完整三欄 + react-resizable-panels */
  return (
    <div className="flex h-full flex-col">
      <GlobalNav chatOpen={chatOpen} onToggleChat={toggleChat} />
      <div className="flex flex-1 overflow-hidden">
        <PanelGroup orientation="horizontal" className="flex-1">
          <Panel minSize="200px">
            <main className="h-full overflow-auto bg-bg-canvas">
              {children}
            </main>
          </Panel>
          {chatOpen && (
            <>
              <PanelResizeHandle className="relative flex w-1 items-center justify-center transition-colors before:absolute before:inset-y-0 before:w-px before:bg-border-default hover:before:bg-accent-blue data-[resize-handle-active]:before:bg-accent-blue" />
              <Panel
                defaultSize="350px"
                minSize="300px"
                maxSize="600px"
              >
                <ChatPanel onCollapse={toggleChat} />
              </Panel>
            </>
          )}
        </PanelGroup>
      </div>
      <StatusBar />
    </div>
  );
}
