"use client";

/**
 * 我的程式碼選單（U2e）— Toolbar dropdown：另存命名檔案 + 列表載入/刪除。
 */

import { useEffect, useRef, useState } from "react";
import { FolderOpen, Loader2, Trash2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import {
  CodeFileMeta,
  deleteCodeFile,
  getCodeFile,
  listCodeFiles,
  saveCodeFile,
} from "@/lib/code-files";

export function CodeFilesMenu({
  getCode,
  onLoad,
}: {
  /** 取得編輯器目前內容（儲存時） */
  getCode: () => string;
  /** 載入檔案內容至編輯器 */
  onLoad: (code: string, name: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [files, setFiles] = useState<CodeFileMeta[] | null>(null);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    listCodeFiles().then(
      (xs) => !cancelled && setFiles(xs),
      () => !cancelled && setError("載入檔案列表失敗"),
    );
    const onOutside = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node))
        setOpen(false);
    };
    document.addEventListener("mousedown", onOutside);
    return () => {
      cancelled = true;
      document.removeEventListener("mousedown", onOutside);
    };
  }, [open]);

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

  const save = () =>
    run(async () => {
      const saved = await saveCodeFile(name.trim(), getCode());
      setName("");
      setFiles((prev) => [
        saved,
        ...(prev ?? []).filter((f) => f.id !== saved.id),
      ]);
    });

  const load = (f: CodeFileMeta) =>
    run(async () => {
      const detail = await getCodeFile(f.id);
      onLoad(detail.code, detail.name);
      setOpen(false);
    });

  const remove = (f: CodeFileMeta) => {
    if (!confirm(`確定刪除「${f.name}」？`)) return;
    void run(async () => {
      await deleteCodeFile(f.id);
      setFiles((prev) => prev?.filter((x) => x.id !== f.id) ?? prev);
    });
  };

  return (
    <div ref={rootRef} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex h-7 items-center gap-1.5 rounded-md px-2 text-xs text-text-secondary hover:bg-bg-subtle hover:text-text-primary aria-expanded:bg-bg-subtle aria-expanded:text-text-primary"
        title="我的程式碼"
      >
        <FolderOpen className="size-4" />
        我的程式碼
      </button>

      {open && (
        <div className="absolute right-0 top-full z-20 mt-1 w-72 rounded-md border border-border-default bg-surface-1 p-3 shadow-modal">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (name.trim()) void save();
            }}
            className="flex items-center gap-2"
          >
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={100}
              placeholder="檔名（同名覆蓋）"
              className="h-7 min-w-0 flex-1 rounded-md border border-border-default bg-bg-canvas px-2 text-xs text-text-primary focus:border-accent-blue focus:outline-none"
            />
            <button
              type="submit"
              disabled={!name.trim() || busy}
              className="flex h-7 shrink-0 items-center gap-1 rounded-md bg-btn-primary-bg px-2.5 text-xs font-medium text-white transition-colors hover:bg-btn-primary-hover disabled:opacity-50"
            >
              {busy && <Loader2 className="size-3 animate-spin" />}
              儲存
            </button>
          </form>

          {error && <p className="mt-2 text-xs text-accent-red">{error}</p>}

          <div className="mt-2 max-h-64 overflow-y-auto">
            {files === null && (
              <p className="py-2 text-xs text-text-muted">載入中…</p>
            )}
            {files?.length === 0 && (
              <p className="py-2 text-xs text-text-muted">尚無儲存的檔案。</p>
            )}
            {files?.map((f) => (
              <div
                key={f.id}
                className="flex items-center gap-2 border-t border-border-muted py-1.5 first:border-t-0"
              >
                <button
                  onClick={() => load(f)}
                  disabled={busy}
                  className="min-w-0 flex-1 text-left disabled:opacity-50"
                  title={`載入 ${f.name}`}
                >
                  <span className="block truncate text-xs text-text-primary hover:text-text-link">
                    {f.name}
                  </span>
                  <span className="text-[10px] text-text-muted">
                    {new Date(f.updated_at).toLocaleString("zh-TW", {
                      dateStyle: "short",
                      timeStyle: "short",
                    })}
                  </span>
                </button>
                <button
                  onClick={() => remove(f)}
                  disabled={busy}
                  aria-label={`刪除 ${f.name}`}
                  className="text-text-muted hover:text-accent-red disabled:opacity-50"
                >
                  <Trash2 className="size-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
