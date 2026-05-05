"use client";

/**
 * 精熟度詳細總覽（roadmap 3-3c）。
 *
 * 依 category 分群顯示所有 concepts 的 mastery progress bar。
 * 全展開（無摺疊互動）— 學生一眼看清整體分布。
 *
 * 視覺：
 * - Category header：name + 摘要 (mastered/started/total) + overall bar
 * - 該 category 下：concept 列表（每行 concept name + difficulty pill + mini bar + percent）
 */

import { useEffect, useState } from "react";
import { Layers, Loader2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import {
  CategoryBreakdown,
  ConceptMasteryDetail,
  MasteryOverviewData,
  getMasteryOverview,
} from "@/lib/dashboard";

const MASTERED_THRESHOLD = 0.8;

export function MasteryBreakdown() {
  const [data, setData] = useState<MasteryOverviewData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getMasteryOverview()
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (!cancelled) setError(humanizeError(e));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="space-y-3">
      <header className="flex items-center gap-1.5 text-xs text-text-secondary">
        <Layers className="size-3.5 text-text-muted" />
        <span>精熟度總覽（依主題分群）</span>
      </header>

      {error ? (
        <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
          {error}
        </div>
      ) : data === null ? (
        <SkeletonView />
      ) : data.categories.length === 0 ? (
        <EmptyView />
      ) : (
        <div className="space-y-3">
          {data.categories.map((cat) => (
            <CategorySection key={cat.name} category={cat} />
          ))}
        </div>
      )}
    </section>
  );
}

function SkeletonView() {
  return (
    <div className="flex items-center gap-2 rounded-md border border-border-default bg-surface-1 px-4 py-3 text-sm text-text-secondary">
      <Loader2 className="size-4 animate-spin" />
      載入精熟度資料...
    </div>
  );
}

function EmptyView() {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 px-4 py-6 text-center text-sm text-text-secondary">
      尚未建立任何概念。請聯絡管理員 seed 課程資料。
    </div>
  );
}

function CategorySection({ category }: { category: CategoryBreakdown }) {
  const masteredPercent =
    category.total === 0
      ? 0
      : Math.round((category.mastered / category.total) * 100);
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-sm font-medium text-text-primary">
          {category.name}
        </h3>
        <span className="font-mono text-xs text-text-muted">
          {category.mastered} / {category.total} 熟練
          {category.started > category.mastered && (
            <span className="ml-1.5 text-text-muted/70">
              · {category.started - category.mastered} 進行中
            </span>
          )}
        </span>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-pill bg-surface-2">
        <div
          className="h-full bg-accent-green"
          style={{ width: `${masteredPercent}%` }}
          role="progressbar"
          aria-valuenow={masteredPercent}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>

      <ol className="mt-3 space-y-1.5">
        {category.concepts.map((c) => (
          <ConceptRow key={c.concept_tag} concept={c} />
        ))}
      </ol>
    </div>
  );
}

function ConceptRow({ concept }: { concept: ConceptMasteryDetail }) {
  const percent = Math.round(concept.confidence * 100);
  const isMastered = concept.confidence >= MASTERED_THRESHOLD;
  const barColor = isMastered ? "bg-accent-green" : "bg-accent-blue";
  return (
    <li className="flex items-center gap-3">
      {concept.video_order !== null && (
        <span className="w-7 shrink-0 font-mono text-xs text-text-muted">
          #{String(concept.video_order).padStart(2, "0")}
        </span>
      )}
      <span className="min-w-0 flex-1 truncate text-sm text-text-primary">
        {concept.concept_name_zh}
      </span>
      <span className="rounded-pill border border-border-default px-1.5 text-[10px] text-text-muted">
        D{concept.difficulty}
      </span>
      <div className="h-1 w-24 overflow-hidden rounded-pill bg-surface-2">
        <div
          className={`h-full ${barColor}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="w-9 shrink-0 text-right font-mono text-xs text-text-muted">
        {percent}%
      </span>
    </li>
  );
}

function humanizeError(e: unknown): string {
  if (e instanceof ApiRequestError) {
    if (e.status === 401) return "請先登入。";
    return e.body.message || "載入精熟度資料失敗。";
  }
  return e instanceof Error ? e.message : "未知錯誤";
}
