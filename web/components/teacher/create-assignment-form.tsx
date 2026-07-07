"use client";

/**
 * 建立作業表單（5-5a-3）— 選班級 + 標題/內容/截止時間 + 附件，送出後依序上傳附件。
 */

import { useState } from "react";
import { Loader2, Plus } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import {
  AssignmentInfo,
  createAssignment,
  uploadAttachment,
} from "@/lib/assignments";
import { ClassInfo } from "@/lib/classroom";

import {
  AssignmentFields,
  AssignmentFieldValues,
  localInputToIso,
} from "./assignment-fields";
import { FileDropzone } from "./file-dropzone";

const EMPTY: AssignmentFieldValues = { title: "", description: "", dueLocal: "" };

export function CreateAssignmentForm({
  classes,
  onCreated,
}: {
  classes: ClassInfo[];
  onCreated: (a: AssignmentInfo) => void;
}) {
  const [classId, setClassId] = useState(classes[0]?.id ?? "");
  const [values, setValues] = useState<AssignmentFieldValues>(EMPTY);
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (classes.length === 0) {
    return (
      <p className="text-sm text-text-muted">
        請先於「班級管理」建立班級，才能指派作業。
      </p>
    );
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!classId || !values.title.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const a = await createAssignment({
        class_id: classId,
        title: values.title.trim(),
        description: values.description.trim(),
        due_at: localInputToIso(values.dueLocal),
      });
      for (const f of files) await uploadAttachment(a.id, f);
      onCreated(a);
      setValues(EMPTY);
      setFiles([]);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.body.message : "建立失敗");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-3">
      <select
        value={classId}
        onChange={(e) => setClassId(e.target.value)}
        className="h-8 w-full rounded-md border border-border-default bg-bg-canvas px-2 text-sm text-text-primary focus:border-accent-blue focus:outline-none [color-scheme:dark]"
      >
        {classes.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </select>
      <AssignmentFields
        values={values}
        onChange={(p) => setValues((v) => ({ ...v, ...p }))}
      />
      <FileDropzone files={files} onChange={setFiles} />
      <button
        type="submit"
        disabled={busy || values.title.trim().length === 0}
        className="flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-3 text-sm font-medium text-white transition-colors hover:bg-btn-primary-hover disabled:opacity-50"
      >
        {busy ? (
          <Loader2 className="size-4 animate-spin" />
        ) : (
          <Plus className="size-4" />
        )}
        建立作業
      </button>
      {error && <p className="text-xs text-accent-red">{error}</p>}
    </form>
  );
}
