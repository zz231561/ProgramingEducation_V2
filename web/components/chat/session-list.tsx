"use client";

import { useState, useRef, useEffect } from "react";
import { History, Plus, Trash2, MessageSquare } from "lucide-react";
import type { ChatSession } from "@/hooks/use-sessions";

interface SessionListProps {
  sessions: ChatSession[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onNewChat: () => void;
}

/**
 * Session 歷史下拉選單 — 點擊 History 圖示展開。
 */
export function SessionList({
  sessions,
  activeId,
  onSelect,
  onDelete,
  onNewChat,
}: SessionListProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex size-7 items-center justify-center rounded-md text-text-muted hover:text-text-secondary hover:bg-bg-subtle transition-colors"
        title="對話歷史"
      >
        <History className="size-3.5" />
      </button>

      {open && (
        <Dropdown
          sessions={sessions}
          activeId={activeId}
          onSelect={(id) => { onSelect(id); setOpen(false); }}
          onDelete={onDelete}
          onNewChat={() => { onNewChat(); setOpen(false); }}
        />
      )}
    </div>
  );
}

function Dropdown({
  sessions,
  activeId,
  onSelect,
  onDelete,
  onNewChat,
}: Omit<SessionListProps, ""> ) {
  return (
    <div className="absolute left-0 top-full z-50 mt-1 w-64 rounded-md border border-border-default bg-bg-default shadow-lg">
      <button
        onClick={onNewChat}
        className="flex w-full items-center gap-2 px-3 py-2 text-sm text-accent-blue hover:bg-bg-subtle transition-colors"
      >
        <Plus className="size-3.5" />
        新對話
      </button>

      {sessions.length === 0 && (
        <p className="px-3 py-3 text-xs text-text-muted">尚無對話歷史</p>
      )}

      <div className="max-h-60 overflow-y-auto">
        {sessions.map((s) => (
          <SessionItem
            key={s.id}
            session={s}
            isActive={s.id === activeId}
            onSelect={() => onSelect(s.id)}
            onDelete={() => onDelete(s.id)}
          />
        ))}
      </div>
    </div>
  );
}

function SessionItem({
  session,
  isActive,
  onSelect,
  onDelete,
}: {
  session: ChatSession;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
}) {
  return (
    <div
      className={`group flex items-center gap-2 px-3 py-2 text-sm cursor-pointer transition-colors ${
        isActive ? "bg-bg-subtle text-text-primary" : "text-text-secondary hover:bg-bg-subtle"
      }`}
      onClick={onSelect}
    >
      <MessageSquare className="size-3.5 shrink-0 text-text-muted" />
      <span className="flex-1 truncate">{session.title}</span>
      <button
        onClick={(e) => { e.stopPropagation(); onDelete(); }}
        className="hidden size-5 items-center justify-center rounded text-text-muted hover:text-accent-red group-hover:flex"
        title="刪除對話"
      >
        <Trash2 className="size-3" />
      </button>
    </div>
  );
}
