"use client";

/**
 * 反思追問元件（Phase 2-5c；2026-07-16 修訂）— 顯示 AI 教練追問 + 學生補答 UI。
 *
 * 設計：
 * - 追問是引導不是門檻：可補答、也可由 footer「直接開始作答」跳過
 * - 不顯示分數（避免對初學者造成壓力；分數仍入 DB 供研究）
 * - 受控元件：value/onChange 由 caller 管，提交與放行也由 caller 觸發
 */

import { Lightbulb } from "lucide-react";

interface ReflectionFollowupProps {
  question: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function ReflectionFollowup({
  question,
  value,
  onChange,
  disabled = false,
}: ReflectionFollowupProps) {
  return (
    <div className="space-y-4">
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
