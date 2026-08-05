/**
 * 終端 WS frame 協議 — 與 `runner/app/terminal.py` 的 docstring 為同一份契約。
 * 修改任一端務必同步另一端。
 */

import type { ExecutionResult } from "@/components/workspace/types";

/** runner → client */
export type ServerFrame =
  | { type: "queue"; position: number }
  | { type: "compiling" }
  | { type: "compile_error"; output: string; status_description: string }
  | { type: "started" }
  | { type: "output"; data: string }
  | {
      type: "exit";
      exit_code: number | null;
      status_description: string;
      time?: string;
      output_summary?: string;
    }
  | { type: "error"; code: string };

/** WS 連線位址：跨子網域直連 backend（Next.js Route Handler 無法 proxy WS）。 */
export function terminalWsUrl(): string | null {
  const configured = process.env.NEXT_PUBLIC_TERMINAL_WS_URL;
  if (configured) return configured;
  if (typeof window === "undefined") return null;
  // 未設定時退回同源（本機 dev 走 Next rewrite / 直連皆可）
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/terminal/ws`;
}

/**
 * 把終端 session 的結束狀態轉為 ExecutionResult，
 * 讓 RunBlock / Coddy 主動說明 / 行為事件沿用既有邏輯（欄位語意不變）。
 */
export function frameToExecutionResult(
  frame: ServerFrame,
  stdout: string,
): ExecutionResult {
  if (frame.type === "compile_error") {
    return {
      stdout: "",
      stderr: "",
      compile_output: frame.output,
      exit_code: -1,
      status_description: frame.status_description,
    };
  }
  if (frame.type === "exit") {
    return {
      stdout: frame.output_summary ?? stdout,
      stderr: "",
      compile_output: "",
      exit_code: frame.exit_code ?? -1,
      status_description: frame.status_description,
      time: frame.time,
    };
  }
  return {
    stdout,
    stderr: "",
    compile_output: "",
    exit_code: -1,
    status_description: "Internal Error",
  };
}
