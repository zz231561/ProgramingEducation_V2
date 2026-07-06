"use client";

/**
 * 程式實作題面板 — 讀題 → 反思 gating → 引導至 Workspace 作答。
 * 自 exercises-tab.tsx 拆出（題型分類後主檔維持 ≤ 250 行）。
 */

import { CheckCircle2, Sparkles } from "lucide-react";
import Link from "next/link";

import { Question } from "@/lib/quiz";
import { Reflection } from "@/lib/reflection";

import { QuestionHeader } from "./exercises-tab-views";

export type CodingPhase = "question" | "reflecting" | "done";

export function CodingPanel({
  question,
  phase,
  reflection,
  onStartReflect,
  onReset,
}: {
  question: Question;
  phase: CodingPhase;
  reflection: Reflection | null;
  onStartReflect: () => void;
  onReset: () => void;
}) {
  const content = question.content as { stem: string; starter_code?: string };
  return (
    <div className="space-y-3">
      <QuestionHeader question={question} onReset={onReset} />

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
        <CheckCircle2 className="size-4" />
        <span>反思已記錄</span>
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
