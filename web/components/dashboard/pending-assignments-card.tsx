"use client";

/**
 * Dashboard「待辦作業」卡（5-5b-3）— 列出尚未繳交的作業，連往作業頁。
 * 自帶 fetch；無作業時不渲染（避免版面雜訊）。
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { ClipboardList } from "lucide-react";

import { formatDue, isOverdue } from "@/lib/assignment-format";
import { StudentAssignment, listMyAssignments } from "@/lib/assignments";

export function PendingAssignmentsCard() {
  const [items, setItems] = useState<StudentAssignment[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    listMyAssignments().then(
      (xs) => !cancelled && setItems(xs),
      () => {}, // 靜默：載不到就不顯示卡片
    );
    return () => {
      cancelled = true;
    };
  }, []);

  if (!items || items.length === 0) return null;
  const pending = items.filter((a) => a.submission == null);

  return (
    <section className="rounded-md border border-border-default bg-surface-1 p-4">
      <div className="mb-3 flex items-center gap-2">
        <ClipboardList className="size-4 text-text-secondary" />
        <h2 className="text-sm font-medium text-text-primary">待辦作業</h2>
        {pending.length > 0 && (
          <span className="text-xs text-text-muted">{pending.length} 項待繳</span>
        )}
      </div>
      {pending.length === 0 ? (
        <p className="text-sm text-text-muted">作業都已繳交。</p>
      ) : (
        <ul className="space-y-2">
          {pending.map((a) => (
            <li key={a.id}>
              <Link
                href="/assignments"
                className="flex items-center justify-between gap-3 rounded-md border border-border-default bg-bg-canvas px-3 py-2 text-sm transition-colors hover:border-border-emphasis"
              >
                <span className="truncate text-text-primary">{a.title}</span>
                <span className="shrink-0 text-xs text-text-muted">
                  {formatDue(a.due_at)}
                  {isOverdue(a.due_at) && (
                    <span className="text-accent-orange"> · 逾期</span>
                  )}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
