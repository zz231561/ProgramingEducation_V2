"use client";

/**
 * EPL（Explain Prior to Looking）— 用自己的話解釋剛才的解法（2-6b）。
 *
 * 評分回三個細項分數（概念正確性 / 具體程度 / 因果連結），
 * 學生看得到分項才知道下次要補哪一塊，只給「通過/未通過」學不到東西。
 */

import { StepShell, ScoreBar } from "./step-parts";
import type { EplGrade } from "@/lib/comprehension";

interface Props {
  prompt: string;
  answer: string;
  onAnswerChange: (value: string) => void;
  onSubmit: () => void;
  busy: boolean;
  grade: EplGrade | null;
}

export function EplStep({
  prompt, answer, onAnswerChange, onSubmit, busy, grade,
}: Props) {
  if (grade) {
    return (
      <div className="space-y-3">
        <ScoreBar label="概念正確性" value={grade.conceptual_correctness} />
        <ScoreBar label="具體程度" value={grade.specificity} />
        <ScoreBar label="因果連結" value={grade.causality} />
      </div>
    );
  }

  return (
    <StepShell
      prompt={prompt}
      onSubmit={onSubmit}
      busy={busy}
      canSubmit={answer.trim().length > 0}
    >
      <textarea
        value={answer}
        onChange={(e) => onAnswerChange(e.target.value)}
        disabled={busy}
        rows={5}
        placeholder="說說看你的程式碼在做什麼、為什麼這樣寫會對……"
        className="w-full resize-none rounded-md border border-border-default bg-bg-canvas px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-blue focus:outline-none disabled:opacity-50"
      />
    </StepShell>
  );
}
