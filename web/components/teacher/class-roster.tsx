"use client";

/**
 * 班級名冊（5-1c-1）— 展開時 lazy 載入該班學生 profile。
 * 欄位：姓名 / 學號 / 系所 / 校名 / email（皆學生自填身分）。
 */

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { ApiRequestError } from "@/lib/api";
import { ClassMember, getClassMembers } from "@/lib/classroom";

type View =
  | { mode: "loading" }
  | { mode: "error"; message: string }
  | { mode: "ready"; members: ClassMember[] };

export function ClassRoster({ classId }: { classId: string }) {
  const [view, setView] = useState<View>({ mode: "loading" });

  useEffect(() => {
    let cancelled = false;
    getClassMembers(classId).then(
      (members) => {
        if (!cancelled) setView({ mode: "ready", members });
      },
      (e) => {
        if (!cancelled) {
          const msg =
            e instanceof ApiRequestError ? e.body.message : "載入名冊失敗";
          setView({ mode: "error", message: msg });
        }
      },
    );
    return () => {
      cancelled = true;
    };
  }, [classId]);

  if (view.mode === "loading") {
    return (
      <div className="flex items-center gap-2 px-3 py-4 text-xs text-text-muted">
        <Loader2 className="size-3.5 animate-spin" />
        載入名冊…
      </div>
    );
  }

  if (view.mode === "error") {
    return (
      <p className="px-3 py-4 text-xs text-accent-red">{view.message}</p>
    );
  }

  if (view.members.length === 0) {
    return (
      <p className="px-3 py-4 text-xs text-text-muted">
        尚無學生加入。分享邀請碼讓學生加入班級。
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b border-border-muted text-text-muted">
            <th className="px-3 py-2 font-medium">姓名</th>
            <th className="px-3 py-2 font-medium">學號</th>
            <th className="px-3 py-2 font-medium">系所</th>
            <th className="px-3 py-2 font-medium">校名</th>
            <th className="px-3 py-2 font-medium">Email</th>
          </tr>
        </thead>
        <tbody>
          {view.members.map((m) => (
            <tr
              key={m.user_id}
              className="border-b border-border-muted last:border-0 text-text-secondary"
            >
              <td className="px-3 py-2 text-text-primary">{m.real_name ?? "—"}</td>
              <td className="px-3 py-2 font-mono">{m.student_id ?? "—"}</td>
              <td className="px-3 py-2">{m.department ?? "—"}</td>
              <td className="px-3 py-2">{m.school ?? "—"}</td>
              <td className="px-3 py-2">{m.email}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
