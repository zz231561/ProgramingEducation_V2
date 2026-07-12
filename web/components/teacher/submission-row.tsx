"use client";

/**
 * 單一學生交件列（5-5b-4）— 狀態徽章 + 展開檢視繳交文字/附件 + 評分表單。
 */

import { useState } from "react";
import { ChevronDown, Download } from "lucide-react";

import { formatDateTime, submissionBadge } from "@/lib/assignment-format";
import {
  Submission,
  SubmissionRow,
  attachmentDownloadUrl,
} from "@/lib/assignments";

import { GradeForm } from "./grade-form";

export function SubmissionRowItem({
  row,
  onGraded,
}: {
  row: SubmissionRow;
  onGraded: (studentId: string, s: Submission) => void;
}) {
  const [open, setOpen] = useState(false);
  const badge = submissionBadge(row.submission);
  const sub = row.submission;

  return (
    <div className="border-t border-border-muted first:border-t-0">
      <button
        type="button"
        onClick={() => sub && setOpen((v) => !v)}
        disabled={!sub}
        aria-expanded={open}
        className="flex w-full flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2.5 text-left disabled:cursor-default"
      >
        <span className="min-w-0 flex-1 truncate text-sm text-text-primary">
          {row.real_name || row.email}
          {row.real_name && (
            <span className="ml-2 text-xs text-text-muted">{row.email}</span>
          )}
        </span>
        {sub && (
          <span className="text-xs text-text-muted">
            {formatDateTime(sub.updated_at)}
          </span>
        )}
        <span className={`text-xs ${badge.className}`}>{badge.label}</span>
        {sub && (
          <ChevronDown
            className={`size-3.5 text-text-muted transition-transform ${open ? "rotate-180" : ""}`}
          />
        )}
      </button>

      {open && sub && (
        <div className="space-y-3 px-4 pb-4">
          {sub.text ? (
            <p className="whitespace-pre-wrap rounded-md border border-border-muted bg-bg-canvas p-3 text-sm text-text-secondary">
              {sub.text}
            </p>
          ) : (
            <p className="text-xs text-text-muted">（無文字內容）</p>
          )}

          {row.attachments.length > 0 && (
            <ul className="space-y-1">
              {row.attachments.map((a) => (
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
          )}

          <GradeForm
            submission={sub}
            onGraded={(s) => onGraded(row.student_id, s)}
          />
        </div>
      )}
    </div>
  );
}
