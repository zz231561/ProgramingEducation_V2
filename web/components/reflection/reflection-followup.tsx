"use client";

/**
 * 反思追問元件（Phase 2-5c）— 顯示 LLM 蘇格拉底式追問 + 學生補答 UI。
 *
 * 設計：
 * - 不允許跳過：學生必須補答覆才能再次評分（PRIMM Modify 階段）
 * - 顯示當前 quality_score 與三面向細項（caller 傳入時才顯示）
 * - 受控元件：value/onChange 由 caller 管，提交與放行也由 caller 觸發
 */

import { Lightbulb } from "lucide-react";

interface ReflectionFollowupProps {
  question: string;
  qualityScore: number | null;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function ReflectionFollowup({
  question,
  qualityScore,
  value,
  onChange,
  disabled = false,
}: ReflectionFollowupProps) {
  return (
    <div className="space-y-4">
      {qualityScore !== null && (
        <QualityBar score={qualityScore} />
      )}

      <div className="rounded-md border border-border-default bg-surface-2 p-3">
        <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-accent-purple">
          <Lightbulb className="size-3.5" />
          AI 教練的追問
        </div>
        <p className="text-sm leading-6 text-text-primary">{question}</p>
      </div>

      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-text-primary">
          你的補充回答
        </label>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder="再多想一下，補充更具體的說明..."
          rows={4}
          className="w-full rounded-md border border-border-default bg-bg-canvas px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-blue focus:outline-none disabled:opacity-50"
        />
      </div>
    </div>
  );
}

function QualityBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  // 顏色：紅 < 0.4 / 橘 < 0.6 / 綠 >= 0.6（GitHub Dark accent token）
  const color =
    score < 0.4
      ? "bg-accent-red"
      : score < 0.6
        ? "bg-accent-orange"
        : "bg-accent-green";

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-text-secondary">
        <span>反思品質</span>
        <span className="font-mono">{pct}%</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-pill bg-bg-subtle">
        <div
          className={`h-full ${color} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
