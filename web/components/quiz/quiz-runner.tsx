"use client";

/**
 * Quiz 主流程 runner（roadmap 3-2a）。
 *
 * 三狀態：idle（題型選擇）→ question（作答）→ result（看結果）
 * K3e：result 答錯時 ResultView 內顯示診斷嫌疑鏈，微測驗直接切入指定題目。
 * 靜態子視圖 / 錯誤訊息轉換 → `quiz-runner-views.tsx`
 *
 * 設計分工：
 * - Quiz 頁面 = 純測驗（取題 → 作答 → 結果），無反思
 * - Learn 練習 tab = 學習場景含反思（已於 3-1e 整合）
 */

import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ApiRequestError } from "@/lib/api";
import {
  HintResponse,
  Question,
  QuestionType,
  SubmitAnswer,
  SubmitResponse,
  generateQuestion,
  getQuestionById,
  getQuestionFromBank,
  requestHint,
  submitAnswer,
} from "@/lib/quiz";

import { CodingQuestion } from "./coding-question";
import { HintPanel } from "./hint-panel";
import { MCQuestion } from "./mc-question";
import {
  IdleView,
  LoadingView,
  QuestionMeta,
  UnsupportedTypeNote,
  humanizeError,
} from "./quiz-runner-views";
import { ResultView } from "./result-view";
import { Timer } from "./timer";

type Phase =
  | { mode: "idle" }
  | { mode: "loading"; source: "bank" | "generate" }
  | { mode: "question"; question: Question; startedAt: number }
  | { mode: "submitting"; question: Question }
  | { mode: "result"; question: Question; result: SubmitResponse };

export function QuizRunner() {
  const [phase, setPhase] = useState<Phase>({ mode: "idle" });
  const [type, setType] = useState<QuestionType>("multiple_choice");
  const [error, setError] = useState<string | null>(null);
  // 3-2b：累計提示（每換題清空）+ hint LLM 載入旗標
  const [hints, setHints] = useState<HintResponse[]>([]);
  const [hintBusy, setHintBusy] = useState(false);

  // U2d 題庫優先：先抽題庫（弱項模式 + 排除已答過，< 1s），
  // 題庫無可用題才 fallback LLM 現生（5-15s；新題 validated 後入庫）
  const fetchQuestion = useCallback(async () => {
    setError(null);
    setHints([]);
    setPhase({ mode: "loading", source: "bank" });
    try {
      const q = await getQuestionFromBank(undefined, type);
      setPhase({ mode: "question", question: q, startedAt: Date.now() });
      return;
    } catch (e) {
      const bankEmpty =
        e instanceof ApiRequestError &&
        e.status === 404 &&
        e.body.error === "QUESTION_BANK_EMPTY";
      if (!bankEmpty) {
        setPhase({ mode: "idle" });
        setError(humanizeError(e));
        return;
      }
    }

    setPhase({ mode: "loading", source: "generate" });
    try {
      const q = await generateQuestion({ type, bloom_level: 3 });
      setPhase({ mode: "question", question: q, startedAt: Date.now() });
    } catch (e) {
      setPhase({ mode: "idle" });
      setError(humanizeError(e));
    }
  }, [type]);

  // K3e 微測驗：診斷嫌疑鏈已取得完整題目 → 直接進入作答
  const startQuestion = useCallback((question: Question) => {
    setError(null);
    setHints([]);
    setPhase({ mode: "question", question, startedAt: Date.now() });
  }, []);

  // DEV-9 深連結：/quiz?question=<id> 直接載入指定題（題庫抽查用）
  const deepLinkQuestionId = useSearchParams().get("question");
  useEffect(() => {
    if (!deepLinkQuestionId) return;
    let cancelled = false;
    setPhase({ mode: "loading", source: "bank" });
    getQuestionById(deepLinkQuestionId).then(
      (q) => {
        if (!cancelled) startQuestion(q);
      },
      () => {
        if (cancelled) return;
        setPhase({ mode: "idle" });
        setError("找不到指定題目");
      },
    );
    return () => {
      cancelled = true;
    };
  }, [deepLinkQuestionId, startQuestion]);

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
          hint_level_used: hints.length,
        });
        setPhase({ mode: "result", question, result });
      } catch (e) {
        setPhase({ mode: "question", question, startedAt });
        setError(humanizeError(e));
      }
    },
    [phase, hints.length],
  );

  const handleRequestHint = useCallback(async () => {
    if (phase.mode !== "question" || hintBusy || hints.length >= 5) return;
    setHintBusy(true);
    setError(null);
    try {
      const next = await requestHint({
        question_id: phase.question.id,
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
    return <LoadingView source={phase.source} />;
  }

  if (phase.mode === "result") {
    return (
      <ResultView
        question={phase.question}
        result={phase.result}
        onNext={fetchQuestion}
        onExit={reset}
        onStartQuestion={startQuestion}
      />
    );
  }

  // question / submitting
  const busy = phase.mode === "submitting";
  // submitting 時找不到 startedAt（phase 沒帶），用 question 模式的 timer 即可，這裡 fallback 0 不顯示
  const startedAt = phase.mode === "question" ? phase.startedAt : null;
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <QuestionMeta question={phase.question} />
        {startedAt !== null && <Timer startedAt={startedAt} />}
      </div>
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
      <HintPanel
        hints={hints}
        busy={hintBusy}
        onRequestNext={handleRequestHint}
      />
      {error && (
        <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
          {error}
        </div>
      )}
    </div>
  );
}
