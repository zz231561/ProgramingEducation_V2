"use client";

/**
 * 學習單元頁底部 action bar — 上一單元 / 主動作（開始 / 完成）/ 下一單元。
 *
 * 由 unit-content.tsx 拆出（6-2c 拆分後檔案降至 < 250 行）；
 * 純展示元件，狀態與 callback 由父層 prop-driven。
 */

import { CheckCircle2, ChevronLeft, ChevronRight, Play } from "lucide-react";

import { Unit } from "@/lib/learning";

export function NavButton({
  disabled,
  onClick,
  direction,
}: {
  disabled: boolean;
  onClick: (() => void) | undefined;
  direction: "prev" | "next";
}) {
  const isPrev = direction === "prev";
  const Icon = isPrev ? ChevronLeft : ChevronRight;
  const label = isPrev ? "上一單元" : "下一單元";
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="inline-flex h-8 items-center gap-1 rounded-md border border-btn-default-border bg-btn-default-bg px-3 text-sm text-text-primary hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40"
    >
      {isPrev && <Icon className="size-4" />}
      {label}
      {!isPrev && <Icon className="size-4" />}
    </button>
  );
}

export function ActionButton({
  unit,
  onStart,
  onComplete,
  busy,
}: {
  unit: Unit;
  onStart: () => void;
  onComplete: () => void;
  busy: boolean;
}) {
  if (unit.status === "available") {
    return (
      <button
        type="button"
        onClick={onStart}
        disabled={busy}
        className="inline-flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover disabled:opacity-50"
      >
        <Play className="size-4" />
        開始學習
      </button>
    );
  }
  if (unit.status === "in_progress") {
    return (
      <button
        type="button"
        onClick={onComplete}
        disabled={busy}
        className="inline-flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover disabled:opacity-50"
      >
        完成單元
      </button>
    );
  }
  if (unit.status === "completed") {
    return (
      <span className="inline-flex items-center gap-1.5 text-sm text-accent-green">
        <CheckCircle2 className="size-4" />
        已完成
      </span>
    );
  }
  // locked
  return (
    <span className="text-sm text-text-muted">尚未解鎖</span>
  );
}
