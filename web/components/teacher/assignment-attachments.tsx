"use client";

/**
 * 作業附件面板（5-5a-3）— 懶載入現有附件，支援下載 / 刪除 / 續傳。
 */

import { useEffect, useState } from "react";
import { Download, Loader2, Trash2, Upload } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import {
  AttachmentInfo,
  attachmentDownloadUrl,
  deleteAttachment,
  getAssignment,
  uploadAttachment,
} from "@/lib/assignments";

import { FileDropzone } from "./file-dropzone";

function fmtSize(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export function AssignmentAttachments({ assignmentId }: { assignmentId: string }) {
  const [items, setItems] = useState<AttachmentInfo[] | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getAssignment(assignmentId).then(
      (d) => !cancelled && setItems(d.attachments),
      () => !cancelled && setError("載入附件失敗"),
    );
    return () => {
      cancelled = true;
    };
  }, [assignmentId]);

  const upload = async () => {
    if (!files.length || busy) return;
    setBusy(true);
    setError(null);
    try {
      const added: AttachmentInfo[] = [];
      for (const f of files) added.push(await uploadAttachment(assignmentId, f));
      setItems((prev) => [...(prev ?? []), ...added]);
      setFiles([]);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.body.message : "上傳失敗");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id: string) => {
    setError(null);
    try {
      await deleteAttachment(id);
      setItems((prev) => (prev ?? []).filter((a) => a.id !== id));
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.body.message : "刪除失敗");
    }
  };

  return (
    <div className="space-y-3 p-4">
      {items === null && !error && (
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <Loader2 className="size-3.5 animate-spin" />
          載入附件…
        </div>
      )}
      {items?.length === 0 && (
        <p className="text-xs text-text-muted">尚無附件。</p>
      )}
      {items && items.length > 0 && (
        <ul className="space-y-1">
          {items.map((a) => (
            <li
              key={a.id}
              className="flex items-center justify-between rounded bg-surface-inset px-2 py-1.5 text-xs"
            >
              <a
                href={attachmentDownloadUrl(a.id)}
                download
                className="flex min-w-0 items-center gap-1.5 text-text-link hover:underline"
              >
                <Download className="size-3.5 shrink-0" />
                <span className="truncate">{a.filename}</span>
              </a>
              <div className="flex items-center gap-2 text-text-muted">
                <span>{fmtSize(a.size_bytes)}</span>
                <button
                  onClick={() => remove(a.id)}
                  className="hover:text-accent-red"
                  aria-label={`刪除 ${a.filename}`}
                >
                  <Trash2 className="size-3.5" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
      <FileDropzone files={files} onChange={setFiles} />
      {files.length > 0 && (
        <button
          onClick={upload}
          disabled={busy}
          className="flex h-8 items-center gap-1.5 rounded-md border border-border-default px-3 text-xs text-text-secondary transition-colors hover:bg-surface-2 hover:text-text-primary disabled:opacity-50"
        >
          {busy ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <Upload className="size-3.5" />
          )}
          上傳 {files.length} 個檔案
        </button>
      )}
      {error && <p className="text-xs text-accent-red">{error}</p>}
    </div>
  );
}
