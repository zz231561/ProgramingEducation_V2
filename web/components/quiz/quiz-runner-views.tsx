"use client";

/**
 * QuizRunner 靜態子視圖（K3e 自 quiz-runner.tsx 拆出控制檔案大小）。
 *
 * 無狀態 presentational 元件 + 錯誤訊息轉換；流程邏輯留在 quiz-runner.tsx。
 */

import { Code2, ListChecks, Loader2, Play, Target } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { Question, QuestionType } from "@/lib/quiz";

export const TYPE_LABELS: Record<QuestionType, string> = {
  multiple_choice: "選擇題",
  coding: "程式撰寫題",
  fill_blank: "填空題",
};

/** U2a：題型選擇卡的圖示與一句話說明。 */
const TYPE_META: Record<
  "multiple_choice" | "coding",
  { icon: typeof ListChecks; hint: string }
> = {
  multiple_choice: { icon: ListChecks, hint: "觀念判斷，快速檢驗理解" },
  coding: { icon: Code2, hint: "實際撰寫 C++，深度練習" },
};

export function IdleView({
  type,
  onTypeChange,
  onStart,
  error,
}: {
  type: QuestionType;
  onTypeChange: (t: QuestionType) => void;
  onStart: () => void;
  error: string | null;
}) {
  return (
    <div className="mx-auto max-w-md space-y-6">
      <div className="space-y-2 text-center">
        <span className="inline-flex size-11 items-center justify-center rounded-md border border-border-default bg-surface-1">
          <Target className="size-5 text-text-secondary" />
        </span>
        <h1 className="text-xl font-medium text-text-primary">Quiz 測驗</h1>
        <p className="text-sm leading-6 text-text-secondary">
          系統依你目前的弱項概念出題，作答後立即顯示解析，
          <br />
          連續失誤時自動診斷根源弱點。
        </p>
      </div>

      <div className="space-y-2">
        <span className="block text-xs font-medium uppercase tracking-wide text-text-muted">
          題型
        </span>
        <div className="grid grid-cols-2 gap-2">
          {(["multiple_choice", "coding"] as const).map((t) => {
            const { icon: Icon, hint } = TYPE_META[t];
            const active = type === t;
            return (
              <button
                key={t}
                type="button"
                onClick={() => onTypeChange(t)}
                aria-pressed={active}
                className={`rounded-md border p-3 text-left transition-colors ${
                  active
                    ? "border-border-emphasis bg-surface-2"
                    : "border-border-default bg-surface-1 hover:border-border-emphasis"
                }`}
              >
                <span className="flex items-center gap-2">
                  <Icon
                    className={`size-4 ${active ? "text-text-primary" : "text-text-muted"}`}
                  />
                  <span
                    className={`text-sm font-medium ${
                      active ? "text-text-primary" : "text-text-secondary"
                    }`}
                  >
                    {TYPE_LABELS[t]}
                  </span>
                </span>
                <span className="mt-1 block text-xs leading-5 text-text-muted">
                  {hint}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex flex-col items-center gap-2">
        <button
          type="button"
          onClick={onStart}
          className="inline-flex h-9 w-full max-w-60 items-center justify-center gap-2 rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover"
        >
          <Play className="size-4" />
          開始 Quiz
        </button>
      </div>

      {error && (
        <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
          {error}
        </div>
      )}
    </div>
  );
}

export function LoadingView({ source }: { source: "bank" | "generate" }) {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-text-secondary">
      <Loader2 className="size-6 animate-spin" />
      {source === "bank" ? (
        <p className="text-sm">正在從題庫挑題...</p>
      ) : (
        <>
          <p className="text-sm">題庫無可用題目，AI 正在生成新題（含自我審查）...</p>
          <p className="text-xs text-text-muted">通常 5–15 秒</p>
        </>
      )}
    </div>
  );
}

export function QuestionMeta({ question }: { question: Question }) {
  return (
    <div className="flex items-center gap-2 text-xs text-text-muted">
      <span className="rounded-pill border border-border-default px-1.5">
        {TYPE_LABELS[question.type]}
      </span>
      <span className="rounded-pill border border-border-default px-1.5">
        難度 {question.difficulty}
      </span>
      <span className="rounded-pill border border-border-default px-1.5">
        Bloom L{question.bloom_level}
      </span>
      {question.concept_tags.map((tag) => (
        <span key={tag} className="font-mono">
          {tag}
        </span>
      ))}
    </div>
  );
}

export function UnsupportedTypeNote({ type }: { type: string }) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 px-4 py-6 text-center text-sm text-text-secondary">
      題型「{type}」UI 尚未實作（3-2a 範圍：選擇題 + 程式撰寫題）。
    </div>
  );
}

export function humanizeError(e: unknown): string {
  if (e instanceof ApiRequestError) {
    if (e.status === 503 && e.body.error === "QUIZ_VALIDATION_RETRY_EXHAUSTED") {
      return "AI 連續審查未通過，請再試一次。";
    }
    if (e.status === 503 && e.body.error === "QUIZ_UNAVAILABLE") {
      return "題庫尚未初始化（請聯絡管理員）。";
    }
    if (e.status === 404) {
      return e.body.message || "找不到題目（可能已被移除）。";
    }
    if (e.status === 400 && e.body.error === "QUESTION_NOT_VALIDATED") {
      return "此題尚未通過 AI 審查，無法作答。";
    }
    if (e.status === 401) return "請先登入。";
    return e.body.message || "操作失敗。";
  }
  return e instanceof Error ? e.message : "未知錯誤";
}
