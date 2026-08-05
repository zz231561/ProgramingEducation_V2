"use client";

import { useState, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import { interactStream, type InteractStage } from "@/lib/chat-interact";
import { getActiveReflectionId } from "@/lib/active-reflection";
import { computeHintLevel } from "@/lib/hint-escalation";
import type { ExecutionResult } from "@/components/workspace/workspace-context";
import type {
  ChatItem, MessageItem, ExecutionItem,
  SessionDetailResponse, ApiMessage,
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
    citations: msg.citations ?? undefined,
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
  // 7-U6：EDF 管線目前跑到哪一層（null = 尚未收到第一則進度）
  const [stage, setStage] = useState<InteractStage | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  // Hint Ladder 追蹤：同脈絡連續追問遞增、卡住跳級、理解／換脈絡歸零
  const hintLevelRef = useRef(0);
  const freshContextRef = useRef(true);

  const resetHintLadder = useCallback(() => {
    hintLevelRef.current = 0;
    freshContextRef.current = true;
  }, []);

  const sendMessage = useCallback(
    async (question: string) => {
      const code = options.getCode?.() ?? "";
      if (!question.trim()) return;

      const hintLevel = computeHintLevel(
        hintLevelRef.current,
        question,
        freshContextRef.current,
      );
      hintLevelRef.current = hintLevel;
      freshContextRef.current = false;

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
      setStage(null);
      try {
        // Phase 2-5e：若 sessionStorage 有 active reflection_id，後端注入 EDF prompt
        const reflectionId = getActiveReflectionId();
        const res = await interactStream(
          {
            code,
            question,
            session_id: sessionIdRef.current,
            hint_level: hintLevel,
            execution_result: options.getExecutionResult?.() ?? null,
            reflection_id: reflectionId,
          },
          setStage,
        );

        const isNew = sessionIdRef.current !== res.session_id;
        sessionIdRef.current = res.session_id;

        // DEV-7：debug 觀測掛在 assistant 訊息上（僅 dev 帳號有值）
        const assistantItem = {
          ...toMessageItem(res.assistant_message),
          debug: res.debug ?? undefined,
        };
        setItems((prev) => [
          ...prev.map((it) =>
            it.id === tempId ? toMessageItem(res.user_message) : it,
          ),
          assistantItem,
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
        setStage(null);
      }
    },
    [options],
  );

  /** Coddy 反思開場：建立新 session 並顯示開場訊息（失敗靜默，不擋流程）。 */
  const loadKickoff = useCallback(
    async (reflectionId: string) => {
      setIsLoading(true);
      try {
        const res = await api<{
          session_id: string;
          session_title: string;
          assistant_message: ApiMessage;
        }>("/chat/reflection-kickoff", {
          method: "POST",
          body: JSON.stringify({ reflection_id: reflectionId }),
        });
        resetHintLadder();
        sessionIdRef.current = res.session_id;
        setItems([toMessageItem(res.assistant_message)]);
        options.onSessionCreated?.(res.session_id, res.session_title);
      } catch {
        // 開場失敗不打擾學生；聊天功能照常可用
      } finally {
        setIsLoading(false);
      }
    },
    [options, resetHintLadder],
  );

  /**
   * 執行出問題時 Coddy 主動說明（環境限制直說 / 學生錯誤引導，後端判定）。
   * 失敗靜默：學生仍可自己提問，不因此看到錯誤訊息。
   */
  const requestRunHelp = useCallback(
    async (compileOutput: string, statusDescription = "", kind = "") => {
      setIsLoading(true);
      try {
        const res = await api<{
          session_id: string;
          session_title: string;
          assistant_message: ApiMessage;
        }>("/chat/run-help", {
          method: "POST",
          body: JSON.stringify({
            code: options.getCode?.() ?? "",
            compile_output: compileOutput,
            status_description: statusDescription,
            kind,
            session_id: sessionIdRef.current,
          }),
        });
        const isNew = sessionIdRef.current !== res.session_id;
        sessionIdRef.current = res.session_id;
        setItems((prev) => [...prev, toMessageItem(res.assistant_message)]);
        if (isNew) options.onSessionCreated?.(res.session_id, res.session_title);
      } catch {
        // 配額用盡 / 網路問題都不打擾學生
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
      resetHintLadder();
      sessionIdRef.current = sessionId;
      setItems(res.messages.map(toMessageItem));
    } catch {
      setItems([]);
    } finally {
      setIsLoading(false);
    }
  }, [resetHintLadder]);

  const startNewSession = useCallback(() => {
    setItems([]);
    sessionIdRef.current = null;
    resetHintLadder();
  }, [resetHintLadder]);

  const injectExecutionResult = useCallback((result: ExecutionResult) => {
    // 重新執行＝學生採取了行動，脈絡刷新，hint 階梯歸零重爬
    resetHintLadder();
    const item: ExecutionItem = {
      type: "execution",
      id: crypto.randomUUID(),
      result,
      createdAt: new Date().toISOString(),
    };
    setItems((prev) => [...prev, item]);
  }, [resetHintLadder]);

  return {
    items,
    isLoading,
    /** EDF 管線階段（7-U6）；null = 尚未收到進度，顯示通用等待文案 */
    stage,
    sessionId: sessionIdRef.current,
    sendMessage,
    loadKickoff,
    requestRunHelp,
    loadSession,
    startNewSession,
    injectExecutionResult,
  };
}
