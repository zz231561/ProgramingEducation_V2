"use client";

/**
 * Quiz demo 的題目顯示元件（Phase 2-5c demo）。
 *
 * 在 preview / reflecting / ready 三個 phase 共用：題目本體持續顯示，
 * 確保學生有「先讀題、再反思、最後作答」的完整脈絡（PRIMM 強調對「具體題目」反思）。
 *
 * Phase 完整 Quiz UI 屬 Phase 3-2；此處僅為 2-5c 流程驗證。
 * 2-5d：ready phase 加「前往 Workspace」按鈕，把 reflection_id 寫入 sessionStorage。
 */

import Link from "next/link";
import { ArrowRight, CheckCircle2, RotateCcw, Sparkles } from "lucide-react";

import { setActiveReflectionId } from "@/lib/active-reflection";
import { Reflection } from "@/lib/reflection";

export type DisplayPhase = "preview" | "reflecting" | "ready";

export interface CodingQuestion {
  id: string;
  type: string;
  concept_tags: string[];
  bloom_level: number;
  difficulty: number;
  content: { stem: string; starter_code?: string };
}

interface QuestionDisplayProps {
  question: CodingQuestion;
  phase: DisplayPhase;
  reflection: Reflection | null;
  onStartReflect: () => void;
  onReset: () => void;
}

export function QuestionDisplay({
  question,
  phase,
  reflection,
  onStartReflect,
  onReset,
}: QuestionDisplayProps) {
  return (
    <div className="w-full max-w-3xl space-y-4">
      <Header question={question} onReset={onReset} />
      <Stem stem={question.content.stem} />
      {question.content.starter_code && (
        <StarterCode code={question.content.starter_code} />
      )}
      {phase === "preview" && <PreviewFooter onStartReflect={onStartReflect} />}
      {phase === "reflecting" && <ReflectingHint />}
      {phase === "ready" && reflection && (
        <ReflectionSummary
          reflection={reflection}
          starterCode={question.content.starter_code}
        />
      )}
    </div>
  );
}

function Header({
  question,
  onReset,
}: {
  question: CodingQuestion;
  onReset: () => void;
}) {
  const tagList = question.concept_tags.join(", ");
  return (
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
  );
}

function Stem({ stem }: { stem: string }) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <p className="text-sm leading-6 text-text-primary">{stem}</p>
    </div>
  );
}

function StarterCode({ code }: { code: string }) {
  return (
    <div className="rounded-md border border-border-default bg-bg-inset p-4">
      <p className="mb-2 text-xs text-text-muted">起手程式碼</p>
      <pre className="overflow-x-auto font-mono text-xs leading-5 text-text-primary">
        {code}
      </pre>
    </div>
  );
}

function PreviewFooter({ onStartReflect }: { onStartReflect: () => void }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-border-default bg-surface-2 p-4">
      <div className="space-y-1">
        <p className="text-sm font-medium text-text-primary">讀完題目了嗎？</p>
        <p className="text-xs text-text-secondary">
          動手前先寫下你的解題思路，研究顯示能顯著提升正確率。
        </p>
      </div>
      <button
        type="button"
        onClick={onStartReflect}
        className="inline-flex h-9 shrink-0 items-center gap-2 rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover"
      >
        <Sparkles className="size-4" />
        開始反思
      </button>
    </div>
  );
}

function ReflectingHint() {
  return (
    <div className="rounded-md border border-border-default bg-surface-2 p-3 text-xs text-text-muted">
      請在彈出視窗完成反思後，再回到題目作答。
    </div>
  );
}

function ReflectionSummary({
  reflection,
  starterCode,
}: {
  reflection: Reflection;
  starterCode?: string;
}) {
  const handleGoWorkspace = () =>
    setActiveReflectionId(reflection.id, {
      fileName: "程式實作題",
      starterCode,
    });
  return (
    <div className="rounded-md border border-border-default bg-surface-2 p-4">
      <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-accent-green">
        <CheckCircle2 className="size-3.5" />
        反思已完成 — 你可以開始作答了
      </p>
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
      </ul>
      <div className="mt-3 border-t border-border-default pt-3">
        <Link
          href="/workspace"
          onClick={handleGoWorkspace}
          className="inline-flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-3 text-xs font-medium text-white hover:bg-btn-primary-hover"
        >
          前往 Workspace 作答
          <ArrowRight className="size-3.5" />
        </Link>
        <p className="mt-1.5 text-xs text-text-muted">
          反思計畫會在 Workspace 左側持續顯示，可隨時編輯。
        </p>
      </div>
    </div>
  );
}
