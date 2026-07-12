"use client";

/**
 * 學生作業頁主體（5-5b-3）— 作業列表 + 選取進入詳情/繳交。
 */

import { useCallback, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { formatDue, isOverdue, submissionBadge } from "@/lib/assignment-format";
import { StudentAssignment, listMyAssignments } from "@/lib/assignments";
import { JoinClassForm } from "@/components/classroom/join-class-form";

import { StudentAssignmentDetailView } from "./student-assignment-detail";

export function StudentAssignments() {
  const [items, setItems] = useState<StudentAssignment[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const load = useCallback(() => {
    let cancelled = false;
    listMyAssignments().then(
      (xs) => !cancelled && setItems(xs),
      (e) =>
        !cancelled &&
        setError(e instanceof ApiRequestError ? e.body.message : "載入失敗"),
    );
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => load(), [load]);

  if (selected)
    return (
      <StudentAssignmentDetailView
        assignmentId={selected}
        onBack={() => setSelected(null)}
      />
    );

  return (
    <div className="mx-auto w-full max-w-3xl space-y-4">
      <h1 className="text-xl font-medium text-text-primary">作業</h1>
      {error && <p className="text-sm text-accent-red">{error}</p>}
      {!items && !error && (
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <Loader2 className="size-4 animate-spin" />
          載入作業…
        </div>
      )}
      {items?.length === 0 && (
        <div className="rounded-md border border-border-default bg-surface-1 p-4">
          <p className="text-sm text-text-muted">
            目前沒有作業。若老師提供了班級邀請碼，可在此加入班級：
          </p>
          <div className="mt-3">
            <JoinClassForm onJoined={load} />
          </div>
        </div>
      )}
      {items && items.length > 0 && (
        <ul className="space-y-2">
          {items.map((a) => {
            const badge = submissionBadge(a.submission);
            return (
              <li key={a.id}>
                <button
                  onClick={() => setSelected(a.id)}
                  className="flex w-full items-start justify-between gap-3 rounded-md border border-border-default bg-surface-1 px-4 py-3 text-left transition-colors hover:border-border-emphasis"
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-text-primary">
                      {a.title}
                    </div>
                    <div className="mt-0.5 text-xs text-text-muted">
                      {formatDue(a.due_at)}
                      {isOverdue(a.due_at) && a.submission == null && (
                        <span className="text-accent-orange"> · 已逾期</span>
                      )}
                    </div>
                  </div>
                  <span className={`shrink-0 text-xs ${badge.className}`}>
                    {badge.label}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
