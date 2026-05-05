"use client";

/**
 * 作答後 EDF 回饋 section（roadmap 3-2c）。
 *
 * 結果頁渲染 → 立即 async fetch /quiz/answers/{id}/feedback；
 * 顯示 BKT 概念精熟度條 + LLM 個人化建議 + 推薦學習單元連結。
 *
 * LLM 慢，所以與 ResultView 主體分離；loading 期間顯示 skeleton。
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { Lightbulb, Loader2, Sparkles, TrendingUp } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import {
  ConceptMasteryItem,
  QuizFeedbackResponse,
  RecommendedUnit,
  getQuizFeedback,
} from "@/lib/quiz";

interface Props {
  answerId: string;
}

export function FeedbackSection({ answerId }: Props) {
  const [data, setData] = useState<QuizFeedbackResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    // 切換 answerId 時 reset state（典型「effect 同步外部 fetch」場景，rule 例外）
    /* eslint-disable react-hooks/set-state-in-effect */
    setData(null);
    setError(null);
    /* eslint-enable react-hooks/set-state-in-effect */
    getQuizFeedback(answerId)
      .then((r) => {
        if (!cancelled) setData(r);
      })
      .catch((e) => {
        if (!cancelled) setError(humanizeError(e));
      });
    return () => {
      cancelled = true;
    };
  }, [answerId]);

  if (error) {
    return (
      <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
        {error}
      </div>
    );
  }

  if (!data) {
    return <SkeletonView />;
  }

  return (
    <div className="space-y-3">
      <SuggestionCard
        suggestion={data.suggestion}
        fallback={data.suggestion_fallback}
      />
      {data.concept_mastery.length > 0 && (
        <MasteryCard items={data.concept_mastery} />
      )}
      {data.recommended_units.length > 0 && (
        <RecommendedCard units={data.recommended_units} />
      )}
    </div>
  );
}

function SkeletonView() {
  return (
    <div className="flex items-center gap-2 rounded-md border border-border-default bg-surface-1 px-4 py-3 text-sm text-text-secondary">
      <Loader2 className="size-4 animate-spin" />
      AI 正在依你的作答產生個人化回饋...
    </div>
  );
}

function SuggestionCard({
  suggestion,
  fallback,
}: {
  suggestion: string;
  fallback: boolean;
}) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <div className="flex items-center gap-1.5 text-xs text-text-secondary">
        <Sparkles className="size-3.5 text-accent-purple" />
        <span>個人化建議</span>
        {fallback && <span className="text-accent-orange">（離線 fallback）</span>}
      </div>
      <p className="mt-2 text-sm leading-relaxed text-text-primary">{suggestion}</p>
    </div>
  );
}

function MasteryCard({ items }: { items: ConceptMasteryItem[] }) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <div className="flex items-center gap-1.5 text-xs text-text-secondary">
        <TrendingUp className="size-3.5 text-accent-blue" />
        <span>相關概念精熟度（BKT）</span>
      </div>
      <ul className="mt-3 space-y-2.5">
        {items.map((m) => (
          <MasteryRow key={m.concept_tag} item={m} />
        ))}
      </ul>
    </div>
  );
}

function MasteryRow({ item }: { item: ConceptMasteryItem }) {
  const percent = Math.round(item.confidence * 100);
  return (
    <li>
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm text-text-primary">{item.concept_name_zh}</span>
        <span className="font-mono text-xs text-text-muted">{percent}%</span>
      </div>
      <div className="mt-1 h-1.5 overflow-hidden rounded-pill bg-surface-2">
        <div
          className="h-full bg-accent-green transition-[width]"
          style={{ width: `${percent}%` }}
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </li>
  );
}

function RecommendedCard({ units }: { units: RecommendedUnit[] }) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <div className="flex items-center gap-1.5 text-xs text-text-secondary">
        <Lightbulb className="size-3.5 text-accent-orange" />
        <span>建議的學習單元</span>
      </div>
      <ul className="mt-3 space-y-1.5">
        {units.map((u) => (
          <li key={u.unit_id}>
            <Link
              href="/learn"
              className="inline-flex items-center gap-2 text-sm text-text-link hover:underline"
            >
              {u.video_order !== null && (
                <span className="font-mono text-xs text-text-muted">
                  #{String(u.video_order).padStart(2, "0")}
                </span>
              )}
              {u.concept_name_zh}
              <span className="text-xs text-text-muted">（{u.status}）</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function humanizeError(e: unknown): string {
  if (e instanceof ApiRequestError) {
    if (e.status === 404 && e.body.error === "STUDENT_ANSWER_NOT_FOUND") {
      return "找不到此作答紀錄。";
    }
    if (e.status === 401) return "請先登入。";
    return e.body.message || "載入回饋失敗。";
  }
  return e instanceof Error ? e.message : "未知錯誤";
}
