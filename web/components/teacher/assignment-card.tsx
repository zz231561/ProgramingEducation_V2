"use client";

/**
 * 單一作業卡（5-5a-3）— 顯示標題/內容/截止時間，可編輯 / 停用 / 刪除 / 展開附件。
 */

import { useState } from "react";
import { CalendarClock, ChevronDown, Pencil, Trash2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { AssignmentInfo, deleteAssignment, updateAssignment } from "@/lib/assignments";

import { AssignmentAttachments } from "./assignment-attachments";
import { AssignmentEditForm } from "./assignment-edit-form";

function fmtDue(iso: string | null): string {
  if (!iso) return "無截止時間";
  const d = new Date(iso);
  return `截止 ${d.toLocaleString("zh-TW", { dateStyle: "medium", timeStyle: "short" })}`;
}

const actionBtn =
  "rounded-md border border-border-default px-2.5 py-1 text-xs text-text-secondary transition-colors hover:bg-surface-2 hover:text-text-primary disabled:opacity-50";

export function AssignmentCard({
  assignment,
  className,
  onUpdated,
  onDeleted,
}: {
  assignment: AssignmentInfo;
  className?: string;
  onUpdated: (a: AssignmentInfo) => void;
  onDeleted: (id: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [showFiles, setShowFiles] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.body.message : "操作失敗");
    } finally {
      setBusy(false);
    }
  };

  const toggleActive = () =>
    run(async () =>
      onUpdated(await updateAssignment(assignment.id, { is_active: !assignment.is_active })),
    );

  const remove = () => {
    if (!confirm("確定刪除此作業？學生繳交與附件將一併刪除。")) return;
    run(async () => {
      await deleteAssignment(assignment.id);
      onDeleted(assignment.id);
    });
  };

  if (editing) {
    return (
      <div className="rounded-md border border-border-default bg-surface-1">
        <AssignmentEditForm
          assignment={assignment}
          onCancel={() => setEditing(false)}
          onSaved={(a) => {
            onUpdated(a);
            setEditing(false);
          }}
        />
      </div>
    );
  }

  return (
    <div className="rounded-md border border-border-default bg-surface-1">
      <div className="flex flex-wrap items-start gap-x-4 gap-y-2 p-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="truncate text-sm font-medium text-text-primary">
              {assignment.title}
            </h3>
            {!assignment.is_active && (
              <span className="rounded-pill border border-border-emphasis px-2 py-0.5 text-[10px] text-text-muted">
                已停用
              </span>
            )}
          </div>
          {assignment.description && (
            <p className="mt-1 line-clamp-2 whitespace-pre-wrap text-xs text-text-secondary">
              {assignment.description}
            </p>
          )}
          {className && (
            <p className="mt-1 text-xs text-text-muted">{className}</p>
          )}
          <div className="mt-1 flex items-center gap-1.5 text-xs text-text-muted">
            <CalendarClock className="size-3.5" />
            {fmtDue(assignment.due_at)}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setShowFiles((v) => !v)}
            aria-expanded={showFiles}
            className={`flex items-center gap-1 ${actionBtn}`}
          >
            附件
            <ChevronDown
              className={`size-3.5 transition-transform ${showFiles ? "rotate-180" : ""}`}
            />
          </button>
          <button onClick={() => setEditing(true)} className={`flex items-center gap-1 ${actionBtn}`}>
            <Pencil className="size-3.5" />
            編輯
          </button>
          <button onClick={toggleActive} disabled={busy} className={actionBtn}>
            {assignment.is_active ? "停用" : "啟用"}
          </button>
          <button
            onClick={remove}
            disabled={busy}
            aria-label="刪除作業"
            className="rounded-md border border-accent-red px-2 py-1 text-accent-red transition-colors hover:bg-surface-2 disabled:opacity-50"
          >
            <Trash2 className="size-3.5" />
          </button>
        </div>
      </div>

      {error && <p className="px-4 pb-3 text-xs text-accent-red">{error}</p>}

      {showFiles && (
        <div className="border-t border-border-muted">
          <AssignmentAttachments assignmentId={assignment.id} />
        </div>
      )}
    </div>
  );
}
