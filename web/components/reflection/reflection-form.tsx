"use client";

/**
 * Pre-Coding Reflection 表單元件（Phase 2-5c）。
 *
 * 三個必填欄位（PRIMM / Polya 解題四步驟）：
 * - problem_understanding：學生重述問題（避免直接動手沒讀題）
 * - planned_steps：步驟列表（動態增刪）
 * - expected_concepts：預期會用到的概念
 *
 * 純受控元件 — 由 caller 管 state；caller 統一決定送出時機。
 */

import { useCallback } from "react";
import { Plus, X } from "lucide-react";

export interface ReflectionFormValue {
  problemUnderstanding: string;
  plannedSteps: string[];
  expectedConcepts: string;
}

interface ReflectionFormProps {
  value: ReflectionFormValue;
  onChange: (value: ReflectionFormValue) => void;
  disabled?: boolean;
}

export function ReflectionForm({ value, onChange, disabled = false }: ReflectionFormProps) {
  const setUnderstanding = useCallback(
    (problemUnderstanding: string) => onChange({ ...value, problemUnderstanding }),
    [value, onChange],
  );

  const setConcepts = useCallback(
    (expectedConcepts: string) => onChange({ ...value, expectedConcepts }),
    [value, onChange],
  );

  const setStep = useCallback(
    (idx: number, text: string) => {
      const next = [...value.plannedSteps];
      next[idx] = text;
      onChange({ ...value, plannedSteps: next });
    },
    [value, onChange],
  );

  const addStep = useCallback(() => {
    onChange({ ...value, plannedSteps: [...value.plannedSteps, ""] });
  }, [value, onChange]);

  const removeStep = useCallback(
    (idx: number) => {
      const next = value.plannedSteps.filter((_, i) => i !== idx);
      onChange({ ...value, plannedSteps: next.length > 0 ? next : [""] });
    },
    [value, onChange],
  );

  return (
    <div className="space-y-5">
      <Field
        label="這個問題要你做什麼？"
        hint="用你自己的話重述題目（不要抄原文）"
      >
        <textarea
          value={value.problemUnderstanding}
          onChange={(e) => setUnderstanding(e.target.value)}
          disabled={disabled}
          placeholder="例：給定一串整數，找出第 K 大的數..."
          rows={3}
          className={INPUT_BASE}
        />
      </Field>

      <Field
        label="你打算怎麼做？"
        hint="逐步寫下解題計畫（越具體越好）"
      >
        <div className="space-y-2">
          {value.plannedSteps.map((step, idx) => (
            <StepRow
              key={idx}
              index={idx}
              value={step}
              disabled={disabled}
              canRemove={value.plannedSteps.length > 1}
              onChange={(text) => setStep(idx, text)}
              onRemove={() => removeStep(idx)}
            />
          ))}
          <button
            type="button"
            onClick={addStep}
            disabled={disabled}
            className="flex items-center gap-1 text-xs text-text-secondary hover:text-text-primary disabled:opacity-50"
          >
            <Plus className="size-3.5" />
            新增步驟
          </button>
        </div>
      </Field>

      <Field
        label="會用到哪些概念？"
        hint="例如：迴圈、陣列、排序、雜湊表..."
      >
        <input
          type="text"
          value={value.expectedConcepts}
          onChange={(e) => setConcepts(e.target.value)}
          disabled={disabled}
          placeholder="以逗號分隔"
          className={INPUT_BASE}
        />
      </Field>
    </div>
  );
}

const INPUT_BASE =
  "w-full rounded-md border border-border-default bg-bg-canvas px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-blue focus:outline-none disabled:opacity-50";

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <div>
        <label className="block text-sm font-medium text-text-primary">{label}</label>
        {hint && <p className="text-xs text-text-muted">{hint}</p>}
      </div>
      {children}
    </div>
  );
}

function StepRow({
  index,
  value,
  disabled,
  canRemove,
  onChange,
  onRemove,
}: {
  index: number;
  value: string;
  disabled: boolean;
  canRemove: boolean;
  onChange: (text: string) => void;
  onRemove: () => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-5 shrink-0 text-xs text-text-muted">{index + 1}.</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={`步驟 ${index + 1}`}
        className={INPUT_BASE}
      />
      {canRemove && (
        <button
          type="button"
          onClick={onRemove}
          disabled={disabled}
          className="flex size-7 shrink-0 items-center justify-center rounded-md text-text-muted hover:bg-bg-subtle hover:text-text-primary disabled:opacity-50"
          aria-label={`刪除步驟 ${index + 1}`}
        >
          <X className="size-3.5" />
        </button>
      )}
    </div>
  );
}

/** 表單是否已填到可送出的最低門檻 — 三項皆要有非空字串。 */
export function isReflectionFormValid(value: ReflectionFormValue): boolean {
  if (!value.problemUnderstanding.trim()) return false;
  if (!value.expectedConcepts.trim()) return false;
  const steps = value.plannedSteps.map((s) => s.trim()).filter(Boolean);
  return steps.length > 0;
}

/** 把 form value 轉成 backend payload 形式（trim + 過濾空步驟）。 */
export function toBackendPayload(value: ReflectionFormValue): {
  problem_understanding: string;
  planned_steps: string[];
  expected_concepts: string;
} {
  return {
    problem_understanding: value.problemUnderstanding.trim(),
    planned_steps: value.plannedSteps.map((s) => s.trim()).filter(Boolean),
    expected_concepts: value.expectedConcepts.trim(),
  };
}

export const EMPTY_REFLECTION_FORM: ReflectionFormValue = {
  problemUnderstanding: "",
  plannedSteps: [""],
  expectedConcepts: "",
};
