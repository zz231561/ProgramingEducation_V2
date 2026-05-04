"use client";

/**
 * ReflectionSidebar 的「編輯模式」（Phase 2-5d 拆檔）。
 * 復用 ReflectionForm；存檔呼叫 PATCH /reflection/{id}（觸發後端重新評分）。
 */

import { useCallback, useState } from "react";
import { Loader2, Save } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import {
  PatchReflectionPayload,
  Reflection,
  patchReflection,
} from "@/lib/reflection";
import {
  EMPTY_REFLECTION_FORM,
  ReflectionForm,
  ReflectionFormValue,
} from "./reflection-form";

interface EditModeProps {
  reflection: Reflection;
  onCancel: () => void;
  onSaved: (r: Reflection) => void;
}

export function ReflectionSidebarEdit({ reflection, onCancel, onSaved }: EditModeProps) {
  const [value, setValue] = useState<ReflectionFormValue>(() => ({
    problemUnderstanding: reflection.problem_understanding,
    plannedSteps:
      reflection.planned_steps.length > 0
        ? reflection.planned_steps
        : EMPTY_REFLECTION_FORM.plannedSteps,
    expectedConcepts: reflection.expected_concepts,
  }));
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const save = useCallback(async () => {
    setSaving(true);
    setErr(null);
    const payload: PatchReflectionPayload = {
      problem_understanding: value.problemUnderstanding.trim(),
      planned_steps: value.plannedSteps.map((s) => s.trim()).filter(Boolean),
      expected_concepts: value.expectedConcepts.trim(),
    };
    try {
      onSaved(await patchReflection(reflection.id, payload));
    } catch (e) {
      setErr(humanizePatchError(e));
    } finally {
      setSaving(false);
    }
  }, [value, reflection.id, onSaved]);

  return (
    <div className="space-y-3 p-4">
      <ReflectionForm value={value} onChange={setValue} disabled={saving} />
      {err && (
        <div className="rounded-md border-l-2 border-accent-red bg-surface-2 px-3 py-2 text-xs text-accent-red">
          {err}
        </div>
      )}
      <div className="flex items-center justify-end gap-2 border-t border-border-default pt-3">
        <button
          type="button"
          onClick={onCancel}
          disabled={saving}
          className="text-xs text-text-muted hover:text-text-secondary disabled:opacity-50"
        >
          取消
        </button>
        <button
          type="button"
          onClick={save}
          disabled={saving}
          className="flex h-7 items-center gap-1 rounded-md bg-btn-primary-bg px-2.5 text-xs font-medium text-white hover:bg-btn-primary-hover disabled:opacity-50"
        >
          {saving ? <Loader2 className="size-3 animate-spin" /> : <Save className="size-3" />}
          儲存
        </button>
      </div>
    </div>
  );
}

function humanizePatchError(e: unknown): string {
  if (e instanceof ApiRequestError) {
    if (e.status === 404) return "反思不存在或已被刪除。";
    return e.body.message || "儲存失敗，請稍後再試。";
  }
  return e instanceof Error ? e.message : "未知錯誤";
}
