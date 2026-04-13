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

interface ApiMessage {
  id: string;
  role: string;
  content: string;
  code_snapshot: string | null;
  evidence: Record<string, unknown> | null;
  created_at: string;
}

interface UseChatOptions {
  /** 取得當前編輯器程式碼 */
  getCode?: () => string;
  /** 取得最近一次執行結果 */
  getExecutionResult?: () => object | null;
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
 * 管理訊息列表、session、發送、loading 狀態。
 */
export function useChat(options: UseChatOptions = {}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const sessionIdRef = useRef<string | null>(null);

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

        sessionIdRef.current = res.session_id;
        setMessages((prev) => [
          ...prev,
          toMessage(res.user_message),
          toMessage(res.assistant_message),
        ]);
      } catch (err) {
        const fallback: ChatMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "⚠ 無法取得 AI 回應，請稍後再試。",
          createdAt: new Date().toISOString(),
        };
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "user",
            content: question,
            createdAt: new Date().toISOString(),
          },
          fallback,
        ]);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [options],
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    sessionIdRef.current = null;
  }, []);

  return { messages, isLoading, sendMessage, clearMessages };
}
