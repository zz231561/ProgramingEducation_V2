"use client";

/**
 * ExercisesTab 子展示元件（idle + loading + 共用題目 header）
 * — 拆出以維持 exercises-tab.tsx ≤ 250 行。純展示無 state。
 *
 * IdleView 題型分類（2026-07-06）：程式實作題走反思 gating、
 * 觀念選擇題直接作答；卡片樣式遵循 R8.5（active 用 border 不用色塊）。
 */

import { Code2, ListChecks, Loader2 } from "lucide-react";

import { Question } from "@/lib/quiz";

export type ExerciseCategory = "coding" | "multiple_choice";

const CATEGORY_CARDS: {
  category: ExerciseCategory;
  title: string;
  description: string;
  Icon: typeof Code2;
}[] = [
  {
    category: "coding",
    title: "程式實作題",
    description: "先寫下解題思路（反思），再到 Workspace 撰寫程式",
    Icon: Code2,
  },
  {
    category: "multiple_choice",
    title: "觀念選擇題",
    description: "快速檢驗概念理解，作答後立即看回饋",
    Icon: ListChecks,
  },
];

export function IdleView({
  conceptNameZh,
  onStart,
  error,
}: {
  conceptNameZh: string;
  onStart: (category: ExerciseCategory) => void;
  error: string | null;
}) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 px-6 py-8">
      <p className="text-center text-sm text-text-primary">
        針對「{conceptNameZh}」練習一題，選擇題型：
      </p>
      <div className="mx-auto mt-5 grid max-w-md gap-3 sm:grid-cols-2">
        {CATEGORY_CARDS.map(({ category, title, description, Icon }) => (
          <button
            key={category}
            type="button"
            onClick={() => onStart(category)}
            className="rounded-md border border-border-default bg-surface-2 p-4 text-left transition-colors hover:border-border-emphasis"
          >
            <Icon className="size-5 text-text-secondary" />
            <p className="mt-2 text-sm font-medium text-text-primary">{title}</p>
            <p className="mt-1 text-xs leading-relaxed text-text-secondary">
              {description}
            </p>
          </button>
        ))}
      </div>
      <p className="mt-4 text-center text-xs text-text-muted">
        優先從題庫取題（&lt; 1 秒）；題庫無題時由 AI 現場生成
      </p>
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
