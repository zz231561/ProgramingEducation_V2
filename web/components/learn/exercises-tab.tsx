"use client";

/**
 * 練習題 tab — 3-1e 觸發點。
 *
 * 三狀態：
 * - idle：「開始練習」按鈕
 * - question：顯示題目 + 「開始反思」按鈕
 * - done：反思完成 ✓
 *
 * 範圍：本 tab 負責「取題 → 反思觸發」。完整作答 UI（含程式碼編輯 / 提交判分）屬 Phase 3-2。
 * 點「在 Workspace 作答」可導向 /workspace（reflection_id 已寫入 sessionStorage 由
 * use-active-reflection hook 帶入）。
 */

import { useCallback, useState } from "react";
import { Loader2, Play, Sparkles } from "lucide-react";
import Link from "next/link";

import { ReflectionFlow } from "@/components/reflection/reflection-flow";
import { ApiRequestError } from "@/lib/api";
import { Question, generateQuestion } from "@/lib/quiz";
import { Reflection } from "@/lib/reflection";

interface Props {
  conceptTag: string;
  conceptNameZh: string;
}

type Phase = "idle" | "loading" | "question" | "reflecting" | "done";

export function ExercisesTab({ conceptTag, conceptNameZh }: Props) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [question, setQuestion] = useState<Question | null>(null);
  const [reflection, setReflection] = useState<Reflection | null>(null);
  const [error, setError] = useState<string | null>(null);

  const startExercise = useCallback(async () => {
    setError(null);
    setPhase("loading");
    try {
      const q = await generateQuestion({
        type: "coding",
        bloom_level: 3,
        concept_tag: conceptTag,
      });
      setQuestion(q);
      setPhase("question");
    } catch (e) {
      setPhase("idle");
      setError(humanizeError(e));
    }
  }, [conceptTag]);

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

  return (
    <div className="space-y-4">
      {phase === "idle" && (
        <IdleView conceptNameZh={conceptNameZh} onStart={startExercise} error={error} />
      )}
      {phase === "loading" && <LoadingView />}
      {(phase === "question" || phase === "reflecting" || phase === "done") && question && (
        <QuestionPanel
          question={question}
          phase={phase}
          reflection={reflection}
          onStartReflect={() => setPhase("reflecting")}
          onReset={reset}
        />
      )}
      <ReflectionFlow
        open={phase === "reflecting"}
        sourceType="quiz"
        sourceId={question?.id ?? null}
        onApprove={handleApproveReflection}
        onClose={closeReflectionModal}
      />
    </div>
  );
}

function IdleView({
  conceptNameZh,
  onStart,
  error,
}: {
  conceptNameZh: string;
  onStart: () => void;
  error: string | null;
}) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 px-6 py-8 text-center">
      <Sparkles className="mx-auto size-8 text-text-muted/60" />
      <p className="mt-3 text-sm text-text-primary">
        針對「{conceptNameZh}」練習一題
      </p>
      <p className="mt-1 text-xs text-text-secondary">
        系統會生成程式撰寫題；你會先讀題、寫下解題思路（反思），再進入作答
      </p>
      <button
        type="button"
        onClick={onStart}
        className="mt-5 inline-flex h-9 items-center gap-2 rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover"
      >
        <Play className="size-4" />
        開始練習
      </button>
      {error && (
        <div className="mt-4 rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-left text-xs text-accent-red">
          {error}
        </div>
      )}
    </div>
  );
}

function LoadingView() {
  return (
    <div className="flex flex-col items-center gap-3 py-12 text-text-secondary">
      <Loader2 className="size-6 animate-spin" />
      <p className="text-sm">AI 正在生成題目（含自我審查 retry）...</p>
      <p className="text-xs text-text-muted">通常 5–15 秒</p>
    </div>
  );
}

function QuestionPanel({
  question,
  phase,
  reflection,
  onStartReflect,
  onReset,
}: {
  question: Question;
  phase: Phase;
  reflection: Reflection | null;
  onStartReflect: () => void;
  onReset: () => void;
}) {
  const content = question.content as { stem: string; starter_code?: string };
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <span className="rounded-pill border border-border-default px-1.5">
            難度 {question.difficulty}
          </span>
          <span className="rounded-pill border border-border-default px-1.5">
            Bloom L{question.bloom_level}
          </span>
        </div>
        <button
          type="button"
          onClick={onReset}
          className="text-xs text-text-secondary hover:text-text-primary"
        >
          重新出題
        </button>
      </div>

      <div className="rounded-md border border-border-default bg-surface-1 p-4">
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-text-primary">
          {content.stem}
        </p>
        {content.starter_code && (
          <pre className="mt-3 overflow-x-auto rounded-md border border-border-default bg-bg-inset p-3 font-mono text-xs text-text-primary">
            {content.starter_code}
          </pre>
        )}
      </div>

      {phase === "question" && (
        <div className="flex justify-center pt-2">
          <button
            type="button"
            onClick={onStartReflect}
            className="inline-flex h-9 items-center gap-2 rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover"
          >
            <Sparkles className="size-4" />
            開始反思
          </button>
        </div>
      )}

      {phase === "reflecting" && (
        <p className="text-center text-xs text-text-muted">
          反思填寫中（請於彈出視窗操作）...
        </p>
      )}

      {phase === "done" && reflection && (
        <ReflectionDoneSummary reflection={reflection} />
      )}
    </div>
  );
}

function ReflectionDoneSummary({ reflection }: { reflection: Reflection }) {
  const score = reflection.quality_score;
  return (
    <div className="space-y-3 rounded-md border border-border-default bg-surface-1 p-4">
      <div className="flex items-center gap-2 text-sm text-accent-green">
        <span>✓ 反思已記錄</span>
        {score !== null && score !== undefined && (
          <span className="text-text-muted">（品質分數 {Math.round(score * 100)}%）</span>
        )}
      </div>
      {reflection.followup_question && (
        <p className="rounded-md border-l-2 border-accent-blue bg-surface-2 px-3 py-2 text-xs text-text-secondary">
          系統追問：{reflection.followup_question}
        </p>
      )}
      <p className="text-xs text-text-secondary">
        完整作答介面整合中（屬 Phase 3-2 Quiz 完整版）。你可以：
      </p>
      <div className="flex gap-2">
        <Link
          href="/workspace"
          className="inline-flex h-8 items-center gap-1 rounded-md border border-btn-default-border bg-btn-default-bg px-3 text-xs text-text-primary hover:bg-surface-2"
        >
          在 Workspace 作答
        </Link>
        <span className="self-center text-xs text-text-muted">
          或回上方點「完成單元」結束本單元
        </span>
      </div>
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
