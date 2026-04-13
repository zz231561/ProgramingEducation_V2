"use client";

import { useState, useCallback, useEffect } from "react";
import {
  Panel,
  Group as PanelGroup,
  Separator as PanelResizeHandle,
} from "react-resizable-panels";
import { PanelRightOpen } from "lucide-react";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ActivityBar } from "./activity-bar";
import { ChatPanel } from "./chat-panel";
import { StatusBar } from "./status-bar";
import { MobileNav } from "./mobile-nav";
import { TabletHeader } from "./tablet-header";
import { useBreakpoint } from "@/hooks/use-breakpoint";

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

  if (breakpoint === "mobile") {
    return (
      <TooltipProvider delay={400}>
        <div className="flex h-full flex-col">
          <main className="flex-1 overflow-auto bg-bg-canvas">{children}</main>
          <MobileNav />
        </div>
      </TooltipProvider>
    );
  }

  if (breakpoint === "tablet") {
    return (
      <TooltipProvider delay={400}>
        <div className="flex h-full flex-col">
          <TabletHeader onToggleChat={toggleChat} />
          <main className="flex-1 overflow-auto bg-bg-canvas">{children}</main>
          <StatusBar />
        </div>
      </TooltipProvider>
    );
  }

  if (breakpoint === "laptop") {
    return (
      <TooltipProvider delay={400}>
        <div className="flex h-full flex-col">
          <div className="flex flex-1 overflow-hidden">
            <ActivityBar />
            <main className="relative flex-1 overflow-auto bg-bg-canvas">
              {children}
              {!chatOpen && <ChatToggle onClick={toggleChat} />}
            </main>
            {chatOpen && (
              <div className="absolute right-0 top-0 z-30 h-[calc(100%-24px)] w-[400px] border-l border-border-default shadow-xl">
                <ChatPanel onCollapse={toggleChat} />
              </div>
            )}
          </div>
          <StatusBar />
        </div>
      </TooltipProvider>
    );
  }

  /* Desktop：完整三欄 + react-resizable-panels */
  return (
    <TooltipProvider delay={400}>
      <div className="flex h-full flex-col">
        <div className="flex flex-1 overflow-hidden">
          <ActivityBar />
          <PanelGroup orientation="horizontal" className="flex-1">
            <Panel minSize="200px">
              <main className="h-full overflow-auto bg-bg-canvas">
                {children}
              </main>
            </Panel>
            {chatOpen && (
              <>
                <PanelResizeHandle className="w-px bg-border-default hover:bg-accent-blue transition-colors data-[resize-handle-active]:bg-accent-blue" />
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
          {!chatOpen && <ChatToggle onClick={toggleChat} />}
        </div>
        <StatusBar />
      </div>
    </TooltipProvider>
  );
}

function ChatToggle({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="fixed right-3 top-3 z-20 flex size-8 items-center justify-center rounded-md border border-border-default bg-bg-default text-text-muted hover:text-text-secondary hover:bg-bg-subtle transition-colors"
      title="展開 AI Chat (Ctrl+B)"
    >
      <PanelRightOpen className="size-4" />
    </button>
  );
}
