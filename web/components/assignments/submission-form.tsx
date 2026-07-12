"use client";

/**
 * 學生繳交表單（5-5b-3）— 文字 + 附件；重繳覆蓋、可刪除已繳附件。
 */

import { useState } from "react";
import { Download, Loader2, Send, Trash2 } from "lucide-react";

import { FileDropzone } from "@/components/teacher/file-dropzone";
import { ApiRequestError } from "@/lib/api";
import { formatDateTime, submissionBadge } from "@/lib/assignment-format";
import {
  AttachmentInfo,
  Submission,
  attachmentDownloadUrl,
  deleteAttachment,
  submitAssignment,
  uploadSubmissionAttachment,
} from "@/lib/assignments";

export function SubmissionForm({
  assignmentId,
  submission,
  attachments,
  onChanged,
}: {
  assignmentId: string;
  submission: Submission | null;
  attachments: AttachmentInfo[];
  onChanged: () => void;
}) {
  const [text, setText] = useState(submission?.text ?? "");
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const sub = await submitAssignment(assignmentId, text.trim());
      for (const f of files) await uploadSubmissionAttachment(sub.id, f);
      setFiles([]);
      onChanged();
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.body.message : "繳交失敗");
    } finally {
      setBusy(false);
    }
  };

  const removeAtt = async (id: string) => {
    setError(null);
    try {
      await deleteAttachment(id);
      onChanged();
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.body.message : "刪除失敗");
    }
  };

  return (
    <div className="space-y-3 rounded-md border border-border-default bg-surface-1 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-medium text-text-primary">我的繳交</h3>
        <span className={`text-xs ${submissionBadge(submission).className}`}>
          {submissionBadge(submission).label}
        </span>
        {submission && (
          <span className="text-xs text-text-muted">
            繳交於 {formatDateTime(submission.updated_at)}
          </span>
        )}
      </div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={4}
        placeholder="輸入文字說明（可選）"
        className="w-full resize-y rounded-md border border-border-default bg-bg-canvas px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-blue focus:outline-none"
      />
      {attachments.length > 0 && (
        <ul className="space-y-1">
          {attachments.map((a) => (
            <li
              key={a.id}
              className="flex items-center justify-between rounded bg-surface-inset px-2 py-1 text-xs"
            >
              <a
                href={attachmentDownloadUrl(a.id)}
                download
                className="flex min-w-0 items-center gap-1.5 text-text-link hover:underline"
              >
                <Download className="size-3.5 shrink-0" />
                <span className="truncate">{a.filename}</span>
              </a>
              <button
                onClick={() => removeAtt(a.id)}
                className="text-text-muted hover:text-accent-red"
                aria-label={`刪除 ${a.filename}`}
              >
                <Trash2 className="size-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}
      <FileDropzone files={files} onChange={setFiles} />
      <button
        onClick={submit}
        disabled={busy}
        className="flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-3 text-sm font-medium text-white transition-colors hover:bg-btn-primary-hover disabled:opacity-50"
      >
        {busy ? (
          <Loader2 className="size-4 animate-spin" />
        ) : (
          <Send className="size-4" />
        )}
        {submission ? "更新繳交" : "繳交"}
      </button>
      {error && <p className="text-xs text-accent-red">{error}</p>}
    </div>
  );
}
