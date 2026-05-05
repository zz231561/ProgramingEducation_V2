"use client";

/**
 * 提示面板（roadmap 3-2b）— 累計顯示已取得的 hints + 「再給一個提示」按鈕。
 *
 * 設計：
 * - 提示 level 強制遞增（1 → 2 → ... → 5），學生不能跳級看 level 5
 * - 達到 max=5 後按鈕 disabled
 * - 收合預設打開（學生主動點才會用到 hint）
 * - 純 prop-driven：caller 持有 hints[] 與 nextLevel
 */

import { Lightbulb, Loader2 } from "lucide-react";

import { HintResponse } from "@/lib/quiz";

interface Props {
  hints: HintResponse[];
  busy: boolean;
  onRequestNext: () => void;
}

const MAX_LEVEL = 5;

export function HintPanel({ hints, busy, onRequestNext }: Props) {
  const usedMax = hints.length >= MAX_LEVEL;
  const nextLevel = hints.length + 1;

  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs text-text-secondary">
          <Lightbulb className="size-3.5 text-accent-orange" />
          <span>提示（{hints.length} / {MAX_LEVEL} 已使用）</span>
        </div>
        <button
          type="button"
          onClick={onRequestNext}
          disabled={busy || usedMax}
          className="inline-flex h-7 items-center gap-1 rounded-md border border-btn-default-border bg-btn-default-bg px-2.5 text-xs text-text-primary hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy && <Loader2 className="size-3 animate-spin" />}
          {usedMax ? "已用完" : busy ? "生成中..." : `取得第 ${nextLevel} 個提示`}
        </button>
      </div>

      {hints.length > 0 && (
        <ol className="mt-3 space-y-2">
          {hints.map((h) => (
            <li
              key={h.level}
              className="rounded-md border border-border-muted bg-bg-canvas p-2.5 text-sm text-text-primary"
            >
              <div className="flex items-center gap-1.5 text-xs text-text-muted">
                <span className="font-mono">L{h.level}</span>
                {h.fallback && (
                  <span className="text-accent-orange">（離線 fallback）</span>
                )}
              </div>
              <p className="mt-1 leading-relaxed">{h.hint}</p>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
