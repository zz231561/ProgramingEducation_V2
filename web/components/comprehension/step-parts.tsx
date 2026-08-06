"use client";

/**
 * 三種 comprehension 步驟共用的小零件（題幹殼、送出鈕、分數條）。
 *
 * 只抽真正重複三次的東西；各 type 的作答區差異很大，不強行共用。
 */

interface StepShellProps {
  prompt: string;
  children: React.ReactNode;
  onSubmit: () => void;
  busy: boolean;
  canSubmit: boolean;
  submitLabel?: string;
  /** 題幹下方的補充說明（如變體挑戰的測資、禁用 AI 提醒） */
  aside?: React.ReactNode;
}

export function StepShell({
  prompt, children, onSubmit, busy, canSubmit, submitLabel = "提交", aside,
}: StepShellProps) {
  return (
    <div className="space-y-3">
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-text-primary">
        {prompt}
      </p>
      {aside}
      {children}
      <div className="flex justify-end">
        <button
          onClick={onSubmit}
          disabled={busy || !canSubmit}
          className="h-8 rounded-md bg-btn-primary-bg px-4 text-sm text-white transition-colors hover:bg-btn-primary-hover disabled:opacity-50"
        >
          {busy ? "評分中…" : submitLabel}
        </button>
      </div>
    </div>
  );
}

/** 0-1 分數條。null＝後端沒給這一項（評分部分失敗時仍要能顯示其餘項目）。 */
export function ScoreBar({ label, value }: { label: string; value: number | null }) {
  const pct = value === null ? 0 : Math.round(Math.min(Math.max(value, 0), 1) * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-text-secondary">{label}</span>
        <span className="font-mono text-text-muted">
          {value === null ? "—" : pct + "%"}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-pill bg-bg-inset">
        <div
          className="h-full rounded-pill bg-accent-blue transition-all"
          style={{ width: pct + "%" }}
        />
      </div>
    </div>
  );
}
