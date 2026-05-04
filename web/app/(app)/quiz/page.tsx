"use client";

/**
 * Quiz 頁面（Phase 2-5c demo 入口）。
 *
 * 完整 Quiz UI 屬於 Phase 3-2；此處先做反思流程 demo：
 * 1. 點「開始示範」→ 後端拿一道 coding 題
 * 2. 進入 preview：題目展示給學生讀，按「開始反思」才彈 modal
 * 3. reflecting：modal 彈出，題目仍在背景
 * 4. ready：反思摘要 + 題目（可作答上下文）
 *
 * 規格：roadmap 2-5c「程式撰寫題開題時觸發反思表單 UI」。
 * 設計原則（PRIMM）：反思必須針對「已讀過的具體題目」，不能讓學生在沒看題就反思。
 */

import { useCallback, useState } from "react";
import { FileQuestion, Loader2, Play } from "lucide-react";

import {
  CodingQuestion,
  DisplayPhase,
  QuestionDisplay,
} from "@/components/quiz-demo/question-display";
import { ReflectionFlow } from "@/components/reflection/reflection-flow";
import { ApiRequestError, api } from "@/lib/api";
import { Reflection } from "@/lib/reflection";

type Phase = "idle" | "loading" | DisplayPhase;

export default function QuizPage() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [question, setQuestion] = useState<CodingQuestion | null>(null);
  const [reflection, setReflection] = useState<Reflection | null>(null);
  const [error, setError] = useState<string | null>(null);

  const startDemo = useCallback(async () => {
    setError(null);
    setPhase("loading");
    try {
      const q = await api<CodingQuestion>("/quiz/generate", {
        method: "POST",
        body: JSON.stringify({ type: "coding", bloom_level: 3 }),
      });
      setQuestion(q);
      setPhase("preview");
    } catch (e) {
      setPhase("idle");
      setError(humanizeQuizError(e));
    }
  }, []);

  const startReflect = useCallback(() => setPhase("reflecting"), []);

  const handleApprove = useCallback((r: Reflection) => {
    setReflection(r);
    setPhase("ready");
  }, []);

  const handleClose = useCallback(() => {
    // 關閉反思 modal → 回到 preview（題目仍可讀），不丟棄 question
    if (phase === "reflecting") setPhase("preview");
  }, [phase]);

  const reset = useCallback(() => {
    setQuestion(null);
    setReflection(null);
    setPhase("idle");
    setError(null);
  }, []);

  const showQuestion = question && phase !== "idle" && phase !== "loading";

  return (
    <div className="flex h-full flex-col items-center px-6 py-10">
      {phase === "idle" && <IdleView onStart={startDemo} error={error} />}
      {phase === "loading" && <LoadingView />}
      {showQuestion && (
        <QuestionDisplay
          question={question}
          phase={phase as DisplayPhase}
          reflection={reflection}
          onStartReflect={startReflect}
          onReset={reset}
        />
      )}
      <ReflectionFlow
        open={phase === "reflecting"}
        sourceType="quiz"
        sourceId={question?.id ?? null}
        onApprove={handleApprove}
        onClose={handleClose}
      />
    </div>
  );
}

function IdleView({
  onStart,
  error,
}: {
  onStart: () => void;
  error: string | null;
}) {
  return (
    <div className="mt-12 max-w-md text-center">
      <FileQuestion className="mx-auto size-10 text-text-muted/60" />
      <h1 className="mt-4 text-xl font-medium text-text-primary">
        Pre-Coding Reflection 示範
      </h1>
      <p className="mt-2 text-sm leading-6 text-text-secondary">
        系統會生成一道程式撰寫題；你會先讀題，再寫下解題思路，最後才動手作答。
        完整 Quiz 介面屬於 Phase 3-2 的範疇。
      </p>
      <button
        type="button"
        onClick={onStart}
        className="mt-6 inline-flex h-9 items-center gap-2 rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover"
      >
        <Play className="size-4" />
        開始示範
      </button>
      {error && (
        <div className="mt-6 rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-left text-xs text-accent-red">
          {error}
        </div>
      )}
    </div>
  );
}

function LoadingView() {
  return (
    <div className="mt-24 flex flex-col items-center gap-3 text-text-secondary">
      <Loader2 className="size-6 animate-spin" />
      <p className="text-sm">AI 正在生成題目（含自我審查 retry）...</p>
      <p className="text-xs text-text-muted">通常 5–15 秒</p>
    </div>
  );
}

function humanizeQuizError(e: unknown): string {
  if (e instanceof ApiRequestError) {
    if (e.status === 503 && e.body.error === "QUIZ_VALIDATION_RETRY_EXHAUSTED") {
      return "AI 連續審查未通過，請再試一次。";
    }
    if (e.status === 503 && e.body.error === "QUIZ_UNAVAILABLE") {
      return "題庫尚未初始化（請聯絡管理員）。";
    }
    if (e.status === 401) return "請先登入。";
    return e.body.message || "生成題目失敗。";
  }
  return e instanceof Error ? e.message : "未知錯誤";
}
