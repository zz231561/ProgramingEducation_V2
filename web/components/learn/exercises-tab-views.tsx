"use client";

/**
 * ExercisesTab 子展示元件（idle + loading + 共用題目 header）
 * — 拆出以維持 exercises-tab.tsx ≤ 250 行。純展示無 state。
 *
 * U2g：題型改由 unit-content tab 決定（程式實作題 / 觀念題各一個 tab），
 * IdleView 依 category 顯示對應說明與開始按鈕。
 */

import { Code2, ListChecks, Loader2 } from "lucide-react";

import { Question } from "@/lib/quiz";

export type ExerciseCategory = "coding" | "multiple_choice";

const CATEGORY_COPY: Record<
  ExerciseCategory,
  { description: string; Icon: typeof Code2 }
> = {
  coding: {
    description: "先寫下解題思路（反思），再到 Workspace 撰寫程式",
    Icon: Code2,
  },
  multiple_choice: {
    description: "快速檢驗概念理解，作答後立即看回饋",
    Icon: ListChecks,
  },
};

export function IdleView({
  category,
  conceptNameZh,
  onStart,
  error,
}: {
  category: ExerciseCategory;
  conceptNameZh: string;
  onStart: () => void;
  error: string | null;
}) {
  const { description, Icon } = CATEGORY_COPY[category];
  return (
    <div className="rounded-md border border-border-default bg-surface-1 px-6 py-8 text-center">
      <Icon className="mx-auto size-8 text-text-muted/60" />
      <p className="mt-3 text-sm text-text-primary">
        針對「{conceptNameZh}」練習一題
      </p>
      <p className="mt-1 text-xs text-text-secondary">{description}</p>
      <button
        type="button"
        onClick={onStart}
        className="mt-5 inline-flex h-9 items-center gap-2 rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover"
      >
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

/** 題目上方共用列：難度 / Bloom 徽章 + 重新出題。 */
export function QuestionHeader({
  question,
  onReset,
}: {
  question: Question;
  onReset: () => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2 text-xs text-text-muted">
        <span className="rounded-pill border border-border-default px-1.5">
          難度 {question.difficulty}
        </span>
        <span className="rounded-pill border border-border-default px-1.5">
          Bloom L{question.bloom_level}
        </span>
      </div>
      <button
        type="button"
        onClick={onReset}
        className="text-xs text-text-secondary hover:text-text-primary"
      >
        重新出題
      </button>
    </div>
  );
}
