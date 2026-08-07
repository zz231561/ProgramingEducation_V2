"use client";

/**
 * 解題後的理解驗證 Modal。
 *
 * 答對後彈出，依後端建議的 type 顯示 EPL / 預測輸出 / 變體挑戰。
 * 全程可關閉——驗證是加分項不是關卡，卡住學生比沒驗更糟。
 *
 * 註：規格線框寫的是 emoji 標題，此處改用 lucide icon（frontend.md R8.2 禁 emoji）。
 */

import { useEffect } from "react";
import { Brain, CheckCircle2, X, XCircle } from "lucide-react";

import { EplStep } from "./epl-step";
import { PredictStep } from "./predict-step";
import { VariationStep } from "./variation-step";
import { useComprehension } from "./use-comprehension";

const TITLE: Record<string, string> = {
  epl: "理解驗證 — 說說你的解法",
  predict_output: "理解驗證 — 預測輸出",
  variation: "理解驗證 — 變體挑戰",
};

export function ComprehensionModal({
  answerId,
  onClose,
}: {
  answerId: string;
  onClose: () => void;
}) {
  const { phase, answer, setAnswer, submit, error } = useComprehension(answerId);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  // 後端判定不需要驗、或出題失敗 → 完全不出現
  if (phase.k === "skip") return null;

  const type = phase.k === "loading" ? phase.type
    : phase.k === "checking" ? null
    : phase.data.type;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg-inset/80 p-4">
      <div
        role="dialog"
        aria-modal="true"
        className="max-h-[85vh] w-full max-w-xl overflow-y-auto rounded-lg border border-border-default bg-bg-default shadow-modal"
      >
        <div className="flex items-center justify-between border-b border-border-default px-4 py-3">
          <div className="flex items-center gap-2">
            <Brain className="size-4 text-text-secondary" />
            <span className="text-sm font-medium text-text-primary">
              {(type && TITLE[type]) || "理解驗證"}
            </span>
          </div>
          <button
            onClick={onClose}
            className="flex size-7 items-center justify-center rounded-md text-text-muted transition-colors hover:bg-bg-subtle hover:text-text-secondary"
            title="關閉（Esc）"
          >
            <X className="size-3.5" />
          </button>
        </div>

        <div className="space-y-4 px-4 py-4">
          {(phase.k === "checking" || phase.k === "loading") && (
            <p className="text-sm text-text-muted">正在準備題目…</p>
          )}

          {(phase.k === "answering" || phase.k === "grading" || phase.k === "done") && (
            <StepBody
              phase={phase}
              answer={answer}
              setAnswer={setAnswer}
              submit={submit}
            />
          )}

          {error && <p className="text-sm text-accent-red">{error}</p>}

          {phase.k === "done" && (
            <>
              <Verdict passed={phase.passed} feedback={phase.feedback} />
              <div className="flex justify-end">
                <button
                  onClick={onClose}
                  className="h-8 rounded-md border border-border-default bg-btn-default-bg px-4 text-sm text-text-secondary transition-colors hover:bg-bg-subtle hover:text-text-primary"
                >
                  完成
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function StepBody({
  phase, answer, setAnswer, submit,
}: {
  phase: Extract<ReturnType<typeof useComprehension>["phase"], { data: unknown }>;
  answer: string;
  setAnswer: (v: string) => void;
  submit: () => void;
}) {
  const busy = phase.k === "grading";
  const done = phase.k === "done" ? phase : null;

  if (phase.data.type === "epl") {
    return (
      <EplStep
        prompt={phase.data.prompt}
        answer={answer}
        onAnswerChange={setAnswer}
        onSubmit={submit}
        busy={busy}
        grade={done?.epl ?? null}
      />
    );
  }
  if (phase.data.type === "predict_output") {
    return (
      <PredictStep
        testInput={phase.data.testInput}
        answer={answer}
        onAnswerChange={setAnswer}
        onSubmit={submit}
        busy={busy}
        grade={done?.predict ?? null}
      />
    );
  }
  return (
    <VariationStep
      challenge={phase.data.challenge}
      code={answer}
      onCodeChange={setAnswer}
      onSubmit={submit}
      busy={busy}
      passed={done ? done.passed : null}
    />
  );
}

function Verdict({
  passed,
  feedback,
}: {
  passed: boolean | null;
  feedback: string | null;
}) {
  return (
    <div className="space-y-2 border-t border-border-muted pt-3">
      <div className="flex items-center gap-2 text-sm">
        {passed ? (
          <CheckCircle2 className="size-4 text-accent-green" />
        ) : (
          <XCircle className="size-4 text-accent-orange" />
        )}
        <span className="text-text-primary">
          {passed ? "理解驗證通過" : "還有一點沒對上"}
        </span>
      </div>
      {feedback && (
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-text-secondary">
          {feedback}
        </p>
      )}
    </div>
  );
}
