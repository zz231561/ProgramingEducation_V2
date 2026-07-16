"use client";

/**
 * 程式實作題 tab（6-3c）— 取單元預生成 coding 題（source='batch'），
 * 讀題 → 反思 gating → Workspace 作答。LEARN 完全不呼叫 LLM。
 *
 * 觀念題 tab 見 concept-quiz-tab.tsx（整組逐題）；QUIZ 弱項現生題不列入。
 */

import { useCallback, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { ReflectionFlow } from "@/components/reflection/reflection-flow";
import { ApiRequestError } from "@/lib/api";
import { Question, getUnitQuestionSet } from "@/lib/quiz";
import { Reflection } from "@/lib/reflection";

import { CodingPanel, CodingPhase } from "./exercises-coding-panel";

interface Props {
  conceptTag: string;
  /** 單元標題 — Workspace 檔案自動命名用 */
  unitTitle: string;
}

type Phase = "loading" | "empty" | "error" | "question" | "reflecting" | "done";

export function ExercisesTab({ conceptTag, unitTitle }: Props) {
  const [phase, setPhase] = useState<Phase>("loading");
  const [question, setQuestion] = useState<Question | null>(null);
  const [reflection, setReflection] = useState<Reflection | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const set = await getUnitQuestionSet(conceptTag, "coding");
        if (cancelled) return;
        if (set.total === 0) {
          setPhase("empty");
          return;
        }
        setQuestion(set.items[0].question);
        setPhase("question");
      } catch (e) {
        if (cancelled) return;
        setPhase("error");
        setError(
          e instanceof ApiRequestError
            ? e.body.message || "載入題目失敗。"
            : "載入題目失敗。",
        );
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [conceptTag]);

  const handleApproveReflection = useCallback((r: Reflection) => {
    setReflection(r);
    setPhase("done");
  }, []);

  const closeReflectionModal = useCallback(() => {
    setPhase((p) => (p === "reflecting" ? "question" : p));
  }, []);

  const stem = (question?.content as { stem?: string } | undefined)?.stem ?? null;

  if (phase === "loading") {
    return (
      <div className="flex flex-col items-center gap-3 py-12 text-text-secondary">
        <Loader2 className="size-6 animate-spin" />
        <p className="text-sm">載入題目...</p>
      </div>
    );
  }

  if (phase === "empty") {
    return (
      <p className="rounded-md border border-border-default bg-surface-1 px-4 py-8 text-center text-sm text-text-secondary">
        本單元尚無程式實作題。
      </p>
    );
  }

  if (phase === "error") {
    return (
      <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {question && (
        <CodingPanel
          question={question}
          unitTitle={unitTitle}
          phase={phase as CodingPhase}
          reflection={reflection}
          onStartReflect={() => setPhase("reflecting")}
        />
      )}
      <ReflectionFlow
        open={phase === "reflecting"}
        sourceType="quiz"
        sourceId={question?.id ?? null}
        questionStem={stem}
        onApprove={handleApproveReflection}
        onClose={closeReflectionModal}
      />
    </div>
  );
}
