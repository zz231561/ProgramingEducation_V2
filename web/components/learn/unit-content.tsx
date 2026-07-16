"use client";

/**
 * 學習單元內容頁（roadmap 3-1d）— tab 切換 + 上下單元導航 + 完成按鈕。
 *
 * tab 內容（U2g 2026-07-06 晚間重構）：
 * - 概念說明：YT IFrame player + grounded markdown + citation 跳轉（6-2c，元件移至 concept-tab.tsx）
 * - 程式實作題：讀題 → 反思 → Workspace 作答；「課程介紹」單元（video 1-3）隱藏
 * - 觀念題：選擇題直接作答 + 即時回饋
 * ※ 摘要 tab（U2b）與範例程式 tab（U2g）已移除
 *
 * 設計原則：
 * - 元件純 prop-driven（status / 導航 / 完成 callback）
 * - tab 狀態用單一 useState，無路由依賴（單頁切換比 nested route 簡潔）
 * - 「開始學習」/「完成單元」按鈕依 status 顯示
 */

import { useState } from "react";
import { ArrowLeft } from "lucide-react";

import { Unit } from "@/lib/learning";
import { useRole } from "@/lib/use-role";

import { ConceptQuizTab } from "./concept-quiz-tab";
import { ConceptTab } from "./concept-tab";
import { ExercisesTab } from "./exercises-tab";
import { TeacherQuestionBank } from "./teacher-question-bank";
import { ActionButton, NavButton } from "./unit-action-bar";
import { UnitStatusIcon, statusLabel } from "./unit-status-icon";

type Tab = "concept" | "coding" | "quiz" | "bank";

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
  /** 全開瀏覽（教師/DEV）：locked 單元標頭以「可學習」呈現，不顯示鎖頭。 */
  ghostUnlock?: boolean;
}

const TABS: { key: Tab; label: string }[] = [
  { key: "concept", label: "概念說明" },
  { key: "coding", label: "程式實作題" },
  { key: "quiz", label: "觀念題" },
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
  ghostUnlock,
}: Props) {
  const [tab, setTab] = useState<Tab>("concept");
  const role = useRole();
  const displayStatus =
    ghostUnlock && unit.status === "locked" ? "available" : unit.status;

  // 6-3c：資料驅動隱藏 tab——無 batch 題的 tab 直接不顯示
  // （安裝教學片無可測驗概念 → 觀念題消失；課程介紹片無程式題 → 程式實作題消失）
  const tabs = TABS.filter(
    (t) =>
      (t.key !== "coding" || unit.has_coding_exercise) &&
      (t.key !== "quiz" || unit.has_concept_quiz),
  );
  // 5-6c：教師專屬「題庫」tab（看該單元題目 + 解答，解答預設隱藏）
  if (role === "teacher") tabs.push({ key: "bank", label: "題庫（教師）" });
  // 防呆：若切到被隱藏的 tab（例如從一般單元導航到只有概念說明的單元），退回概念說明
  const activeTab = tabs.some((t) => t.key === tab) ? tab : "concept";

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
          <UnitStatusIcon status={displayStatus} className="size-3.5" />
          <span>{statusLabel(displayStatus)}</span>
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
          {tabs.map((t) => (
            <TabButton
              key={t.key}
              active={activeTab === t.key}
              onClick={() => setTab(t.key)}
            >
              {t.label}
            </TabButton>
          ))}
        </div>
      </div>

      <div className="min-h-[240px]">
        {activeTab === "concept" && <ConceptTab unit={unit} />}
        {activeTab === "coding" && (
          <ExercisesTab
            key="coding"
            conceptTag={unit.concept_tag}
            unitTitle={unit.concept_name_zh}
          />
        )}
        {activeTab === "quiz" && (
          <ConceptQuizTab key="quiz" conceptTag={unit.concept_tag} />
        )}
        {activeTab === "bank" && (
          <TeacherQuestionBank key="bank" conceptTag={unit.concept_tag} />
        )}
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

