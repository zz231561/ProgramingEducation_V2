"use client";

/**
 * Quiz 頁面（Phase 2-5c demo 入口）。
 *
 * 完整 Quiz UI 屬於 Phase 3-2；此處先做反思流程 demo：
 * 1. 點「開始示範」→ 後端拿一道 coding 題
 * 2. 立刻彈出 ReflectionFlow modal（必填反思 + LLM 評估 + 追問）
 * 3. 放行後顯示題目本體（題幹 + starter_code）
 *
 * 規格：roadmap 2-5c「程式撰寫題開題時觸發反思表單 UI」。
 */

import { useCallback, useState } from "react";
import { FileQuestion, Loader2, Play, RotateCcw } from "lucide-react";

import { ReflectionFlow } from "@/components/reflection/reflection-flow";
import { ApiRequestError, api } from "@/lib/api";
import { Reflection } from "@/lib/reflection";

interface CodingQuestion {
  id: string;
  type: string;
  concept_tags: string[];
  bloom_level: number;
  difficulty: number;
  content: { stem: string; starter_code?: string };
}

type Phase = "idle" | "loading" | "reflecting" | "ready";

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
      setPhase("reflecting");
    } catch (e) {
      setPhase("idle");
      setError(humanizeQuizError(e));
    }
  }, []);

  const handleApprove = useCallback((r: Reflection) => {
    setReflection(r);
    setPhase("ready");
  }, []);

  const handleClose = useCallback(() => {
    if (phase === "reflecting") {
      // 學生取消反思 → 回到 idle，question 也清掉（避免不一致）
      setQuestion(null);
      setPhase("idle");
    }
  }, [phase]);

  const reset = useCallback(() => {
    setQuestion(null);
    setReflection(null);
    setPhase("idle");
    setError(null);
  }, []);

  return (
    <div className="flex h-full flex-col items-center px-6 py-10">
      {phase === "idle" && (
        <IdleView onStart={startDemo} error={error} />
      )}
      {phase === "loading" && <LoadingView />}
      {phase === "ready" && question && (
        <ReadyView question={question} reflection={reflection} onReset={reset} />
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
        點下方按鈕後，系統會生成一道程式撰寫題，並在開題前要求你先反思解題思路。
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

function ReadyView({
  question,
  reflection,
  onReset,
}: {
  question: CodingQuestion;
  reflection: Reflection | null;
  onReset: () => void;
}) {
  const tagList = question.concept_tags.join(", ");
  return (
    <div className="w-full max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-medium text-text-primary">題目</h1>
          <p className="mt-1 text-xs text-text-muted">
            概念：{tagList} ・ Bloom {question.bloom_level} ・ 難度 {question.difficulty}/5
          </p>
        </div>
        <button
          type="button"
          onClick={onReset}
          className="flex h-7 items-center gap-1 rounded-md border border-border-default bg-btn-default-bg px-2.5 text-xs text-text-secondary hover:text-text-primary"
        >
          <RotateCcw className="size-3" />
          重新開始
        </button>
      </div>

      <div className="rounded-md border border-border-default bg-surface-1 p-4">
        <p className="text-sm leading-6 text-text-primary">{question.content.stem}</p>
      </div>

      {question.content.starter_code && (
        <div className="rounded-md border border-border-default bg-bg-inset p-4">
          <p className="mb-2 text-xs text-text-muted">起手程式碼</p>
          <pre className="overflow-x-auto font-mono text-xs leading-5 text-text-primary">
            {question.content.starter_code}
          </pre>
        </div>
      )}

      {reflection && <ReflectionSummary reflection={reflection} />}
    </div>
  );
}

function ReflectionSummary({ reflection }: { reflection: Reflection }) {
  const score = reflection.quality_score;
  return (
    <div className="rounded-md border border-border-default bg-surface-2 p-4">
      <p className="mb-2 text-xs font-medium text-text-secondary">你的反思摘要</p>
      <ul className="space-y-1.5 text-xs leading-5 text-text-primary">
        <li>
          <span className="text-text-muted">問題理解：</span>
          {reflection.problem_understanding || "（空）"}
        </li>
        <li>
          <span className="text-text-muted">步驟：</span>
          {reflection.planned_steps.join(" → ") || "（空）"}
        </li>
        <li>
          <span className="text-text-muted">預期概念：</span>
          {reflection.expected_concepts || "（空）"}
        </li>
        {score !== null && (
          <li>
            <span className="text-text-muted">品質分數：</span>
            <span className="font-mono">{Math.round(score * 100)}%</span>
          </li>
        )}
      </ul>
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
