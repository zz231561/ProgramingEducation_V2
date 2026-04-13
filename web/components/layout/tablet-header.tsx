"use client";

import { PanelRightOpen } from "lucide-react";

interface TabletHeaderProps {
  onToggleChat: () => void;
}

export function TabletHeader({ onToggleChat }: TabletHeaderProps) {
  return (
    <header className="flex h-10 shrink-0 items-center justify-between border-b border-border-default bg-bg-default px-3">
      <div className="flex items-center gap-2">
        <button className="text-text-secondary hover:text-text-primary">
          <span className="text-lg">☰</span>
        </button>
        <span className="text-sm font-medium text-text-primary">
          C++ Tutor
        </span>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={onToggleChat}
          className="flex size-8 items-center justify-center rounded-md text-text-muted hover:text-text-secondary hover:bg-bg-subtle transition-colors"
        >
          <PanelRightOpen className="size-4" />
        </button>
        <div className="size-7 rounded-full bg-bg-subtle border border-border-default flex items-center justify-center text-xs text-text-secondary">
          U
        </div>
      </div>
    </header>
  );
}
