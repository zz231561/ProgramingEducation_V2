"use client";

/**
 * 加入班級表單 — 學生輸入 6 位邀請碼入班（作業頁空狀態 + Settings 共用）。
 */

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { joinClass } from "@/lib/classroom";

export function JoinClassForm({ onJoined }: { onJoined: () => void }) {
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const valid = /^\d{6}$/.test(code);

  const submit = async () => {
    if (!valid) return;
    setBusy(true);
    setError(null);
    try {
      await joinClass(code);
      setCode("");
      onJoined();
    } catch (e) {
      setError(
        e instanceof ApiRequestError ? e.body.message : "加入失敗，請重試",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
        className="flex items-center gap-2"
      >
        <input
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
          inputMode="numeric"
          placeholder="6 位邀請碼"
          aria-label="班級邀請碼"
          className="h-8 w-36 rounded-md border border-border-default bg-bg-canvas px-2 text-sm tracking-widest text-text-primary focus:border-accent-blue focus:outline-none"
        />
        <button
          type="submit"
          disabled={!valid || busy}
          className="flex h-8 items-center gap-1.5 rounded-md bg-btn-primary-bg px-3 text-sm font-medium text-white transition-colors hover:bg-btn-primary-hover disabled:opacity-50"
        >
          {busy && <Loader2 className="size-3.5 animate-spin" />}
          加入班級
        </button>
      </form>
      {error && <p className="mt-2 text-xs text-accent-red">{error}</p>}
    </div>
  );
}
