"use client";

/**
 * 題目上方共用徽章列（難度 / Bloom）— 供 coding-panel 使用。純展示無 state。
 */

import { Question } from "@/lib/quiz";

export function QuestionHeader({ question }: { question: Question }) {
  return (
    <div className="flex items-center gap-2 text-xs text-text-muted">
      <span className="rounded-pill border border-border-default px-1.5">
        難度 {question.difficulty}
      </span>
      <span className="rounded-pill border border-border-default px-1.5">
        Bloom L{question.bloom_level}
      </span>
    </div>
  );
}
