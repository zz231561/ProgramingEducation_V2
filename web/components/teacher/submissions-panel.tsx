"use client";

/**
 * 教師交件檢視面板（5-5b-4）— 名冊 × 繳交狀態列表 + 繳交率統計。
 */

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import {
  Submission,
  SubmissionRow,
  listAssignmentSubmissions,
} from "@/lib/assignments";

import { SubmissionRowItem } from "./submission-row";

export function SubmissionsPanel({ assignmentId }: { assignmentId: string }) {
  const [rows, setRows] = useState<SubmissionRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listAssignmentSubmissions(assignmentId).then(
      (r) => !cancelled && setRows(r),
      (e) =>
        !cancelled &&
        setError(e instanceof ApiRequestError ? e.body.message : "載入失敗"),
    );
    return () => {
      cancelled = true;
    };
  }, [assignmentId]);

  const onGraded = (studentId: string, s: Submission) =>
    setRows(
      (prev) =>
        prev?.map((r) =>
          r.student_id === studentId ? { ...r, submission: s } : r,
        ) ?? prev,
    );

  if (error) return <p className="p-4 text-xs text-accent-red">{error}</p>;
  if (!rows)
    return (
      <div className="flex items-center gap-2 p-4 text-sm text-text-muted">
        <Loader2 className="size-4 animate-spin" />
        載入交件…
      </div>
    );
  if (rows.length === 0)
    return <p className="p-4 text-sm text-text-muted">此班級尚無學生。</p>;

  const submitted = rows.filter((r) => r.submission != null).length;

  return (
    <div>
      <p className="px-4 pt-3 text-xs text-text-muted">
        已繳交 {submitted} / {rows.length}
      </p>
      <div className="mt-2">
        {rows.map((r) => (
          <SubmissionRowItem key={r.student_id} row={r} onGraded={onGraded} />
        ))}
      </div>
    </div>
  );
}
