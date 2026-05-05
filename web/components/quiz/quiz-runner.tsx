"use client";

/**
 * Quiz 主流程 runner（roadmap 3-2a）。
 *
 * 三狀態：idle（題型選擇）→ question（作答）→ result（看結果）
 * 計時器 / 提示系統 / 完整 EDF 回饋屬 3-2b/c。
 *
 * 設計分工：
 * - Quiz 頁面 = 純測驗（取題 → 作答 → 結果），無反思
 * - Learn 練習 tab = 學習場景含反思（已於 3-1e 整合）
 */

import { useCallback, useState } from "react";
import { FileQuestion, Loader2, Play } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import {
  Question,
  QuestionType,
  SubmitAnswer,
  SubmitResponse,
  generateQuestion,
  submitAnswer,
} from "@/lib/quiz";

import { CodingQuestion } from "./coding-question";
import { MCQuestion } from "./mc-question";
import { ResultView } from "./result-view";

type Phase =
  | { mode: "idle" }
  | { mode: "loading" }
  | { mode: "question"; question: Question; startedAt: number }
  | { mode: "submitting"; question: Question }
  | { mode: "result"; question: Question; result: SubmitResponse };

const TYPE_LABELS: Record<QuestionType, string> = {
  multiple_choice: "選擇題",
  coding: "程式撰寫題",
  fill_blank: "填空題",
};

export function QuizRunner() {
  const [phase, setPhase] = useState<Phase>({ mode: "idle" });
  const [type, setType] = useState<QuestionType>("multiple_choice");
  const [error, setError] = useState<string | null>(null);

  const fetchQuestion = useCallback(async () => {
    setError(null);
    setPhase({ mode: "loading" });
    try {
      const q = await generateQuestion({ type, bloom_level: 3 });
      setPhase({ mode: "question", question: q, startedAt: Date.now() });
    } catch (e) {
      setPhase({ mode: "idle" });
      setError(humanizeError(e));
    }
  }, [type]);

  const handleSubmit = useCallback(
    async (answer: SubmitAnswer) => {
      if (phase.mode !== "question") return;
      const { question, startedAt } = phase;
      setPhase({ mode: "submitting", question });
      try {
        const result = await submitAnswer({
          question_id: question.id,
          answer,
          time_spent_seconds: Math.max(0, Math.round((Date.now() - startedAt) / 1000)),
          hint_level_used: 0,
        });
        setPhase({ mode: "result", question, result });
      } catch (e) {
        setPhase({ mode: "question", question, startedAt });
        setError(humanizeError(e));
      }
    },
    [phase],
  );

  const reset = useCallback(() => {
    setPhase({ mode: "idle" });
    setError(null);
  }, []);

  if (phase.mode === "idle") {
    return (
      <IdleView
        type={type}
        onTypeChange={setType}
        onStart={fetchQuestion}
        error={error}
      />
    );
  }

  if (phase.mode === "loading") {
    return <LoadingView />;
  }

  if (phase.mode === "result") {
    return (
      <ResultView
        question={phase.question}
        result={phase.result}
        onNext={fetchQuestion}
        onExit={reset}
      />
    );
  }

  // question / submitting
  const busy = phase.mode === "submitting";
  return (
    <div className="space-y-4">
      <QuestionMeta question={phase.question} />
      {phase.question.type === "multiple_choice" ? (
        <MCQuestion
          question={phase.question}
          busy={busy}
          onSubmit={(idx) => handleSubmit({ selected_index: idx })}
        />
      ) : phase.question.type === "coding" ? (
        <CodingQuestion
          question={phase.question}
          busy={busy}
          onSubmit={(code) => handleSubmit({ code })}
        />
      ) : (
        <UnsupportedTypeNote type={phase.question.type} />
      )}
      {error && (
        <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
          {error}
        </div>
      )}
    </div>
  );
}

function IdleView({
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

function LoadingView() {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-text-secondary">
      <Loader2 className="size-6 animate-spin" />
      <p className="text-sm">AI 正在生成題目（含自我審查 retry）...</p>
      <p className="text-xs text-text-muted">通常 5–15 秒</p>
    </div>
  );
}

function QuestionMeta({ question }: { question: Question }) {
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

function UnsupportedTypeNote({ type }: { type: string }) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 px-4 py-6 text-center text-sm text-text-secondary">
      題型「{type}」UI 尚未實作（3-2a 範圍：選擇題 + 程式撰寫題）。
    </div>
  );
}

function humanizeError(e: unknown): string {
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
