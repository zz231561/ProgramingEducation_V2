"use client";

/**
 * 互動終端 session（7-R R4）。
 *
 * 流程：POST /terminal/ticket（cookie 認證，走既有 proxy）→ 帶 ticket 連 WS
 * → start frame → 之後雙向串流。結束時把 ExecutionResult 寫回 workspace
 * （沿用 RunBlock / Coddy 主動說明 / 行為事件既有管線）。
 *
 * 若 ticket 端點回 503（runner 未啟用）則回報 unavailable，由呼叫端退回批次執行。
 */

import { useCallback, useRef, useState } from "react";

import { api } from "@/lib/api";
import {
  frameToExecutionResult,
  terminalWsUrl,
  type ServerFrame,
} from "@/lib/terminal-protocol";
import type { ExecutionResult } from "./types";

export type TerminalPhase = "idle" | "queued" | "compiling" | "running";

interface Options {
  getCode: () => string;
  getArgs: () => string;
  /** 收到輸出（寫進 xterm） */
  onOutput: (data: string) => void;
  /** session 結束（含編譯失敗）→ 寫入執行歷史 */
  onFinish: (result: ExecutionResult) => void;
  /** runner 不可用 → 呼叫端退回批次 */
  onUnavailable: () => void;
}

export function useTerminalSession({
  getCode,
  getArgs,
  onOutput,
  onFinish,
  onUnavailable,
}: Options) {
  const [phase, setPhase] = useState<TerminalPhase>("idle");
  const [queuePosition, setQueuePosition] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const stdoutRef = useRef("");

  const cleanup = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setPhase("idle");
    setQueuePosition(0);
  }, []);

  const handleFrame = useCallback(
    (frame: ServerFrame) => {
      switch (frame.type) {
        case "queue":
          setPhase("queued");
          setQueuePosition(frame.position);
          return;
        case "compiling":
          setPhase("compiling");
          setQueuePosition(0);
          return;
        case "started":
          setPhase("running");
          return;
        case "output":
          stdoutRef.current += frame.data;
          onOutput(frame.data);
          return;
        case "compile_error":
        case "exit":
          onFinish(frameToExecutionResult(frame, stdoutRef.current));
          cleanup();
          return;
        case "error":
          // RUNNER_BUSY / SESSION_LIMIT / UNAUTHORIZED 皆退回批次，學生不中斷
          cleanup();
          onUnavailable();
          return;
      }
    },
    [onOutput, onFinish, onUnavailable, cleanup],
  );

  const start = useCallback(async () => {
    const url = terminalWsUrl();
    if (!url) return onUnavailable();

    let ticket: string;
    try {
      ({ ticket } = await api<{ ticket: string }>("/terminal/ticket", {
        method: "POST",
      }));
    } catch {
      return onUnavailable(); // 503 = runner 未啟用（R5 前的常態）
    }

    stdoutRef.current = "";
    setPhase("compiling");
    const ws = new WebSocket(url);
    wsRef.current = ws;
    ws.onopen = () =>
      ws.send(
        JSON.stringify({
          type: "start",
          ticket,
          code: getCode(),
          args: getArgs(),
        }),
      );
    ws.onmessage = (e) => handleFrame(JSON.parse(e.data) as ServerFrame);
    ws.onerror = () => {
      cleanup();
      onUnavailable();
    };
    ws.onclose = () => {
      // 正常結束已由 exit frame 清理；此處只處理異常斷線
      if (wsRef.current === ws) cleanup();
    };
  }, [getCode, getArgs, handleFrame, cleanup, onUnavailable]);

  /** 使用者在終端機打字 → 送給程式的 stdin */
  const sendInput = useCallback((data: string) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "stdin", data }));
    }
  }, []);

  return { phase, queuePosition, start, sendInput, stop: cleanup };
}
