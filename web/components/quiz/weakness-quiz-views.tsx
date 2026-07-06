"use client";

/**
 * 弱項綜合測驗組（6-3d）子視圖：題數選擇 / 生成中進度 / 完成總結 / 無弱項。
 * 純展示無 state。
 */

import { Loader2, Sparkles, Target } from "lucide-react";

export function WeaknessIdleView({
  onStart,
  error,
}: {
  onStart: (count: 10 | 25) => void;
  error: string | null;
}) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 px-6 py-8 text-center">
      <Target className="mx-auto size-8 text-text-muted/60" />
      <p className="mt-3 text-sm text-text-primary">弱項綜合測驗</p>
      <p className="mt-1 text-xs text-text-secondary">
        依你的弱項與知識關聯一次出題，涵蓋單一概念與綜合應用；選擇題數：
      </p>
      <div className="mx-auto mt-5 flex max-w-xs justify-center gap-3">
        {([10, 25] as const).map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => onStart(n)}
            className="flex-1 rounded-md border border-border-default bg-surface-2 px-4 py-4 transition-colors hover:border-border-emphasis"
          >
            <p className="text-lg font-medium text-text-primary">{n}</p>
            <p className="mt-0.5 text-xs text-text-secondary">題</p>
          </button>
        ))}
      </div>
      {error && (
        <div className="mt-4 rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-left text-xs text-accent-red">
          {error}
        </div>
      )}
    </div>
  );
}

export function WeaknessGeneratingView({ count }: { count: number }) {
  return (
    <div className="flex flex-col items-center gap-4 py-14 text-text-secondary">
      <Loader2 className="size-7 animate-spin text-accent-blue" />
      <div className="w-full max-w-sm overflow-hidden rounded-pill bg-surface-2">
        <div className="h-1.5 w-1/3 animate-[quizbar_1.4s_ease-in-out_infinite] rounded-pill bg-accent-blue" />
      </div>
      <div className="text-center">
        <p className="text-sm text-text-primary">AI 正在為你出 {count} 題...</p>
        <p className="mt-1 text-xs text-text-muted">
          題庫優先取題、缺口即時生成，約需 20–40 秒
        </p>
      </div>
      <style>{`@keyframes quizbar{0%{transform:translateX(-100%)}100%{transform:translateX(400%)}}`}</style>
    </div>
  );
}

export function WeaknessSummaryView({
  total,
  correct,
  onRestart,
}: {
  total: number;
  correct: number;
  onRestart: () => void;
}) {
  const pct = total > 0 ? Math.round((correct / total) * 100) : 0;
  return (
    <div className="space-y-4 rounded-md border border-border-default bg-surface-1 px-6 py-8 text-center">
      <Sparkles className="mx-auto size-8 text-accent-green" />
      <p className="text-sm text-text-primary">本組測驗完成！</p>
      <p className="text-2xl font-medium text-text-primary">
        {correct} / {total}
        <span className="ml-2 text-sm text-text-secondary">（{pct}%）</span>
      </p>
      <button
        type="button"
        onClick={onRestart}
        className="inline-flex h-9 items-center rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover"
      >
        再測一組
      </button>
    </div>
  );
}

export function WeaknessNoneView({ onRestart }: { onRestart: () => void }) {
  return (
    <div className="space-y-3 rounded-md border border-border-default bg-surface-1 px-6 py-8 text-center">
      <Target className="mx-auto size-8 text-text-muted/60" />
      <p className="text-sm text-text-primary">目前沒有偵測到明顯弱項</p>
      <p className="text-xs text-text-secondary">
        先到 LEARN 練習各單元題目，系統記錄掌握度後再回來測驗弱項。
      </p>
      <button
        type="button"
        onClick={onRestart}
        className="inline-flex h-8 items-center rounded-md border border-btn-default-border bg-btn-default-bg px-4 text-xs text-text-primary hover:bg-surface-2"
      >
        返回
      </button>
    </div>
  );
}
