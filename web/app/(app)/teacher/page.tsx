"use client";

/**
 * 教師端班級管理頁（roadmap 5-1c-1）。
 *
 * 角色 gating：以 /auth/me 判定，非 teacher 顯示無權限提示（後端授權層為真正防線，
 * 此處僅避免學生誤入空頁）。
 */

import { useEffect, useState } from "react";
import { Loader2, School } from "lucide-react";

import { ClassManager } from "@/components/teacher/class-manager";
import { api } from "@/lib/api";

type Gate = "loading" | "allowed" | "denied";

export default function TeacherPage() {
  const [gate, setGate] = useState<Gate>("loading");

  useEffect(() => {
    let cancelled = false;
    api<{ role: string }>("/auth/me").then(
      (me) => {
        if (!cancelled) setGate(me.role === "teacher" ? "allowed" : "denied");
      },
      () => {
        if (!cancelled) setGate("denied");
      },
    );
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto h-full max-w-3xl overflow-y-auto px-6 py-8">
      <div className="flex items-center gap-2">
        <School className="size-5 text-text-secondary" />
        <h1 className="text-xl font-medium text-text-primary">班級管理</h1>
      </div>

      {gate === "loading" && (
        <div className="mt-8 flex items-center gap-2 text-sm text-text-muted">
          <Loader2 className="size-4 animate-spin" />
          載入中…
        </div>
      )}

      {gate === "denied" && (
        <p className="mt-4 text-sm text-text-secondary">
          此頁面僅供教師使用。
        </p>
      )}

      {gate === "allowed" && <ClassManager />}
    </div>
  );
}
