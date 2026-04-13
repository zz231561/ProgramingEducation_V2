"use client";

import { useState, useCallback, useRef } from "react";
import { api } from "@/lib/api";

/** 單則訊息 */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  codeSnapshot?: string;
  createdAt: string;
}

/** /chat/interact 回應格式 */
interface InteractResponse {
  session_id: string;
  user_message: ApiMessage;
  assistant_message: ApiMessage;
}

/** /chat/sessions/{id} 回應格式 */
interface SessionDetailResponse {
  session: { id: string; title: string; updated_at: string };
  messages: ApiMessage[];
}

interface ApiMessage {
  id: string;
  role: string;
  content: string;
  code_snapshot: string | null;
  evidence: Record<string, unknown> | null;
  created_at: string;
}

interface UseChatOptions {
  getCode?: () => string;
  getExecutionResult?: () => object | null;
  /** 新 session 建立後的回呼（供 useSessions 同步列表） */
  onSessionCreated?: (id: string, title: string) => void;
}

function toMessage(msg: ApiMessage): ChatMessage {
  return {
    id: msg.id,
    role: msg.role as "user" | "assistant",
    content: msg.content,
    codeSnapshot: msg.code_snapshot ?? undefined,
    createdAt: msg.created_at,
  };
}

/**
 * 聊天狀態管理 hook。
 * 管理訊息列表、session、發送、載入歷史。
 */
export function useChat(options: UseChatOptions = {}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const sessionIdRef = useRef<string | null>(null);

  /** 發送訊息至 EDF pipeline */
  const sendMessage = useCallback(
    async (question: string) => {
      const code = options.getCode?.() ?? "";
      if (!question.trim()) return;

      setIsLoading(true);
      try {
        const res = await api<InteractResponse>("/chat/interact", {
          method: "POST",
          body: JSON.stringify({
            code,
            question,
            session_id: sessionIdRef.current,
            hint_level: 0,
            execution_result: options.getExecutionResult?.() ?? null,
          }),
        });

        const isNew = sessionIdRef.current !== res.session_id;
        sessionIdRef.current = res.session_id;

        setMessages((prev) => [
          ...prev,
          toMessage(res.user_message),
          toMessage(res.assistant_message),
        ]);

        if (isNew) {
          const title = question.length > 50 ? question.slice(0, 50) : question;
          options.onSessionCreated?.(res.session_id, title);
        }
      } catch {
        setMessages((prev) => [
          ...prev,
          { id: crypto.randomUUID(), role: "user", content: question, createdAt: new Date().toISOString() },
          { id: crypto.randomUUID(), role: "assistant", content: "⚠ 無法取得 AI 回應，請稍後再試。", createdAt: new Date().toISOString() },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [options],
  );

  /** 載入既有 session 的歷史訊息 */
  const loadSession = useCallback(async (sessionId: string) => {
    setIsLoading(true);
    try {
      const res = await api<SessionDetailResponse>(`/chat/sessions/${sessionId}`);
      sessionIdRef.current = sessionId;
      setMessages(res.messages.map(toMessage));
    } catch {
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /** 開始新對話（清空目前訊息，不建立 DB record） */
  const startNewSession = useCallback(() => {
    setMessages([]);
    sessionIdRef.current = null;
  }, []);

  return {
    messages,
    isLoading,
    sessionId: sessionIdRef.current,
    sendMessage,
    loadSession,
    startNewSession,
  };
}
