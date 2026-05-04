"use client";

/**
 * ReflectionSidebar 的「顯示模式」（Phase 2-5d 拆檔）。
 * 唯讀展示反思內容 + 編輯/清除入口。
 */

import { Pencil, Trash2 } from "lucide-react";

import { Reflection } from "@/lib/reflection";

interface ViewModeProps {
  reflection: Reflection;
  onEdit: () => void;
  onClear: () => void;
}

export function ReflectionSidebarView({ reflection, onEdit, onClear }: ViewModeProps) {
  const score = reflection.quality_score;
  const steps = reflection.planned_steps.filter((s) => s.trim());

  return (
    <div className="space-y-4 p-4">
      {score !== null && <QualityChip score={score} />}

      <Section label="問題理解">
        <p className="text-xs leading-5 text-text-primary">
          {reflection.problem_understanding || "（空）"}
        </p>
      </Section>

      <Section label="解題步驟">
        {steps.length > 0 ? (
          <ol className="space-y-1.5 text-xs leading-5 text-text-primary">
            {steps.map((s, i) => (
              <li key={i} className="flex gap-2">
                <span className="shrink-0 text-text-muted">{i + 1}.</span>
                <span>{s}</span>
              </li>
            ))}
          </ol>
        ) : (
          <p className="text-xs text-text-muted">（尚未填寫）</p>
        )}
      </Section>

      <Section label="預期會用到的概念">
        <p className="text-xs leading-5 text-text-primary">
          {reflection.expected_concepts || "（空）"}
        </p>
      </Section>

      {reflection.followup_question && (
        <Section label="AI 教練建議">
          <p className="text-xs leading-5 text-text-secondary">
            {reflection.followup_question}
          </p>
          {reflection.followup_answer && (
            <p className="mt-1.5 text-xs leading-5 text-text-primary">
              <span className="text-text-muted">你的補充：</span>
              {reflection.followup_answer}
            </p>
          )}
        </Section>
      )}

      <div className="flex items-center justify-between border-t border-border-default pt-3">
        <button
          type="button"
          onClick={onEdit}
          className="inline-flex h-7 items-center gap-1 rounded-md border border-border-default bg-btn-default-bg px-2.5 text-xs text-text-secondary hover:text-text-primary"
        >
          <Pencil className="size-3" />
          編輯計畫
        </button>
        <button
          type="button"
          onClick={onClear}
          className="inline-flex h-7 items-center gap-1 rounded-md text-xs text-text-muted hover:text-accent-red"
          title="從側邊欄移除（不刪除後端紀錄）"
        >
          <Trash2 className="size-3" />
          清除
        </button>
      </div>
    </div>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-1.5 text-xs font-medium text-text-secondary">{label}</p>
      {children}
    </div>
  );
}

function QualityChip({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const tone =
    score < 0.4 ? "text-accent-red" : score < 0.6 ? "text-accent-orange" : "text-accent-green";
  return (
    <div className="flex items-center gap-1.5 text-xs text-text-secondary">
      <span>反思品質</span>
      <span className={`font-mono ${tone}`}>{pct}%</span>
    </div>
  );
}
