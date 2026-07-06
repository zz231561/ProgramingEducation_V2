"use client";

/**
 * 觀念選擇題面板 — 直接作答、立即回饋，不進反思流程
 * （反思 gating 僅適用程式實作題；MC 重用 Quiz 頁 MCQuestion + submitAnswer）。
 */

import { useCallback, useState } from "react";
import { CheckCircle2, XCircle } from "lucide-react";

import { MCQuestion } from "@/components/quiz/mc-question";
import { ApiRequestError } from "@/lib/api";
import { Question, SubmitResponse, submitAnswer } from "@/lib/quiz";

import { QuestionHeader } from "./exercises-tab-views";

export function McPanel({
  question,
  onNext,
  onReset,
}: {
  question: Question;
  /** 再練一題（同題型重抽） */
  onNext: () => void;
  /** 回題型選擇 */
  onReset: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<SubmitResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(
    async (selectedIndex: number) => {
      setBusy(true);
      setError(null);
      try {
        setResult(
          await submitAnswer({
            question_id: question.id,
            answer: { selected_index: selectedIndex },
          }),
        );
      } catch (e) {
        setError(
          e instanceof ApiRequestError
            ? e.body.message || "提交失敗，請再試一次。"
            : "提交失敗，請再試一次。",
        );
      } finally {
        setBusy(false);
      }
    },
    [question.id],
  );

  return (
    <div className="space-y-3">
      <QuestionHeader question={question} onReset={onReset} />

      <div className="rounded-md border border-border-default bg-surface-1 p-4">
        {result === null ? (
          <MCQuestion question={question} busy={busy} onSubmit={handleSubmit} />
        ) : (
          <McResult result={result} onNext={onNext} onReset={onReset} />
        )}
      </div>

      {error && (
        <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
          {error}
        </div>
      )}
    </div>
  );
}

function McResult({
  result,
  onNext,
  onReset,
}: {
  result: SubmitResponse;
  onNext: () => void;
  onReset: () => void;
}) {
  return (
    <div className="space-y-3">
      <div
        className={`flex items-center gap-2 text-sm ${
          result.is_correct ? "text-accent-green" : "text-accent-red"
        }`}
      >
        {result.is_correct ? (
          <CheckCircle2 className="size-4" />
        ) : (
          <XCircle className="size-4" />
        )}
        <span>{result.is_correct ? "答對了！" : "答錯了"}</span>
      </div>
      {result.feedback && (
        <p className="text-sm leading-relaxed text-text-secondary">{result.feedback}</p>
      )}
      {result.explanation && (
        <p className="rounded-md border-l-2 border-accent-blue bg-surface-2 px-3 py-2 text-xs leading-relaxed text-text-secondary">
          {result.explanation}
        </p>
      )}
      <div className="flex gap-2 pt-1">
        <button
          type="button"
          onClick={onNext}
          className="inline-flex h-8 items-center rounded-md bg-btn-primary-bg px-3 text-xs font-medium text-white hover:bg-btn-primary-hover"
        >
          再練一題
        </button>
        <button
          type="button"
          onClick={onReset}
          className="inline-flex h-8 items-center rounded-md border border-btn-default-border bg-btn-default-bg px-3 text-xs text-text-primary hover:bg-surface-2"
        >
          選其他題型
        </button>
      </div>
    </div>
  );
}
