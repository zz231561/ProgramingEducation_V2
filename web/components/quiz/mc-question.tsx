"use client";

/**
 * 選擇題作答 UI（roadmap 3-2a）。
 *
 * 純 prop-driven：state 由 caller 持有，本元件只負責顯示 + 觸發 onSubmit。
 */

import { useState } from "react";
import { CheckCircle2, Circle } from "lucide-react";

import { MultipleChoiceContent, Question } from "@/lib/quiz";

interface Props {
  question: Question;
  busy: boolean;
  onSubmit: (selectedIndex: number) => void;
}

export function MCQuestion({ question, busy, onSubmit }: Props) {
  const [selected, setSelected] = useState<number | null>(null);
  const content = question.content as MultipleChoiceContent;

  return (
    <div className="space-y-4">
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-text-primary">
        {content.stem}
      </p>

      <ul className="space-y-2">
        {content.options.map((opt, idx) => (
          <li key={idx}>
            <button
              type="button"
              onClick={() => setSelected(idx)}
              disabled={busy}
              className={`flex w-full items-start gap-3 rounded-md border px-3 py-2.5 text-left text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${
                selected === idx
                  ? "border-border-emphasis bg-surface-2 text-text-primary"
                  : "border-border-default bg-surface-1 text-text-secondary hover:border-border-emphasis hover:text-text-primary"
              }`}
            >
              {selected === idx ? (
                <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-accent-blue" />
              ) : (
                <Circle className="mt-0.5 size-4 shrink-0 text-text-muted" />
              )}
              <span className="flex-1">{opt}</span>
            </button>
          </li>
        ))}
      </ul>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => selected !== null && onSubmit(selected)}
          disabled={busy || selected === null}
          className="inline-flex h-9 items-center rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy ? "提交中..." : "提交答案"}
        </button>
      </div>
    </div>
  );
}
