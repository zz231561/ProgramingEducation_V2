"use client";

/**
 * 學生 Dashboard 頁面（roadmap 3-3a）。
 *
 * 4 張統計卡片 + 1 張今日建議。
 * 最近活動時間線（3-3b）+ 精熟度詳細圖表（3-3c）後續加。
 */

import { useCallback, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { ActivityTimeline } from "@/components/dashboard/activity-timeline";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { TodaySuggestionCard } from "@/components/dashboard/today-suggestion";
import { ApiRequestError } from "@/lib/api";
import { DashboardStats, getDashboardStats } from "@/lib/dashboard";

type View =
  | { mode: "loading" }
  | { mode: "error"; message: string }
  | { mode: "ready"; stats: DashboardStats };

export default function DashboardPage() {
  const [view, setView] = useState<View>({ mode: "loading" });

  const load = useCallback(async () => {
    setView({ mode: "loading" });
    try {
      const stats = await getDashboardStats();
      setView({ mode: "ready", stats });
    } catch (e) {
      setView({ mode: "error", message: humanizeError(e) });
    }
  }, []);

  useEffect(() => {
    // 初次載入；setView 是 effect → external 同步典型情境
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  if (view.mode === "loading") {
    return (
      <div className="flex h-full items-center justify-center text-text-secondary">
        <Loader2 className="mr-2 size-5 animate-spin" />
        載入 Dashboard...
      </div>
    );
  }

  if (view.mode === "error") {
    return (
      <div className="flex h-full items-center justify-center px-6 text-center">
        <div className="max-w-md rounded-md border-l-2 border-accent-red bg-surface-2 px-4 py-3 text-sm text-accent-red">
          {view.message}
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto px-6 py-8">
      <div className="mx-auto w-full max-w-5xl space-y-6">
        <header>
          <h1 className="text-xl font-medium text-text-primary">Dashboard</h1>
          <p className="mt-1 text-sm text-text-secondary">
            你的學習進度概覽 — 路徑、Quiz、精熟度、反思
          </p>
        </header>

        <StatsCards stats={view.stats} />
        <TodaySuggestionCard suggestion={view.stats.today_suggestion} />
        <ActivityTimeline />
      </div>
    </div>
  );
}

function humanizeError(e: unknown): string {
  if (e instanceof ApiRequestError) {
    if (e.status === 401) return "請先登入。";
    return e.body.message || "載入 Dashboard 失敗。";
  }
  return e instanceof Error ? e.message : "未知錯誤";
}
