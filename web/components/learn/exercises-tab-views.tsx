"use client";

/**
 * ExercisesTab 子展示元件（idle + loading）— 拆出以維持 exercises-tab.tsx ≤ 250 行。
 * 純展示無 state，便於獨立調整文案 / loading 動畫不影響主流程。
 */

import { Loader2, Play, Sparkles } from "lucide-react";

export function IdleView({
  conceptNameZh,
  onStart,
  error,
}: {
  conceptNameZh: string;
  onStart: () => void;
  error: string | null;
}) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 px-6 py-8 text-center">
      <Sparkles className="mx-auto size-8 text-text-muted/60" />
      <p className="mt-3 text-sm text-text-primary">
        針對「{conceptNameZh}」練習一題
      </p>
      <p className="mt-1 text-xs text-text-secondary">
        系統會生成程式撰寫題；你會先讀題、寫下解題思路（反思），再進入作答
      </p>
      <button
        type="button"
        onClick={onStart}
        className="mt-5 inline-flex h-9 items-center gap-2 rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover"
      >
        <Play className="size-4" />
        開始練習
      </button>
      {error && (
        <div className="mt-4 rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-left text-xs text-accent-red">
          {error}
        </div>
      )}
    </div>
  );
}

export function LoadingView({ source }: { source: "bank" | "generate" }) {
  const isBank = source === "bank";
  return (
    <div className="flex flex-col items-center gap-3 py-12 text-text-secondary">
      <Loader2 className="size-6 animate-spin" />
      <p className="text-sm">
        {isBank ? "查找題庫題目..." : "AI 正在生成題目（含自我審查 retry）..."}
      </p>
      <p className="text-xs text-text-muted">
        {isBank ? "通常 < 1 秒" : "通常 5–15 秒"}
      </p>
    </div>
  );
}
