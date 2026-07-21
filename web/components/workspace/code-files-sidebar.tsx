"use client";

/**
 * 我的程式碼側邊欄（U2e）— 與反思計畫同側（左），可收合：
 * 另存命名檔案（同名覆蓋）+ 列表載入/刪除。
 */

import { useEffect, useState } from "react";
import { Loader2, Trash2, X } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import {
  CodeFileMeta,
  deleteCodeFile,
  getCodeFile,
  listCodeFiles,
} from "@/lib/code-files";

export function CodeFilesSidebar({
  onSaveAs,
  onLoad,
  onCollapse,
  currentName = null,
  onDeletedCurrent,
  refreshToken = 0,
}: {
  /** 以指定檔名儲存編輯器目前內容（與 Ctrl/Cmd+S 同一流程） */
  onSaveAs: (name: string) => Promise<void>;
  /** 載入檔案內容至編輯器 */
  onLoad: (code: string, name: string) => void;
  /** 收合時呼叫（caller 控制 layout） */
  onCollapse: () => void;
  /** 目前開啟的命名檔案名稱（用於偵測刪到當前檔案） */
  currentName?: string | null;
  /** 刪除的正是當前開啟檔案時呼叫（caller 跳回預設程式） */
  onDeletedCurrent?: () => void;
  /** 外部儲存成功時遞增，觸發列表重抓 */
  refreshToken?: number;
}) {
  const [files, setFiles] = useState<CodeFileMeta[] | null>(null);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listCodeFiles().then(
      (xs) => !cancelled && setFiles(xs),
      () => !cancelled && setError("載入檔案列表失敗"),
    );
    return () => {
      cancelled = true;
    };
  }, [refreshToken]);

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
      await onSaveAs(name.trim()); // 成功後 refreshToken 遞增觸發重抓
      setName("");
    });

  const load = (f: CodeFileMeta) =>
    run(async () => {
      const detail = await getCodeFile(f.id);
      onLoad(detail.code, detail.name);
    });

  const remove = (f: CodeFileMeta) => {
    const isCurrent = currentName !== null && f.name === currentName;
    const message = isCurrent
      ? `「${f.name}」是目前開啟的檔案，刪除後將移除並跳回預設程式。確定刪除？`
      : `確定刪除「${f.name}」？`;
    if (!confirm(message)) return;
    void run(async () => {
      await deleteCodeFile(f.id);
      setFiles((prev) => prev?.filter((x) => x.id !== f.id) ?? prev);
      if (isCurrent) onDeletedCurrent?.();
    });
  };

  return (
    <aside className="flex h-full flex-col border-r border-border-default bg-surface-1">
      <div className="flex items-center justify-between border-b border-border-default px-3 py-2">
        <span className="text-sm font-medium text-text-primary">我的程式碼</span>
        <button
          type="button"
          onClick={onCollapse}
          className="flex size-6 items-center justify-center rounded-md text-text-muted hover:bg-bg-subtle hover:text-text-primary"
          aria-label="收合我的程式碼側邊欄"
        >
          <X className="size-4" />
        </button>
      </div>

      <div className="border-b border-border-muted p-3">
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
        <p className="mt-1.5 text-[10px] text-text-muted">
          將編輯器目前內容另存為命名檔案
        </p>
        {error && <p className="mt-1 text-xs text-accent-red">{error}</p>}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-1">
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
    </aside>
  );
}
