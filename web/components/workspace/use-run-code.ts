"use client";

/**
 * 程式碼執行 hook — 優先走互動終端（7-R R4），runner 不可用時退回批次 Judge0。
 *
 * 互動路徑：useTerminalSession 開 WS，輸出直接進 xterm，結束時 exit frame
 * 轉成 ExecutionResult 寫回 workspace（RunBlock / Coddy 主動說明皆沿用）。
 * 批次路徑：原 POST /code/execute，stdin 取自「進階：預先餵入」面板。
 */

import { useCallback, useRef, useState } from "react";

import { useWorkspace } from "@/components/workspace/workspace-context";
import { api } from "@/lib/api";
import type { TerminalHandle } from "./terminal-view";
import { useTerminalSession } from "./use-terminal-session";

/** 後端 /code/execute 回傳格式 */
interface ExecuteResponse {
  stdout: string;
  stderr: string;
  compile_output: string;
  exit_code: number | null;
  time: string | null;
  memory: number | null;
  status_description: string;
}

export function useRunCode({
  getCode,
  onRunStart,
}: {
  /** 取得編輯器目前內容 */
  getCode: () => string;
  /** 開始執行時呼叫（展開 output 面板） */
  onRunStart: () => void;
}) {
  const workspace = useWorkspace();
  const [isRunning, setIsRunning] = useState(false);
  // 程式碼自上次成功執行後是否已修改（Toolbar dot）
  const [isDirty, setIsDirty] = useState(false);
  const termRef = useRef<TerminalHandle | null>(null);
  const pendingRef = useRef<string[]>([]);

  const markChanged = useCallback(() => setIsDirty(true), []);

  const runBatch = useCallback(async () => {
    setIsRunning(true);
    try {
      const result = await api<ExecuteResponse>("/code/execute", {
        method: "POST",
        // 批次路徑：程式讀取的輸入必須在送出前一次給完
        body: JSON.stringify({
          code: getCode(),
          stdin: workspace.getStdin(),
          args: workspace.getArgs(),
        }),
      });
      workspace.setExecutionResult({
        stdout: result.stdout,
        stderr: result.stderr,
        compile_output: result.compile_output,
        exit_code: result.exit_code ?? -1,
        status_description: result.status_description,
        time: result.time ?? undefined,
        memory: result.memory ?? undefined,
      });
      setIsDirty(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "未知錯誤";
      workspace.setExecutionResult({
        stdout: "",
        stderr: msg,
        compile_output: "",
        exit_code: -1,
        status_description: "Internal Error",
      });
    } finally {
      setIsRunning(false);
    }
  }, [workspace, getCode]);

  const terminal = useTerminalSession({
    getCode,
    getArgs: workspace.getArgs,
    // xterm 是動態載入的，首批輸出可能早於 handle 就緒 → 先 buffer，attach 時 flush
    onOutput: (data) => {
      if (termRef.current) termRef.current.write(data);
      else pendingRef.current.push(data);
    },
    onFinish: (result) => {
      workspace.setExecutionResult(result);
      setIsDirty(false);
      setIsRunning(false);
    },
    onUnavailable: () => {
      setIsRunning(false);
      void runBatch();
    },
  });

  const run = useCallback(async () => {
    if (!getCode().trim()) return;
    onRunStart();
    setIsRunning(true);
    termRef.current?.clear();
    pendingRef.current = [];
    await terminal.start();
  }, [getCode, onRunStart, terminal]);

  const attachTerminal = useCallback((handle: TerminalHandle) => {
    termRef.current = handle;
    pendingRef.current.forEach((chunk) => handle.write(chunk));
    pendingRef.current = [];
  }, []);

  return {
    isRunning,
    isDirty,
    markChanged,
    run,
    /** 直接傳給 OutputPanel 的 terminal prop */
    terminal: {
      phase: terminal.phase,
      queuePosition: terminal.queuePosition,
      onData: terminal.sendInput,
      onReady: attachTerminal,
    },
  };
}
