"use client";

import {
  ChevronDown,
  ChevronRight,
  Copy,
  MessageSquare,
  Check,
  X,
  AlertOctagon,
  Clock,
  Minus,
  type LucideIcon,
} from "lucide-react";
import type { ExecutionResult } from "./workspace-context";

export type RunStatus = "accepted" | "compile-error" | "runtime-error" | "limit-exceeded" | "unknown";

export interface RunBlockData {
  id: number;
  timestamp: number;
  result: ExecutionResult;
  expanded: boolean;
}

interface RunBlockProps {
  block: RunBlockData;
  index: number; // Run #N（顯示用，最新為最大）
  onToggle: () => void;
  onSendToChat: () => void;
}

/**
 * 單次 Run 結果 block。Header 永遠顯示，body 展開時顯示 stdout/stderr/compile。
 * 視覺規格：design-plan.md §2.3
 */
export function RunBlock({ block, index, onToggle, onSendToChat }: RunBlockProps) {
  const { result, timestamp, expanded } = block;
  const status = classifyStatus(result);
  const meta = STATUS_META[status];

  const hasStdout = result.stdout.length > 0;
  const hasStderr = result.stderr.length > 0;
  const hasCompile = result.compile_output.length > 0;
  const hasAnyOutput = hasStdout || hasStderr || hasCompile;

  const handleCopy = () => {
    const parts: string[] = [];
    if (hasCompile) parts.push(`[compile]\n${result.compile_output}`);
    if (hasStdout) parts.push(`[stdout]\n${result.stdout}`);
    if (hasStderr) parts.push(`[stderr]\n${result.stderr}`);
    navigator.clipboard.writeText(parts.join("\n\n"));
  };

  return (
    <div className="rounded-md border border-border-default bg-surface-1 overflow-hidden">
      {/* Header — 32px 高，永遠可見 */}
      <div className="flex h-8 items-center gap-2 px-2 text-xs">
        <button
          onClick={onToggle}
          disabled={!hasAnyOutput}
          className="flex h-6 w-6 items-center justify-center rounded text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors disabled:opacity-40 disabled:hover:bg-transparent"
          aria-label={expanded ? "收合" : "展開"}
        >
          {expanded ? <ChevronDown className="size-3.5" /> : <ChevronRight className="size-3.5" />}
        </button>

        <span className="font-medium text-text-secondary">Run #{index}</span>

        <span className="text-text-muted body-ui">{formatTime(timestamp)}</span>

        <span className={`flex items-center gap-1 rounded-pill border px-2 py-0.5 text-xs ${meta.borderClass} ${meta.textClass}`}>
          <meta.Icon className="size-3" />
          {meta.label}
        </span>

        {result.time && (
          <span className="font-mono text-text-muted">{formatRuntime(result.time)}</span>
        )}
        {typeof result.memory === "number" && result.memory > 0 && (
          <span className="font-mono text-text-muted">{formatMemory(result.memory)}</span>
        )}

        <div className="flex-1" />

        <button
          onClick={handleCopy}
          disabled={!hasAnyOutput}
          className="flex h-6 w-6 items-center justify-center rounded text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors disabled:opacity-40 disabled:hover:bg-transparent"
          title="複製輸出"
          aria-label="複製輸出"
        >
          <Copy className="size-3.5" />
        </button>
        <button
          onClick={onSendToChat}
          className="flex h-6 w-6 items-center justify-center rounded text-text-muted hover:text-accent-blue hover:bg-surface-2 transition-colors"
          title="詢問 AI 導師"
          aria-label="詢問 AI 導師"
        >
          <MessageSquare className="size-3.5" />
        </button>
      </div>

      {/* Body — 展開且有輸出時顯示 */}
      {expanded && hasAnyOutput && (
        <div className="border-t border-border-muted bg-bg-inset px-3 py-2 space-y-2">
          {hasCompile && <OutputSection label="compile" content={result.compile_output} variant="error" />}
          {hasStdout && <OutputSection label="stdout" content={result.stdout} variant="normal" />}
          {hasStderr && <OutputSection label="stderr" content={result.stderr} variant="error" />}
        </div>
      )}
    </div>
  );
}

function OutputSection({
  label,
  content,
  variant,
}: {
  label: string;
  content: string;
  variant: "normal" | "error";
}) {
  return (
    <div>
      <div className="mb-1 text-[10px] uppercase tracking-wider text-text-muted body-ui">{label}</div>
      <pre
        className={`whitespace-pre-wrap font-mono text-xs leading-relaxed ${
          variant === "error" ? "text-accent-red" : "text-text-primary"
        }`}
      >
        {content}
      </pre>
    </div>
  );
}

/* ===== Helpers ===== */

export function classifyStatus(result: ExecutionResult): RunStatus {
  if (result.status_description === "Accepted") return "accepted";
  if (result.compile_output.length > 0) return "compile-error";
  const desc = (result.status_description ?? "").toLowerCase();
  if (desc.includes("runtime error") || desc.includes("signal")) return "runtime-error";
  if (desc.includes("time limit") || desc.includes("memory limit")) return "limit-exceeded";
  return "unknown";
}

interface StatusMeta {
  label: string;
  Icon: LucideIcon;
  textClass: string;
  borderClass: string;
}

export const STATUS_META: Record<RunStatus, StatusMeta> = {
  "accepted": {
    label: "Accepted",
    Icon: Check,
    textClass: "text-accent-green",
    borderClass: "border-accent-green",
  },
  "compile-error": {
    label: "Compile Error",
    Icon: AlertOctagon,
    textClass: "text-accent-orange",
    borderClass: "border-accent-orange",
  },
  "runtime-error": {
    label: "Runtime Error",
    Icon: X,
    textClass: "text-accent-red",
    borderClass: "border-accent-red",
  },
  "limit-exceeded": {
    label: "Limit Exceeded",
    Icon: Clock,
    textClass: "text-text-secondary",
    borderClass: "border-border-default",
  },
  "unknown": {
    label: "Unknown",
    Icon: Minus,
    textClass: "text-text-secondary",
    borderClass: "border-border-default",
  },
};

function formatTime(ts: number): string {
  const d = new Date(ts);
  return d.toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
}

function formatRuntime(time: string): string {
  const sec = parseFloat(time);
  if (Number.isNaN(sec)) return time;
  if (sec < 1) return `${Math.round(sec * 1000)}ms`;
  return `${sec.toFixed(2)}s`;
}

function formatMemory(memKB: number): string {
  if (memKB >= 1024) return `${(memKB / 1024).toFixed(1)} MB`;
  return `${memKB} KB`;
}
