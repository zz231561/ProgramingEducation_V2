"use client";

/**
 * Toolbar 檔名欄位（U2e 驗收修訂）— 點檔名即可就地重新命名。
 * 未命名（草稿）時點擊改為開啟另存對話框，因為還沒有檔案可以改名。
 */

import { useEffect, useRef, useState } from "react";

import { ApiRequestError } from "@/lib/api";
import { toStem, withSuffix } from "@/lib/code-files";

import { FileNameInput } from "./file-name-input";

export function FileNameField({
  name,
  canRename,
  onRename,
  onSaveAs,
}: {
  name: string;
  /** 已存成命名檔案才能改名 */
  canRename: boolean;
  onRename: (newName: string) => Promise<void>;
  /** 未命名時點檔名 → 另存對話框 */
  onSaveAs: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [stem, setStem] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [editing]);

  const start = () => {
    if (!canRename) {
      onSaveAs();
      return;
    }
    setStem(toStem(name));
    setError(null);
    setEditing(true);
  };

  const commit = async () => {
    const next = withSuffix(stem);
    if (!stem.trim() || next === name) {
      setEditing(false);
      return;
    }
    setBusy(true);
    try {
      await onRename(next);
      setEditing(false);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.body.message : "重新命名失敗");
    } finally {
      setBusy(false);
    }
  };

  if (!editing) {
    return (
      <button
        type="button"
        onClick={start}
        title={canRename ? "點擊重新命名" : "點擊儲存至我的程式碼"}
        className="rounded-md px-1 text-sm text-text-primary hover:bg-bg-subtle"
      >
        {name}
      </button>
    );
  }

  return (
    <div className="relative flex w-56 items-center">
      <FileNameInput
        ref={inputRef}
        stem={stem}
        onStemChange={setStem}
        size="xs"
        ariaLabel="重新命名檔案"
        onBlur={() => !busy && setEditing(false)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            if (!busy) void commit();
          } else if (e.key === "Escape") {
            setEditing(false);
          }
        }}
      />
      {error && (
        <p className="absolute left-0 top-8 z-10 whitespace-nowrap rounded-md border border-border-default bg-surface-1 px-2 py-1 text-xs text-accent-red shadow-card">
          {error}
        </p>
      )}
    </div>
  );
}
