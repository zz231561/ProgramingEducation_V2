"use client";

import { useState, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import { getActiveReflectionId } from "@/lib/active-reflection";
import type { ExecutionResult } from "@/components/workspace/workspace-context";
import type {
  ChatItem, MessageItem, ExecutionItem,
  InteractResponse, SessionDetailResponse, ApiMessage,
} from "@/lib/chat-types";

export type { ChatItem, MessageItem, ExecutionItem } from "@/lib/chat-types";

interface UseChatOptions {
  getCode?: () => string;
  getExecutionResult?: () => object | null;
  onSessionCreated?: (id: string, title: string) => void;
}

function toMessageItem(msg: ApiMessage): MessageItem {
  return {
    type: "message",
    id: msg.id,
    role: msg.role as "user" | "assistant",
    content: msg.content,
    codeSnapshot: msg.code_snapshot ?? undefined,
    evidence: msg.evidence ?? undefined,
    createdAt: msg.created_at,
  };
}

/**
 * 聊天狀態管理 hook。
 * 管理訊息列表、session、發送、載入歷史、注入執行結果。
 */
export function useChat(options: UseChatOptions = {}) {
  const [items, setItems] = useState<ChatItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const sessionIdRef = useRef<string | null>(null);

  const sendMessage = useCallback(
    async (question: string) => {
      const code = options.getCode?.() ?? "";
      if (!question.trim()) return;

      // 樂觀更新：使用者訊息立即上畫面，後面接「Coddy思考中」indicator；
      // API 成功後以 server 版（真實 id）原位取代
      const tempId = crypto.randomUUID();
      setItems((prev) => [
        ...prev,
        {
          type: "message",
          id: tempId,
          role: "user",
          content: question,
          codeSnapshot: code || undefined,
          createdAt: new Date().toISOString(),
        },
      ]);

      setIsLoading(true);
      try {
        // Phase 2-5e：若 sessionStorage 有 active reflection_id，後端注入 EDF prompt
        const reflectionId = getActiveReflectionId();
        const res = await api<InteractResponse>("/chat/interact", {
          method: "POST",
          body: JSON.stringify({
            code,
            question,
            session_id: sessionIdRef.current,
            hint_level: 0,
            execution_result: options.getExecutionResult?.() ?? null,
            reflection_id: reflectionId,
          }),
        });

        const isNew = sessionIdRef.current !== res.session_id;
        sessionIdRef.current = res.session_id;

        setItems((prev) => [
          ...prev.map((it) =>
            it.id === tempId ? toMessageItem(res.user_message) : it,
          ),
          toMessageItem(res.assistant_message),
        ]);

        if (isNew) {
          const title = question.length > 50 ? question.slice(0, 50) : question;
          options.onSessionCreated?.(res.session_id, title);
        }
      } catch {
        // 樂觀的使用者訊息保留在畫面上，只補一則錯誤回覆
        setItems((prev) => [
          ...prev,
          {
            type: "message",
            id: crypto.randomUUID(),
            role: "assistant",
            content: "無法取得 AI 回應，請稍後再試。",
            createdAt: new Date().toISOString(),
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [options],
  );

  const loadSession = useCallback(async (sessionId: string) => {
    setIsLoading(true);
    try {
      const res = await api<SessionDetailResponse>(`/chat/sessions/${sessionId}`);
      sessionIdRef.current = sessionId;
      setItems(res.messages.map(toMessageItem));
    } catch {
      setItems([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const startNewSession = useCallback(() => {
    setItems([]);
    sessionIdRef.current = null;
  }, []);

  const injectExecutionResult = useCallback((result: ExecutionResult) => {
    const item: ExecutionItem = {
      type: "execution",
      id: crypto.randomUUID(),
      result,
      createdAt: new Date().toISOString(),
    };
    setItems((prev) => [...prev, item]);
  }, []);

  return {
    items,
    isLoading,
    sessionId: sessionIdRef.current,
    sendMessage,
    loadSession,
    startNewSession,
    injectExecutionResult,
  };
}
