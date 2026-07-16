"use client";

import { createContext, useContext, useRef, useCallback } from "react";

/** 執行結果 */
export interface ExecutionResult {
  stdout: string;
  stderr: string;
  compile_output: string;
  exit_code: number;
  status_description?: string;
  time?: string;
  memory?: number;
}

type ExecutionListener = (result: ExecutionResult) => void;
type KickoffListener = (reflectionId: string) => void;

interface WorkspaceContextValue {
  getCode: () => string;
  setCode: (code: string) => void;
  getExecutionResult: () => ExecutionResult | null;
  setExecutionResult: (result: ExecutionResult | null) => void;
  /** 訂閱「Run 完成」事件（auto-inject 用）。 */
  onExecutionComplete: (listener: ExecutionListener) => () => void;
  /**
   * 從 Output block 手動「💬 詢問 AI」時呼叫。
   * 若 chat panel 尚未掛載（沒有 listener），會 queue 起來等 listener 註冊時 drain。
   */
  requestChatInjection: (result: ExecutionResult) => void;
  onChatInjectionRequest: (listener: ExecutionListener) => () => void;
  /**
   * 實作題 handoff 時請求 Coddy 反思開場（chat panel 未掛載則 queue）。
   */
  requestReflectionKickoff: (reflectionId: string) => void;
  onReflectionKickoff: (listener: KickoffListener) => () => void;
  /** Chat Panel 是否展開 */
  chatOpen: boolean;
  /** 切換 Chat Panel 收合/展開 */
  toggleChat: () => void;
}

const Ctx = createContext<WorkspaceContextValue | null>(null);

interface WorkspaceProviderProps {
  chatOpen: boolean;
  toggleChat: () => void;
  children: React.ReactNode;
}

/**
 * Workspace 狀態 Provider。
 * 程式碼/執行結果用 ref（不觸發 re-render）；
 * chat toggle 用 props 從 AppShell 傳入（需觸發 re-render）。
 */
export function WorkspaceProvider({ chatOpen, toggleChat, children }: WorkspaceProviderProps) {
  const codeRef = useRef("");
  const execRef = useRef<ExecutionResult | null>(null);
  const listenersRef = useRef<Set<ExecutionListener>>(new Set());
  const injectListenersRef = useRef<Set<ExecutionListener>>(new Set());
  const pendingInjectRef = useRef<ExecutionResult[]>([]);
  const kickoffListenersRef = useRef<Set<KickoffListener>>(new Set());
  const pendingKickoffRef = useRef<string[]>([]);

  const getCode = useCallback(() => codeRef.current, []);
  const setCode = useCallback((code: string) => { codeRef.current = code; }, []);
  const getExecutionResult = useCallback(() => execRef.current, []);

  const setExecutionResult = useCallback((r: ExecutionResult | null) => {
    execRef.current = r;
    if (r) listenersRef.current.forEach((fn) => fn(r));
  }, []);

  const onExecutionComplete = useCallback((listener: ExecutionListener) => {
    listenersRef.current.add(listener);
    return () => { listenersRef.current.delete(listener); };
  }, []);

  const requestChatInjection = useCallback((r: ExecutionResult) => {
    if (injectListenersRef.current.size > 0) {
      injectListenersRef.current.forEach((fn) => fn(r));
    } else {
      // Chat panel 尚未掛載，queue 起來
      pendingInjectRef.current.push(r);
    }
  }, []);

  const onChatInjectionRequest = useCallback((listener: ExecutionListener) => {
    // 註冊時 drain queue
    if (pendingInjectRef.current.length > 0) {
      pendingInjectRef.current.forEach(listener);
      pendingInjectRef.current = [];
    }
    injectListenersRef.current.add(listener);
    return () => { injectListenersRef.current.delete(listener); };
  }, []);

  const requestReflectionKickoff = useCallback((reflectionId: string) => {
    if (kickoffListenersRef.current.size > 0) {
      kickoffListenersRef.current.forEach((fn) => fn(reflectionId));
    } else {
      pendingKickoffRef.current.push(reflectionId);
    }
  }, []);

  const onReflectionKickoff = useCallback((listener: KickoffListener) => {
    if (pendingKickoffRef.current.length > 0) {
      pendingKickoffRef.current.forEach(listener);
      pendingKickoffRef.current = [];
    }
    kickoffListenersRef.current.add(listener);
    return () => { kickoffListenersRef.current.delete(listener); };
  }, []);

  return (
    <Ctx value={{
      getCode, setCode, getExecutionResult, setExecutionResult,
      onExecutionComplete, requestChatInjection, onChatInjectionRequest,
      requestReflectionKickoff, onReflectionKickoff,
      chatOpen, toggleChat,
    }}>
      {children}
    </Ctx>
  );
}

export function useWorkspace() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useWorkspace must be inside WorkspaceProvider");
  return ctx;
}
