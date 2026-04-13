"use client";

import { createContext, useContext, useRef, useCallback } from "react";

/** 執行結果 */
export interface ExecutionResult {
  stdout: string;
  stderr: string;
  compile_output: string;
  exit_code: number;
  status_description?: string;
}

type ExecutionListener = (result: ExecutionResult) => void;

interface WorkspaceContextValue {
  getCode: () => string;
  setCode: (code: string) => void;
  getExecutionResult: () => ExecutionResult | null;
  /** 更新執行結果，同時通知所有訂閱者 */
  setExecutionResult: (result: ExecutionResult | null) => void;
  /** 訂閱執行完成事件，回傳 unsubscribe 函式 */
  onExecutionComplete: (listener: ExecutionListener) => () => void;
}

const Ctx = createContext<WorkspaceContextValue | null>(null);

/**
 * Workspace 狀態 Provider — 用 ref 儲存避免不必要的 re-render。
 * 提供執行事件訂閱機制供 Chat Panel 監聽。
 */
export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const codeRef = useRef("");
  const execRef = useRef<ExecutionResult | null>(null);
  const listenersRef = useRef<Set<ExecutionListener>>(new Set());

  const getCode = useCallback(() => codeRef.current, []);
  const setCode = useCallback((code: string) => {
    codeRef.current = code;
  }, []);
  const getExecutionResult = useCallback(() => execRef.current, []);

  const setExecutionResult = useCallback((r: ExecutionResult | null) => {
    execRef.current = r;
    if (r) {
      listenersRef.current.forEach((fn) => fn(r));
    }
  }, []);

  const onExecutionComplete = useCallback((listener: ExecutionListener) => {
    listenersRef.current.add(listener);
    return () => { listenersRef.current.delete(listener); };
  }, []);

  return (
    <Ctx value={{ getCode, setCode, getExecutionResult, setExecutionResult, onExecutionComplete }}>
      {children}
    </Ctx>
  );
}

/** 取得 WorkspaceContext — 必須在 WorkspaceProvider 內使用 */
export function useWorkspace() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useWorkspace must be inside WorkspaceProvider");
  return ctx;
}
