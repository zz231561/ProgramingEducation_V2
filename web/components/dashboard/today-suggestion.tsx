"use client";

/**
 * Dashboard 今日建議卡片（roadmap 3-3a）。
 *
 * MVP 用規則版（後端 _today_suggestion）：依 path / unit 狀態決定建議文字 + 連結。
 * LLM 個人化建議留給後續任務。
 */

import { ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";

import { TodaySuggestion } from "@/lib/dashboard";

interface Props {
  suggestion: TodaySuggestion;
}

export function TodaySuggestionCard({ suggestion }: Props) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-5">
      <div className="flex items-center gap-1.5 text-xs text-text-secondary">
        <Sparkles className="size-3.5 text-accent-purple" />
        <span>今日建議</span>
      </div>
      <h2 className="mt-3 text-lg font-medium text-text-primary">
        {suggestion.title}
      </h2>
      <p className="mt-2 text-sm leading-relaxed text-text-secondary">
        {suggestion.description}
      </p>
      <Link
        href={suggestion.link}
        className="mt-4 inline-flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-3 text-sm font-medium text-white hover:bg-btn-primary-hover"
      >
        立即前往
        <ArrowRight className="size-3.5" />
      </Link>
    </div>
  );
}
