"use client";

/**
 * 單一班級卡（5-1c-1）— 邀請碼、成員數、停用/啟用、展開名冊。
 */

import { useState } from "react";
import { Check, ChevronDown, Copy, Users } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { ClassInfo, updateClass } from "@/lib/classroom";

import { ClassRoster } from "./class-roster";

export function ClassCard({
  klass,
  onUpdated,
}: {
  klass: ClassInfo;
  onUpdated: (updated: ClassInfo) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(klass.invite_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* 剪貼簿不可用時靜默；使用者仍可手動複製 */
    }
  };

  const toggleActive = async () => {
    setBusy(true);
    setError(null);
    try {
      const updated = await updateClass(klass.id, { is_active: !klass.is_active });
      onUpdated(updated);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.body.message : "更新失敗");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-md border border-border-default bg-surface-1">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 p-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="truncate text-sm font-medium text-text-primary">
              {klass.name}
            </h3>
            {!klass.is_active && (
              <span className="rounded-pill border border-border-emphasis px-2 py-0.5 text-[10px] text-text-muted">
                已停用
              </span>
            )}
          </div>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-text-muted">
            <Users className="size-3.5" />
            {klass.member_count} 位學生
          </div>
        </div>

        {/* 邀請碼 */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-muted">邀請碼</span>
          <code className="rounded bg-surface-inset px-2 py-1 font-mono text-sm tracking-widest text-text-primary">
            {klass.invite_code}
          </code>
          <button
            onClick={copyCode}
            className="flex size-7 items-center justify-center rounded-md text-text-muted hover:bg-surface-2 hover:text-text-primary transition-colors"
            aria-label="複製邀請碼"
            title="複製邀請碼"
          >
            {copied ? (
              <Check className="size-3.5 text-accent-green" />
            ) : (
              <Copy className="size-3.5" />
            )}
          </button>
        </div>

        {/* 操作 */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex items-center gap-1 rounded-md border border-border-default px-2.5 py-1 text-xs text-text-secondary hover:bg-surface-2 hover:text-text-primary transition-colors"
            aria-expanded={expanded}
          >
            名冊
            <ChevronDown
              className={`size-3.5 transition-transform ${expanded ? "rotate-180" : ""}`}
            />
          </button>
          <button
            onClick={toggleActive}
            disabled={busy}
            className="rounded-md border border-border-default px-2.5 py-1 text-xs text-text-secondary hover:bg-surface-2 hover:text-text-primary transition-colors disabled:opacity-50"
          >
            {klass.is_active ? "停用" : "啟用"}
          </button>
        </div>
      </div>

      {error && <p className="px-4 pb-3 text-xs text-accent-red">{error}</p>}

      {expanded && (
        <div className="border-t border-border-muted">
          <ClassRoster classId={klass.id} />
        </div>
      )}
    </div>
  );
}
