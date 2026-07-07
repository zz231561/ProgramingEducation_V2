"use client";

/**
 * 教師端班級管理頁（roadmap 5-1c-1）。
 *
 * 角色 gating：以 /auth/me 判定，非 teacher 顯示無權限提示（後端授權層為真正防線，
 * 此處僅避免學生誤入空頁）。
 */

import { useEffect, useState } from "react";
import { Loader2, School } from "lucide-react";

import { AssignmentManager } from "@/components/teacher/assignment-manager";
import { ClassManager } from "@/components/teacher/class-manager";
import { api } from "@/lib/api";

type Gate = "loading" | "allowed" | "denied";
type Tab = "classes" | "assignments";

const TABS: { key: Tab; label: string }[] = [
  { key: "classes", label: "班級管理" },
  { key: "assignments", label: "作業" },
];

export default function TeacherPage() {
  const [gate, setGate] = useState<Gate>("loading");
  const [tab, setTab] = useState<Tab>("classes");

  useEffect(() => {
    let cancelled = false;
    api<{ role: string }>("/users/me").then(
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
        <h1 className="text-xl font-medium text-text-primary">教師中心</h1>
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

      {gate === "allowed" && (
        <>
          <div className="mt-4 flex gap-1 border-b border-border-default">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`-mb-px border-b-2 px-3 py-2 text-sm transition-colors ${
                  tab === t.key
                    ? "border-[#F78166] text-text-primary"
                    : "border-transparent text-text-secondary hover:text-text-primary"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          {tab === "classes" ? <ClassManager /> : <AssignmentManager />}
        </>
      )}
    </div>
  );
}
