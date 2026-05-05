"use client";

/**
 * 最近活動時間線（roadmap 3-3b）。
 *
 * 顯示 quiz / reflection / unit_completed 三種事件，依時間倒序。
 * Async load（不擋頁面其餘部分）；空狀態 placeholder。
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  ClipboardList,
  Clock,
  GraduationCap,
  Loader2,
  XCircle,
} from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { ActivityItem, ActivityType, getRecentActivities } from "@/lib/dashboard";

const RECENT_LIMIT = 20;

export function ActivityTimeline() {
  const [items, setItems] = useState<ActivityItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getRecentActivities(RECENT_LIMIT)
      .then((data) => {
        if (!cancelled) setItems(data);
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
        <Clock className="size-3.5 text-text-muted" />
        <span>最近活動</span>
      </header>

      {error ? (
        <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
          {error}
        </div>
      ) : items === null ? (
        <SkeletonRow />
      ) : items.length === 0 ? (
        <EmptyView />
      ) : (
        <ol className="space-y-2">
          {items.map((item, idx) => (
            <ActivityRow key={`${item.type}-${item.timestamp}-${idx}`} item={item} />
          ))}
        </ol>
      )}
    </section>
  );
}

function SkeletonRow() {
  return (
    <div className="flex items-center gap-2 rounded-md border border-border-default bg-surface-1 px-4 py-3 text-sm text-text-secondary">
      <Loader2 className="size-4 animate-spin" />
      載入活動紀錄...
    </div>
  );
}

function EmptyView() {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 px-4 py-6 text-center text-sm text-text-secondary">
      尚無活動紀錄。完成第一個 Quiz 或學習單元後會顯示在這裡。
    </div>
  );
}

function ActivityRow({ item }: { item: ActivityItem }) {
  const inner = (
    <div className="flex items-start gap-3 rounded-md border border-border-default bg-surface-1 px-3 py-2.5 transition-colors hover:border-border-emphasis">
      <ActivityIcon type={item.type} isCorrect={item.is_correct} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-text-primary">{item.title}</p>
        <p className="mt-0.5 text-xs text-text-muted">{item.detail}</p>
      </div>
      <span className="shrink-0 font-mono text-xs text-text-muted">
        {formatRelative(item.timestamp)}
      </span>
    </div>
  );
  if (item.link) {
    return (
      <li>
        <Link href={item.link} className="block">
          {inner}
        </Link>
      </li>
    );
  }
  return <li>{inner}</li>;
}

function ActivityIcon({
  type,
  isCorrect,
}: {
  type: ActivityType;
  isCorrect: boolean | null;
}) {
  const className = "mt-0.5 size-4 shrink-0";
  if (type === "quiz") {
    if (isCorrect === false) {
      return <XCircle className={`${className} text-accent-red`} />;
    }
    return <CheckCircle2 className={`${className} text-accent-green`} />;
  }
  if (type === "reflection") {
    return <ClipboardList className={`${className} text-accent-purple`} />;
  }
  if (type === "unit_completed") {
    return <GraduationCap className={`${className} text-accent-blue`} />;
  }
  return <Clock className={`${className} text-text-muted`} />;
}

function formatRelative(iso: string): string {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "";
  const now = Date.now();
  const diffSec = Math.max(0, Math.floor((now - t) / 1000));
  if (diffSec < 60) return "剛才";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin} 分前`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr} 小時前`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 30) return `${diffDay} 天前`;
  return new Date(iso).toLocaleDateString("zh-TW");
}

function humanizeError(e: unknown): string {
  if (e instanceof ApiRequestError) {
    if (e.status === 401) return "請先登入。";
    return e.body.message || "載入活動紀錄失敗。";
  }
  return e instanceof Error ? e.message : "未知錯誤";
}
