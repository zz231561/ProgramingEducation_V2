"use client";

/**
 * 弱項綜合測驗組 runner（6-3d）— QUIZ 主流程。
 *
 * idle（選 10/25）→ generating（一次生成整組）→ answering（逐題作答）→ summary。
 * 每題重用 MCQuestion / CodingQuestion / HintPanel / ResultView。
 * 無弱項 → none 視圖，提示先去 LEARN 練習。
 */

import { useCallback, useState } from "react";

import {
  HintResponse,
  Question,
  SubmitAnswer,
  SubmitResponse,
  getWeaknessSet,
  requestHint,
  submitAnswer,
} from "@/lib/quiz";

import { CodingQuestion } from "./coding-question";
import { HintPanel } from "./hint-panel";
import { MCQuestion } from "./mc-question";
import { QuestionMeta, humanizeError } from "./quiz-runner-views";
import { ResultView } from "./result-view";
import {
  WeaknessGeneratingView,
  WeaknessIdleView,
  WeaknessNoneView,
  WeaknessSummaryView,
} from "./weakness-quiz-views";

type Phase =
  | { mode: "idle" }
  | { mode: "generating"; count: 10 | 25 }
  | {
      mode: "answering";
      questions: Question[];
      index: number;
      result: SubmitResponse | null;
      correct: number;
    }
  | { mode: "summary"; total: number; correct: number }
  | { mode: "none" };

export function WeaknessQuizRunner() {
  const [phase, setPhase] = useState<Phase>({ mode: "idle" });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [hints, setHints] = useState<HintResponse[]>([]);
  const [hintBusy, setHintBusy] = useState(false);

  const start = useCallback(async (count: 10 | 25) => {
    setError(null);
    setHints([]);
    setPhase({ mode: "generating", count });
    try {
      const set = await getWeaknessSet(count);
      if (set.no_weakness || set.questions.length === 0) {
        setPhase({ mode: "none" });
        return;
      }
      setPhase({
        mode: "answering",
        questions: set.questions,
        index: 0,
        result: null,
        correct: 0,
      });
    } catch (e) {
      setPhase({ mode: "idle" });
      setError(humanizeError(e));
    }
  }, []);

  const handleSubmit = useCallback(
    async (answer: SubmitAnswer) => {
      if (phase.mode !== "answering") return;
      const question = phase.questions[phase.index];
      setBusy(true);
      setError(null);
      try {
        const result = await submitAnswer({ question_id: question.id, answer, hint_level_used: hints.length });
        setPhase({ ...phase, result, correct: phase.correct + (result.is_correct ? 1 : 0) });
      } catch (e) {
        setError(humanizeError(e));
      } finally {
        setBusy(false);
      }
    },
    [phase, hints.length],
  );

  const handleNext = useCallback(() => {
    if (phase.mode !== "answering") return;
    setHints([]);
    if (phase.index + 1 >= phase.questions.length) {
      setPhase({ mode: "summary", total: phase.questions.length, correct: phase.correct });
      return;
    }
    setPhase({ ...phase, index: phase.index + 1, result: null });
  }, [phase]);

  const handleRequestHint = useCallback(async () => {
    if (phase.mode !== "answering" || hintBusy || hints.length >= 5) return;
    setHintBusy(true);
    try {
      const next = await requestHint({
        question_id: phase.questions[phase.index].id,
        hint_level: hints.length + 1,
      });
      setHints((prev) => [...prev, next]);
    } catch (e) {
      setError(humanizeError(e));
    } finally {
      setHintBusy(false);
    }
  }, [phase, hints.length, hintBusy]);

  const reset = useCallback(() => {
    setPhase({ mode: "idle" });
    setHints([]);
    setError(null);
  }, []);

  if (phase.mode === "idle") return <WeaknessIdleView onStart={start} error={error} />;
  if (phase.mode === "generating") return <WeaknessGeneratingView count={phase.count} />;
  if (phase.mode === "none") return <WeaknessNoneView onRestart={reset} />;
  if (phase.mode === "summary") {
    return <WeaknessSummaryView total={phase.total} correct={phase.correct} onRestart={reset} />;
  }

  const question = phase.questions[phase.index];
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <QuestionMeta question={question} />
        <span className="text-xs text-text-muted">
          第 {phase.index + 1} / {phase.questions.length} 題
        </span>
      </div>

      {phase.result === null ? (
        <>
          {question.type === "multiple_choice" ? (
            <MCQuestion
              question={question}
              busy={busy}
              onSubmit={(idx) => handleSubmit({ selected_index: idx })}
            />
          ) : (
            <CodingQuestion
              question={question}
              busy={busy}
              onSubmit={(code) => handleSubmit({ code })}
            />
          )}
          <HintPanel hints={hints} busy={hintBusy} onRequestNext={handleRequestHint} />
        </>
      ) : (
        <ResultView
          question={question}
          result={phase.result}
          onNext={handleNext}
          onExit={reset}
        />
      )}

      {error && (
        <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
          {error}
        </div>
      )}
    </div>
  );
}
