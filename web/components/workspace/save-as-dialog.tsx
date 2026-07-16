"use client";

/**
 * 另存新檔對話框（U2e 快捷鍵修訂）— Ctrl/Cmd+S 於未命名檔案時開啟：
 * 檔名預填且反白（仿主流編輯器），Enter 儲存、Esc 取消。
 */

import { useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";

export function SaveAsDialog({
  suggestedName,
  onSave,
  onClose,
}: {
  suggestedName: string;
  /** 儲存動作（reject 時顯示錯誤，不關閉） */
  onSave: (name: string) => Promise<void>;
  onClose: () => void;
}) {
  const [name, setName] = useState(suggestedName);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 開啟即聚焦並反白檔名，Enter 一鍵確認
  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, []);

  const submit = async () => {
    if (!name.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      await onSave(name.trim());
      onClose();
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.body.message : "儲存失敗");
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 pt-32"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
      onKeyDown={(e) => e.key === "Escape" && onClose()}
      role="dialog"
      aria-modal="true"
      aria-label="儲存至我的程式碼"
    >
      <div className="w-96 rounded-md border border-border-default bg-surface-1 p-4 shadow-modal">
        <h3 className="text-sm font-medium text-text-primary">
          儲存至我的程式碼
        </h3>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void submit();
          }}
          className="mt-3 flex items-center gap-2"
        >
          <input
            ref={inputRef}
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={100}
            placeholder="檔名"
            className="h-8 min-w-0 flex-1 rounded-md border border-border-default bg-bg-canvas px-2 text-sm text-text-primary focus:border-accent-blue focus:outline-none"
          />
          <button
            type="submit"
            disabled={!name.trim() || busy}
            className="flex h-8 shrink-0 items-center gap-1.5 rounded-md bg-btn-primary-bg px-3 text-sm font-medium text-white transition-colors hover:bg-btn-primary-hover disabled:opacity-50"
          >
            {busy && <Loader2 className="size-3.5 animate-spin" />}
            儲存
          </button>
          <button
            type="button"
            onClick={onClose}
            className="h-8 shrink-0 rounded-md border border-border-default px-3 text-sm text-text-secondary transition-colors hover:bg-surface-2 hover:text-text-primary"
          >
            取消
          </button>
        </form>
        <p className="mt-2 text-[10px] text-text-muted">同名檔案將被覆蓋</p>
        {error && <p className="mt-1 text-xs text-accent-red">{error}</p>}
      </div>
    </div>
  );
}
