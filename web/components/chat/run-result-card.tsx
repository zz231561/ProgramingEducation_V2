"use client";

import { CheckCircle, XCircle, Terminal } from "lucide-react";
import type { ExecutionResult } from "@/components/workspace/workspace-context";

interface RunResultCardProps {
  result: ExecutionResult;
}

/**
 * 執行結果摘要卡片 — 顯示在 chat 訊息列中。
 * 讓使用者知道 Coddy已取得程式執行結果。
 */
export function RunResultCard({ result }: RunResultCardProps) {
  const passed = result.status_description === "Accepted";
  const hasCompileError = !!result.compile_output;
  const hasRuntimeError = !!result.stderr;

  return (
    <div className="mx-2 rounded-md border border-border-default bg-bg-canvas p-3">
      <div className="flex items-center gap-2 text-xs font-medium text-text-muted">
        <Terminal className="size-3.5" />
        <span>程式執行結果</span>
        <StatusBadge passed={passed} hasCompileError={hasCompileError} />
      </div>

      {hasCompileError && (
        <OutputPreview label="編譯錯誤" content={result.compile_output} variant="error" />
      )}
      {hasRuntimeError && !hasCompileError && (
        <OutputPreview label="stderr" content={result.stderr} variant="error" />
      )}
      {passed && result.stdout && (
        <OutputPreview label="stdout" content={result.stdout} variant="normal" />
      )}

      <p className="mt-2 text-xs text-text-muted/70">
        Coddy已取得此執行結果，可直接提問
      </p>
    </div>
  );
}

function StatusBadge({ passed, hasCompileError }: { passed: boolean; hasCompileError: boolean }) {
  if (hasCompileError) {
    return (
      <span className="ml-auto flex items-center gap-1 text-accent-red">
        <XCircle className="size-3" /> 編譯失敗
      </span>
    );
  }
  if (passed) {
    return (
      <span className="ml-auto flex items-center gap-1 text-accent-green">
        <CheckCircle className="size-3" /> 通過
      </span>
    );
  }
  return (
    <span className="ml-auto flex items-center gap-1 text-accent-orange">
      <XCircle className="size-3" /> 執行錯誤
    </span>
  );
}

function OutputPreview({
  label,
  content,
  variant,
}: {
  label: string;
  content: string;
  variant: "normal" | "error";
}) {
  const trimmed = content.length > 200 ? content.slice(0, 200) + "…" : content;
  return (
    <div className="mt-2">
      <span className="text-xs text-text-muted">{label}:</span>
      <pre
        className={`mt-0.5 max-h-20 overflow-auto rounded bg-bg-inset px-2 py-1 font-mono text-xs ${
          variant === "error" ? "text-accent-red" : "text-text-secondary"
        }`}
      >
        {trimmed}
      </pre>
    </div>
  );
}
