"use client";

/**
 * 編輯作業表單（5-5a-3）— 調整標題 / 內容 / 截止時間（含清除截止）。
 */

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { AssignmentInfo, updateAssignment } from "@/lib/assignments";

import {
  AssignmentFields,
  AssignmentFieldValues,
  isoToLocalInput,
  localInputToIso,
} from "./assignment-fields";

export function AssignmentEditForm({
  assignment,
  onSaved,
  onCancel,
}: {
  assignment: AssignmentInfo;
  onSaved: (a: AssignmentInfo) => void;
  onCancel: () => void;
}) {
  const [values, setValues] = useState<AssignmentFieldValues>({
    title: assignment.title,
    description: assignment.description,
    dueLocal: isoToLocalInput(assignment.due_at),
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    if (!values.title.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await updateAssignment(assignment.id, {
        title: values.title.trim(),
        description: values.description.trim(),
        due_at: localInputToIso(values.dueLocal), // null = 清除截止
      });
      onSaved(updated);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.body.message : "更新失敗");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3 p-4">
      <AssignmentFields
        values={values}
        onChange={(p) => setValues((v) => ({ ...v, ...p }))}
      />
      <div className="flex items-center gap-2">
        <button
          onClick={save}
          disabled={busy || values.title.trim().length === 0}
          className="flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-3 text-sm font-medium text-white transition-colors hover:bg-btn-primary-hover disabled:opacity-50"
        >
          {busy && <Loader2 className="size-4 animate-spin" />}
          儲存
        </button>
        <button
          onClick={onCancel}
          disabled={busy}
          className="h-8 rounded-md border border-border-default px-3 text-sm text-text-secondary transition-colors hover:bg-surface-2 hover:text-text-primary disabled:opacity-50"
        >
          取消
        </button>
      </div>
      {error && <p className="text-xs text-accent-red">{error}</p>}
    </div>
  );
}
