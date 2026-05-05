"use client";

/**
 * 學習路徑卡片 — list 模式（roadmap 3-1c）。
 *
 * 顯示：title / description / 進度條 / 統計。卡片整體可點選進入 detail。
 * 風格遵守 .claude/rules/frontend.md：GitHub Dark token、純色邊框、無半透明色塊。
 */

import { Trash2 } from "lucide-react";

import { PathSummary, progressPercent } from "@/lib/learning";

interface PathCardProps {
  summary: PathSummary;
  onSelect: (pathId: string) => void;
  onDelete: (pathId: string) => void;
}

export function PathCard({ summary, onSelect, onDelete }: PathCardProps) {
  const percent = progressPercent(summary);
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onSelect(summary.id)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onSelect(summary.id);
      }}
      className="group cursor-pointer rounded-md border border-border-default bg-surface-1 p-4 transition-colors hover:border-border-emphasis"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-base font-medium text-text-primary">
            {summary.title}
          </h3>
          {summary.description && (
            <p className="mt-1 line-clamp-2 text-sm text-text-secondary">
              {summary.description}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(summary.id);
          }}
          className="shrink-0 rounded p-1 text-text-muted opacity-0 transition-opacity hover:bg-surface-2 hover:text-accent-red group-hover:opacity-100"
          aria-label="刪除路徑"
        >
          <Trash2 className="size-4" />
        </button>
      </div>

      <ProgressBar percent={percent} />

      <div className="mt-2 flex items-center gap-3 text-xs text-text-muted">
        <span>
          <span className="text-text-primary">{summary.completed_units}</span>
          {" / "}
          {summary.total_units} 完成
        </span>
        {summary.available_units > 0 && (
          <span className="text-accent-green">
            {summary.available_units} 可學習
          </span>
        )}
      </div>
    </div>
  );
}

function ProgressBar({ percent }: { percent: number }) {
  return (
    <div className="mt-3 h-1.5 overflow-hidden rounded-pill bg-surface-2">
      <div
        className="h-full bg-accent-green transition-[width]"
        style={{ width: `${percent}%` }}
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
      />
    </div>
  );
}
