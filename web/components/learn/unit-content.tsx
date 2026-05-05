"use client";

/**
 * 學習單元內容頁（roadmap 3-1d）— 4 tab + 上下單元導航 + 完成按鈕。
 *
 * 4 tab 內容：
 * - 概念說明：concept name/difficulty/category + YT player（video_id 未補時 placeholder）
 * - 範例程式：unit.content.examples（暫無資料時 placeholder）
 * - 練習題：3-1e 整合 placeholder
 * - 摘要：unit.content.summary（暫無資料時 placeholder）
 *
 * 設計原則：
 * - 元件純 prop-driven（status / 導航 / 完成 callback）
 * - tab 狀態用單一 useState，無路由依賴（單頁切換比 nested route 簡潔）
 * - 「開始學習」/「完成單元」按鈕依 status 顯示
 */

import { useState } from "react";
import { ArrowLeft, ChevronLeft, ChevronRight, MonitorPlay, Play } from "lucide-react";

import { Unit } from "@/lib/learning";

import { UnitStatusIcon, statusLabel } from "./unit-status-icon";

type Tab = "concept" | "examples" | "exercises" | "summary";

interface Props {
  unit: Unit;
  pathTitle: string;
  totalUnits: number;
  onBack: () => void;
  onPrev: (() => void) | null;
  onNext: (() => void) | null;
  onStart: () => void;
  onComplete: () => void;
  busy: boolean;
}

const TABS: { key: Tab; label: string }[] = [
  { key: "concept", label: "概念說明" },
  { key: "examples", label: "範例程式" },
  { key: "exercises", label: "練習題" },
  { key: "summary", label: "摘要" },
];

export function UnitContent({
  unit,
  pathTitle,
  totalUnits,
  onBack,
  onPrev,
  onNext,
  onStart,
  onComplete,
  busy,
}: Props) {
  const [tab, setTab] = useState<Tab>("concept");

  return (
    <div className="mx-auto w-full max-w-3xl space-y-5">
      <button
        type="button"
        onClick={onBack}
        className="inline-flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary"
      >
        <ArrowLeft className="size-4" />
        返回路徑：{pathTitle}
      </button>

      <header className="space-y-2">
        <div className="flex items-baseline gap-2 text-xs text-text-muted">
          <span className="font-mono">
            單元 {String(unit.order_index + 1).padStart(2, "0")} / {String(totalUnits).padStart(2, "0")}
          </span>
          <span>·</span>
          <UnitStatusIcon status={unit.status} className="size-3.5" />
          <span>{statusLabel(unit.status)}</span>
        </div>
        <h1 className="text-2xl font-medium text-text-primary">
          {unit.concept_name_zh}
        </h1>
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <span className="rounded-pill border border-border-default px-1.5">
            難度 {unit.concept_difficulty}
          </span>
          <span>·</span>
          <span className="font-mono">{unit.concept_tag}</span>
        </div>
      </header>

      <div className="border-b border-border-default">
        <div className="flex gap-4">
          {TABS.map((t) => (
            <TabButton
              key={t.key}
              active={tab === t.key}
              onClick={() => setTab(t.key)}
            >
              {t.label}
            </TabButton>
          ))}
        </div>
      </div>

      <div className="min-h-[240px]">
        {tab === "concept" && <ConceptTab unit={unit} />}
        {tab === "examples" && <ExamplesTab unit={unit} />}
        {tab === "exercises" && <ExercisesTab />}
        {tab === "summary" && <SummaryTab unit={unit} />}
      </div>

      <div className="flex items-center justify-between border-t border-border-default pt-4">
        <NavButton disabled={!onPrev} onClick={onPrev || undefined} direction="prev" />
        <ActionButton unit={unit} onStart={onStart} onComplete={onComplete} busy={busy} />
        <NavButton disabled={!onNext} onClick={onNext || undefined} direction="next" />
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative pb-2 text-sm transition-colors ${
        active
          ? "text-text-primary after:absolute after:bottom-[-1px] after:left-0 after:right-0 after:h-[2px] after:bg-accent-blue"
          : "text-text-secondary hover:text-text-primary"
      }`}
    >
      {children}
    </button>
  );
}

function ConceptTab({ unit }: { unit: Unit }) {
  // P1 階段 video_youtube_id 多為 NULL（後端 schema 已支援，等教授補資料）
  // unit.content 不含 video metadata；本 tab 顯示 placeholder + concept 描述
  return (
    <div className="space-y-4">
      <VideoPlayerPlaceholder />
      <div className="rounded-md border border-border-default bg-surface-1 p-4">
        <h3 className="text-sm font-medium text-text-primary">概念簡介</h3>
        <p className="mt-2 text-sm leading-relaxed text-text-secondary">
          這個單元對應 C++ 課程的「{unit.concept_name_zh}」。
          詳細教學內容由教授提供的 YouTube 影片提供（待 video_id 匯入後此處顯示播放器）。
        </p>
      </div>
    </div>
  );
}

function VideoPlayerPlaceholder() {
  return (
    <div className="flex aspect-video w-full items-center justify-center rounded-md border border-border-default bg-bg-inset text-text-muted">
      <div className="text-center">
        <MonitorPlay className="mx-auto size-10" />
        <p className="mt-2 text-sm">教學影片（YT player 待整合）</p>
        <p className="mt-1 text-xs text-text-muted/70">
          教授提供影片 ID 後即可播放
        </p>
      </div>
    </div>
  );
}

function ExamplesTab({ unit }: { unit: Unit }) {
  const examples = unit.content.examples ?? [];
  if (examples.length === 0) {
    return <EmptyTab text="範例程式碼將在後續加入（教學素材匯入後填入）" />;
  }
  return (
    <div className="space-y-3">
      {examples.map((code, idx) => (
        <pre
          key={idx}
          className="overflow-x-auto rounded-md border border-border-default bg-bg-inset p-3 font-mono text-sm text-text-primary"
        >
          {code}
        </pre>
      ))}
    </div>
  );
}

function ExercisesTab() {
  return (
    <EmptyTab text="練習題整合屬 3-1e 範圍 — 將復用 Pre-Coding Reflection 流程，從本單元概念出題並觸發反思表單" />
  );
}

function SummaryTab({ unit }: { unit: Unit }) {
  const summary = unit.content.summary ?? "";
  if (!summary) {
    return <EmptyTab text="本單元摘要將在後續加入（可由 LLM 自動生成或教授手動填寫）" />;
  }
  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4 text-sm leading-relaxed text-text-secondary">
      {summary}
    </div>
  );
}

function EmptyTab({ text }: { text: string }) {
  return (
    <div className="rounded-md border border-border-default bg-surface-1 px-6 py-12 text-center text-sm text-text-secondary">
      {text}
    </div>
  );
}

function NavButton({
  disabled,
  onClick,
  direction,
}: {
  disabled: boolean;
  onClick: (() => void) | undefined;
  direction: "prev" | "next";
}) {
  const isPrev = direction === "prev";
  const Icon = isPrev ? ChevronLeft : ChevronRight;
  const label = isPrev ? "上一單元" : "下一單元";
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="inline-flex h-8 items-center gap-1 rounded-md border border-btn-default-border bg-btn-default-bg px-3 text-sm text-text-primary hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40"
    >
      {isPrev && <Icon className="size-4" />}
      {label}
      {!isPrev && <Icon className="size-4" />}
    </button>
  );
}

function ActionButton({
  unit,
  onStart,
  onComplete,
  busy,
}: {
  unit: Unit;
  onStart: () => void;
  onComplete: () => void;
  busy: boolean;
}) {
  if (unit.status === "available") {
    return (
      <button
        type="button"
        onClick={onStart}
        disabled={busy}
        className="inline-flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover disabled:opacity-50"
      >
        <Play className="size-4" />
        開始學習
      </button>
    );
  }
  if (unit.status === "in_progress") {
    return (
      <button
        type="button"
        onClick={onComplete}
        disabled={busy}
        className="inline-flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-4 text-sm font-medium text-white hover:bg-btn-primary-hover disabled:opacity-50"
      >
        完成單元
      </button>
    );
  }
  if (unit.status === "completed") {
    return (
      <span className="text-sm text-accent-green">已完成 ✓</span>
    );
  }
  // locked
  return (
    <span className="text-sm text-text-muted">尚未解鎖</span>
  );
}
