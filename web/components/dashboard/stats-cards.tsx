"use client";

/**
 * Dashboard 統計卡片網格（roadmap 3-3a）。
 *
 * 4 張卡片：
 * 1. 學習路徑進度（path_progress；無 path 時顯示「尚未建立」）
 * 2. 本週 Quiz（total + accuracy）
 * 3. 精熟度概覽（total / started / mastered）
 * 4. 反思紀錄累計次數
 *
 * 純 prop-driven；視覺對齊 .claude/rules/frontend.md 的 GitHub Dark token + R8 反 AI 感規則。
 */

import {
  BookMarked,
  ClipboardList,
  Sparkles,
  Target,
} from "lucide-react";

import {
  DashboardStats,
  MasteryOverview,
  PathProgress,
  WeekQuiz,
} from "@/lib/dashboard";

interface Props {
  stats: DashboardStats;
}

export function StatsCards({ stats }: Props) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <PathProgressCard data={stats.path_progress} />
      <WeekQuizCard data={stats.week_quiz} />
      <MasteryCard data={stats.mastery} />
      <ReflectionCard count={stats.reflection_count} />
    </div>
  );
}

function CardShell({
  icon: Icon,
  title,
  children,
}: {
  icon: typeof BookMarked;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <div className="flex items-center gap-1.5 text-xs text-text-secondary">
        <Icon className="size-3.5 text-text-muted" />
        <span>{title}</span>
      </div>
      <div className="mt-3">{children}</div>
    </div>
  );
}

function PathProgressCard({ data }: { data: PathProgress | null }) {
  return (
    <CardShell icon={BookMarked} title="學習路徑進度">
      {data === null ? (
        <p className="text-sm text-text-muted">尚未建立</p>
      ) : (
        <>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-medium text-text-primary">
              {data.percent}
            </span>
            <span className="text-sm text-text-muted">%</span>
          </div>
          <p className="mt-1 line-clamp-1 text-xs text-text-muted">
            {data.title}
          </p>
          <div className="mt-2 h-1.5 overflow-hidden rounded-pill bg-surface-2">
            <div
              className="h-full bg-accent-green"
              style={{ width: `${data.percent}%` }}
              role="progressbar"
              aria-valuenow={data.percent}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
          <p className="mt-2 text-xs text-text-muted">
            <span className="text-text-primary">{data.completed_units}</span>
            {" / "}
            {data.total_units} 單元完成
          </p>
        </>
      )}
    </CardShell>
  );
}

function WeekQuizCard({ data }: { data: WeekQuiz }) {
  return (
    <CardShell icon={Target} title="本週 Quiz">
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-medium text-text-primary">
          {data.total_attempts}
        </span>
        <span className="text-sm text-text-muted">題</span>
      </div>
      {data.total_attempts > 0 ? (
        <p className="mt-1 text-xs text-text-muted">
          答對率{" "}
          <span className="font-medium text-accent-green">
            {data.accuracy_percent}%
          </span>
          （{data.correct_count}/{data.total_attempts}）
        </p>
      ) : (
        <p className="mt-1 text-xs text-text-muted">本週尚未作答</p>
      )}
    </CardShell>
  );
}

function MasteryCard({ data }: { data: MasteryOverview }) {
  return (
    <CardShell icon={Sparkles} title="精熟度概覽">
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-medium text-accent-green">
          {data.mastered_count}
        </span>
        <span className="text-sm text-text-muted">
          / {data.total_concepts} 已熟練
        </span>
      </div>
      <p className="mt-1 text-xs text-text-muted">
        已開始學習{" "}
        <span className="text-text-primary">{data.started_count}</span> 個概念
      </p>
    </CardShell>
  );
}

function ReflectionCard({ count }: { count: number }) {
  return (
    <CardShell icon={ClipboardList} title="反思紀錄">
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-medium text-text-primary">{count}</span>
        <span className="text-sm text-text-muted">次</span>
      </div>
      <p className="mt-1 text-xs text-text-muted">
        {count === 0 ? "尚未開始反思" : "累計解題前反思次數"}
      </p>
    </CardShell>
  );
}
