"use client";

/**
 * 建立班級表單（5-1c-1）— 輸入班級名稱，送出後回傳含邀請碼的新班級。
 */

import { useState } from "react";
import { Loader2, Plus } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { ClassInfo, createClass } from "@/lib/classroom";

export function CreateClassForm({
  onCreated,
}: {
  onCreated: (klass: ClassInfo) => void;
}) {
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    setError(null);
    try {
      const klass = await createClass(trimmed);
      onCreated(klass);
      setName("");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.body.message : "建立失敗");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="flex flex-wrap items-center gap-2">
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="輸入班級名稱，例如：資工一甲"
        maxLength={100}
        className="h-8 min-w-0 flex-1 rounded-md border border-border-default bg-bg-canvas px-3 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-blue focus:outline-none"
      />
      <button
        type="submit"
        disabled={busy || name.trim().length === 0}
        className="flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-3 text-sm font-medium text-white hover:bg-btn-primary-hover transition-colors disabled:opacity-50"
      >
        {busy ? (
          <Loader2 className="size-4 animate-spin" />
        ) : (
          <Plus className="size-4" />
        )}
        建立班級
      </button>
      {error && <p className="w-full text-xs text-accent-red">{error}</p>}
    </form>
  );
}
