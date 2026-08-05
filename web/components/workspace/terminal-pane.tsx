"use client";

/**
 * 終端區塊 — 狀態列（排隊 / 編譯中 / 互動中）+ xterm 畫布。
 * 只在 session 進行中掛載；結束後由 Output 面板收回成 RunBlock。
 */

import { Loader2, TerminalSquare } from "lucide-react";

import { TerminalView, type TerminalHandle } from "./terminal-view";
import type { TerminalPhase } from "./use-terminal-session";

const PHASE_LABEL: Record<Exclude<TerminalPhase, "idle">, string> = {
  queued: "排隊中",
  compiling: "編譯中",
  running: "互動中 — 直接在下方輸入",
};

export function TerminalPane({
  phase,
  queuePosition,
  onData,
  onReady,
}: {
  phase: Exclude<TerminalPhase, "idle">;
  queuePosition: number;
  onData: (data: string) => void;
  onReady: (handle: TerminalHandle) => void;
}) {
  return (
    <div className="flex h-full min-h-0 flex-col gap-1.5 p-2">
      <div className="flex h-5 shrink-0 items-center gap-1.5 px-1 text-xs text-text-secondary body-ui">
        {phase === "running" ? (
          <TerminalSquare className="size-3 text-accent-green" />
        ) : (
          <Loader2 className="size-3 animate-spin" />
        )}
        <span>{PHASE_LABEL[phase]}</span>
        {phase === "queued" && queuePosition > 0 && (
          <span className="text-text-muted">（前面還有 {queuePosition} 位）</span>
        )}
      </div>
      <div className="min-h-0 flex-1">
        <TerminalView onData={onData} onReady={onReady} />
      </div>
    </div>
  );
}
