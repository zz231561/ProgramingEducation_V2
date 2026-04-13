"use client";

import { createContext, useContext, useRef, useCallback } from "react";

/** 執行結果 */
export interface ExecutionResult {
  stdout: string;
  stderr: string;
  compile_output: string;
  exit_code: number;
}

interface WorkspaceContextValue {
  /** 取得當前編輯器程式碼（即時讀取 ref） */
  getCode: () => string;
  /** 更新程式碼 ref */
  setCode: (code: string) => void;
  /** 取得最近一次執行結果 */
  getExecutionResult: () => ExecutionResult | null;
  /** 更新執行結果 */
  setExecutionResult: (result: ExecutionResult | null) => void;
}

const Ctx = createContext<WorkspaceContextValue | null>(null);

/**
 * Workspace 狀態 Provider — 用 ref 儲存避免不必要的 re-render。
 * 只提供 getter/setter，不觸發 consumer re-render。
 */
export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const codeRef = useRef("");
  const execRef = useRef<ExecutionResult | null>(null);

  const getCode = useCallback(() => codeRef.current, []);
  const setCode = useCallback((code: string) => {
    codeRef.current = code;
  }, []);
  const getExecutionResult = useCallback(() => execRef.current, []);
  const setExecutionResult = useCallback((r: ExecutionResult | null) => {
    execRef.current = r;
  }, []);

  return (
    <Ctx value={{ getCode, setCode, getExecutionResult, setExecutionResult }}>
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
