"use client";

/**
 * 教師區 layout（5-5a-3 導航改造）— 角色 gating 一次，子頁（班級 / 作業）共用。
 * 非 teacher 顯示無權限提示（後端授權層為真正防線，此處僅避免誤入空頁）。
 */

import { Loader2 } from "lucide-react";

import { useRole } from "@/lib/use-role";

export default function TeacherLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const role = useRole();

  return (
    <div className="mx-auto h-full max-w-3xl overflow-y-auto px-6 py-8">
      {role === null && (
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <Loader2 className="size-4 animate-spin" />
          載入中…
        </div>
      )}
      {role !== null && role !== "teacher" && (
        <p className="text-sm text-text-secondary">此頁面僅供教師使用。</p>
      )}
      {role === "teacher" && children}
    </div>
  );
}
