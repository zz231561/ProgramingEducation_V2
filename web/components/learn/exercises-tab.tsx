"use client";

/**
 * 練習題 tab — 6-3b 題庫優先：先 /quiz/from-bank（< 1s）→ 404 QUESTION_BANK_EMPTY
 * 時 fallback /quiz/generate（LLM 5-15s）。Loading 文案分兩階段提示使用者為何等待。
 *
 * U2g（2026-07-06 晚間）：題型由 caller（unit-content tab）指定——
 * - category="coding"（程式實作題 tab）→ 讀題 → 反思 gating → Workspace 作答
 * - category="multiple_choice"（觀念題 tab）→ 直接作答 + 立即回饋，不進反思
 */

import { useCallback, useState } from "react";

import { ReflectionFlow } from "@/components/reflection/reflection-flow";
import { ApiRequestError } from "@/lib/api";
import { Question, generateQuestion, getQuestionFromBank } from "@/lib/quiz";
import { Reflection } from "@/lib/reflection";

import { CodingPanel, CodingPhase } from "./exercises-coding-panel";
import { McPanel } from "./exercises-mc-panel";
import { ExerciseCategory, IdleView, LoadingView } from "./exercises-tab-views";

interface Props {
  category: ExerciseCategory;
  conceptTag: string;
  conceptNameZh: string;
}

type Phase = "idle" | "loading-bank" | "loading-generate" | "question" | "reflecting" | "done";

export function ExercisesTab({ category, conceptTag, conceptNameZh }: Props) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [question, setQuestion] = useState<Question | null>(null);
  const [reflection, setReflection] = useState<Reflection | null>(null);
  const [error, setError] = useState<string | null>(null);

  const startExercise = useCallback(async () => {
    setError(null);
    setQuestion(null);
    setReflection(null);
    setPhase("loading-bank");
    try {
      const fromBank = await getQuestionFromBank(conceptTag, category);
      setQuestion(fromBank);
      setPhase("question");
      return;
    } catch (e) {
      const bankEmpty =
        e instanceof ApiRequestError &&
        e.status === 404 &&
        e.body.error === "QUESTION_BANK_EMPTY";
      if (!bankEmpty) {
        setPhase("idle");
        setError(humanizeError(e));
        return;
      }
      // 題庫無該題型可用題 → fallback 走 /quiz/generate
    }

    setPhase("loading-generate");
    try {
      const generated = await generateQuestion({
        type: category,
        bloom_level: 3,
        concept_tag: conceptTag,
      });
      setQuestion(generated);
      setPhase("question");
    } catch (e) {
      setPhase("idle");
      setError(humanizeError(e));
    }
  }, [conceptTag, category]);

  const handleApproveReflection = useCallback((r: Reflection) => {
    setReflection(r);
    setPhase("done");
  }, []);

  const closeReflectionModal = useCallback(() => {
    if (phase === "reflecting") setPhase("question");
  }, [phase]);

  const reset = useCallback(() => {
    setQuestion(null);
    setReflection(null);
    setPhase("idle");
    setError(null);
  }, []);

  const isCoding = question?.type === "coding";
  const showPanel =
    (phase === "question" || phase === "reflecting" || phase === "done") && question;
  const stem = (question?.content as { stem?: string } | undefined)?.stem ?? null;

  return (
    <div className="space-y-4">
      {phase === "idle" && (
        <IdleView
          category={category}
          conceptNameZh={conceptNameZh}
          onStart={startExercise}
          error={error}
        />
      )}
      {phase === "loading-bank" && <LoadingView source="bank" />}
      {phase === "loading-generate" && <LoadingView source="generate" />}
      {showPanel &&
        (isCoding ? (
          <CodingPanel
            question={question}
            phase={phase as CodingPhase}
            reflection={reflection}
            onStartReflect={() => setPhase("reflecting")}
            onReset={reset}
          />
        ) : (
          <McPanel question={question} onNext={startExercise} onReset={reset} />
        ))}
      {/* 反思 gating 僅程式實作題；MC 直接作答 */}
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

function humanizeError(e: unknown): string {
  if (e instanceof ApiRequestError) {
    if (e.status === 404 && e.body.error === "CONCEPT_NOT_FOUND") {
      return "本單元的概念尚未在後端註冊（請聯絡管理員）。";
    }
    if (e.status === 503 && e.body.error === "QUIZ_VALIDATION_RETRY_EXHAUSTED") {
      return "AI 生成題目連續審查未通過，請再試一次。";
    }
    if (e.status === 503 && e.body.error === "QUIZ_UNAVAILABLE") {
      return "題庫尚未初始化。";
    }
    if (e.status === 401) return "請先登入。";
    return e.body.message || "生成題目失敗。";
  }
  return e instanceof Error ? e.message : "未知錯誤";
}
