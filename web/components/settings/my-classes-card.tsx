"use client";

/**
 * 我的班級卡（Settings，僅學生）— 列出已加入班級 + 邀請碼加入表單。
 */

import { useCallback, useEffect, useState } from "react";

import { JoinClassForm } from "@/components/classroom/join-class-form";
import { MyClassInfo, listMyClasses } from "@/lib/classroom";
import { useRole } from "@/lib/use-role";

export function MyClassesCard() {
  const role = useRole();
  const [classes, setClasses] = useState<MyClassInfo[] | null>(null);

  const load = useCallback(() => {
    let cancelled = false;
    listMyClasses().then(
      (xs) => !cancelled && setClasses(xs),
      () => {}, // 載入失敗保持 null（不擋整頁）
    );
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (role === "student") return load();
  }, [role, load]);

  if (role !== "student") return null;

  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <h3 className="text-sm font-medium text-text-primary">我的班級</h3>

      {classes && classes.length > 0 ? (
        <ul className="mt-2 space-y-1">
          {classes.map((c) => (
            <li key={c.id} className="text-sm text-text-secondary">
              {c.name}
              <span className="ml-2 text-xs text-text-muted">
                {c.teacher_name} 老師
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-xs text-text-muted">
          {classes === null ? "載入中…" : "尚未加入任何班級。"}
        </p>
      )}

      <div className="mt-3">
        <JoinClassForm onJoined={load} />
      </div>
    </div>
  );
}
