"use client";

/**
 * 學生作業詳情（5-5b-3）— 教師說明/附件 + 評分結果 + 繳交表單。
 */

import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, CalendarClock, Download, Loader2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { formatDue, isOverdue } from "@/lib/assignment-format";
import {
  StudentAssignmentDetail,
  attachmentDownloadUrl,
  getMyAssignment,
} from "@/lib/assignments";

import { SubmissionForm } from "./submission-form";

export function StudentAssignmentDetailView({
  assignmentId,
  onBack,
}: {
  assignmentId: string;
  onBack: () => void;
}) {
  const [detail, setDetail] = useState<StudentAssignmentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    let cancelled = false;
    getMyAssignment(assignmentId).then(
      (d) => !cancelled && setDetail(d),
      (e) =>
        !cancelled &&
        setError(e instanceof ApiRequestError ? e.body.message : "載入失敗"),
    );
    return () => {
      cancelled = true;
    };
  }, [assignmentId]);

  useEffect(() => load(), [load]);

  return (
    <div className="mx-auto w-full max-w-3xl space-y-5">
      <button
        type="button"
        onClick={onBack}
        className="inline-flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary"
      >
        <ArrowLeft className="size-4" />
        返回作業列表
      </button>

      {error && <p className="text-sm text-accent-red">{error}</p>}
      {!detail && !error && (
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <Loader2 className="size-4 animate-spin" />
          載入作業…
        </div>
      )}

      {detail && (
        <>
          <header className="space-y-2">
            <h1 className="text-2xl font-medium text-text-primary">
              {detail.title}
            </h1>
            <div className="flex items-center gap-1.5 text-xs text-text-muted">
              <CalendarClock className="size-3.5" />
              {formatDue(detail.due_at)}
              {isOverdue(detail.due_at) && (
                <span className="text-accent-orange">· 已逾期（仍可補交）</span>
              )}
            </div>
            {detail.description && (
              <p className="whitespace-pre-wrap text-sm text-text-secondary">
                {detail.description}
              </p>
            )}
          </header>

          {detail.teacher_attachments.length > 0 && (
            <section className="space-y-1">
              <h3 className="text-sm font-medium text-text-primary">教師附件</h3>
              <ul className="space-y-1">
                {detail.teacher_attachments.map((a) => (
                  <li key={a.id}>
                    <a
                      href={attachmentDownloadUrl(a.id)}
                      download
                      className="flex w-fit items-center gap-1.5 text-sm text-text-link hover:underline"
                    >
                      <Download className="size-3.5" />
                      {a.filename}
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {detail.submission?.score != null && (
            <div className="rounded-md border border-accent-green bg-surface-1 p-4">
              <div className="text-sm font-medium text-accent-green">
                成績：{detail.submission.score}
              </div>
              {detail.submission.feedback && (
                <p className="mt-1 whitespace-pre-wrap text-sm text-text-secondary">
                  教師評語：{detail.submission.feedback}
                </p>
              )}
            </div>
          )}

          <SubmissionForm
            assignmentId={detail.id}
            submission={detail.submission}
            attachments={detail.submission_attachments}
            onChanged={load}
          />
        </>
      )}
    </div>
  );
}
