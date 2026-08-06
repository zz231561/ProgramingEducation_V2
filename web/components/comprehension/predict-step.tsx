"use client";

/**
 * 預測輸出 — 後端生一組新測資，學生在不執行的情況下預測程式會印什麼（2-6c）。
 *
 * 評分後才揭露正解：`expected_output` 在 generate 階段刻意不下發（存在 server 端），
 * 前端拿不到也就洩不了。
 */

import { StepShell } from "./step-parts";
import type { PredictGrade } from "@/lib/comprehension";

const MATCH_LABEL: Record<string, string> = {
  exact: "與正解逐字相符",
  semantic: "語意相符（格式略有差異）",
  mismatch: "與正解不符",
};

interface Props {
  testInput: string;
  answer: string;
  onAnswerChange: (value: string) => void;
  onSubmit: () => void;
  busy: boolean;
  grade: PredictGrade | null;
}

export function PredictStep({
  testInput, answer, onAnswerChange, onSubmit, busy, grade,
}: Props) {
  if (grade) {
    return (
      <div className="space-y-3">
        <Block label="你的預測">{answer || "（空白）"}</Block>
        <Block label="實際輸出">{grade.expected_output}</Block>
        <p className="text-xs text-text-muted">
          判定方式：{MATCH_LABEL[grade.match_method] ?? grade.match_method}
        </p>
      </div>
    );
  }

  return (
    <StepShell
      prompt="如果用下面這組輸入跑你剛才的程式，會印出什麼？先想清楚再填，不要執行。"
      onSubmit={onSubmit}
      busy={busy}
      canSubmit={answer.trim().length > 0}
      aside={<Block label="測試輸入">{testInput}</Block>}
    >
      <textarea
        value={answer}
        onChange={(e) => onAnswerChange(e.target.value)}
        disabled={busy}
        rows={4}
        placeholder="預測的輸出內容（含換行）"
        className="w-full resize-none rounded-md border border-border-default bg-bg-canvas px-3 py-2 font-mono text-sm text-text-primary placeholder:text-text-muted focus:border-accent-blue focus:outline-none disabled:opacity-50"
      />
    </StepShell>
  );
}

function Block({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <span className="text-xs text-text-muted">{label}</span>
      <pre className="overflow-x-auto rounded-md border border-border-default bg-bg-inset px-3 py-2 font-mono text-xs text-text-primary">
        {children}
      </pre>
    </div>
  );
}
