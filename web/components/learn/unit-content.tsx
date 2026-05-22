"use client";

/**
 * 學習單元內容頁（roadmap 3-1d）— 4 tab + 上下單元導航 + 完成按鈕。
 *
 * 4 tab 內容：
 * - 概念說明：YT IFrame player + grounded markdown + citation 跳轉（6-2c，元件移至 concept-tab.tsx）
 * - 範例程式：grounded code examples + 「在 Workspace 開啟」（6-2d，元件移至 examples-tab.tsx）
 * - 練習題：3-1e 整合 placeholder
 * - 摘要：unit.content.summary（暫無資料時 placeholder）
 *
 * 設計原則：
 * - 元件純 prop-driven（status / 導航 / 完成 callback）
 * - tab 狀態用單一 useState，無路由依賴（單頁切換比 nested route 簡潔）
 * - 「開始學習」/「完成單元」按鈕依 status 顯示
 */

import { useState } from "react";
import { ArrowLeft } from "lucide-react";

import { Unit } from "@/lib/learning";

import { ConceptTab } from "./concept-tab";
import { ExamplesTab } from "./examples-tab";
import { ExercisesTab } from "./exercises-tab";
import { ActionButton, NavButton } from "./unit-action-bar";
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
        {tab === "exercises" && (
          <ExercisesTab
            conceptTag={unit.concept_tag}
            conceptNameZh={unit.concept_name_zh}
          />
        )}
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

