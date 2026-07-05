"use client";

/**
 * QuizRunner 靜態子視圖（K3e 自 quiz-runner.tsx 拆出控制檔案大小）。
 *
 * 無狀態 presentational 元件 + 錯誤訊息轉換；流程邏輯留在 quiz-runner.tsx。
 */

import { FileQuestion, Loader2, Play } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { Question, QuestionType } from "@/lib/quiz";

export const TYPE_LABELS: Record<QuestionType, string> = {
  multiple_choice: "選擇題",
  coding: "程式撰寫題",
  fill_blank: "填空題",
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
    <div className="mx-auto max-w-md space-y-4 text-center">
      <FileQuestion className="mx-auto size-10 text-text-muted/60" />
      <h1 className="text-xl font-medium text-text-primary">Quiz 測驗</h1>
      <p className="text-sm leading-6 text-text-secondary">
        AI 依你目前的弱項自動出題；提交後立即顯示對錯與解析。
      </p>

      <div className="space-y-2 text-left">
        <label className="block text-xs text-text-secondary">題型</label>
        <div className="flex gap-2">
          {(["multiple_choice", "coding"] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => onTypeChange(t)}
              className={`flex-1 rounded-md border px-3 py-2 text-sm transition-colors ${
                type === t
                  ? "border-border-emphasis bg-surface-2 text-text-primary"
                  : "border-border-default bg-surface-1 text-text-secondary hover:border-border-emphasis hover:text-text-primary"
              }`}
            >
              {TYPE_LABELS[t]}
            </button>
          ))}
        </div>
      </div>

      <button
        type="button"
        onClick={onStart}
        className="inline-flex h-9 items-center gap-2 rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover"
      >
        <Play className="size-4" />
        開始 Quiz
      </button>
      {error && (
        <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-left text-xs text-accent-red">
          {error}
        </div>
      )}
    </div>
  );
}

export function LoadingView() {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-text-secondary">
      <Loader2 className="size-6 animate-spin" />
      <p className="text-sm">AI 正在生成題目（含自我審查 retry）...</p>
      <p className="text-xs text-text-muted">通常 5–15 秒</p>
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
