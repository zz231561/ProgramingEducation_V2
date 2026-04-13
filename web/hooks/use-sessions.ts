"use client";

import { useState, useCallback, useEffect } from "react";
import { api } from "@/lib/api";

/** Session 摘要 */
export interface ChatSession {
  id: string;
  title: string;
  updatedAt: string;
}

interface SessionListResponse {
  sessions: Array<{
    id: string;
    title: string;
    updated_at: string;
  }>;
  total: number;
}

function toSession(raw: SessionListResponse["sessions"][number]): ChatSession {
  return { id: raw.id, title: raw.title, updatedAt: raw.updated_at };
}

/**
 * Session 列表管理 hook。
 * 載入、刪除、追蹤 active session。
 */
export function useSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchSessions = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await api<SessionListResponse>("/chat/sessions?limit=50");
      setSessions(res.sessions.map(toSession));
    } catch {
      /* 後端未啟動時靜默失敗 */
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const deleteSession = useCallback(
    async (id: string) => {
      await api(`/chat/sessions/${id}`, { method: "DELETE" });
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeId === id) setActiveId(null);
    },
    [activeId],
  );

  /** 新 session 建立後加入列表頂部並設為 active */
  const addSession = useCallback((id: string, title: string) => {
    const newSession: ChatSession = {
      id,
      title,
      updatedAt: new Date().toISOString(),
    };
    setSessions((prev) => [newSession, ...prev]);
    setActiveId(id);
  }, []);

  return {
    sessions,
    activeId,
    isLoading,
    setActiveId,
    deleteSession,
    addSession,
    refreshSessions: fetchSessions,
  };
}
