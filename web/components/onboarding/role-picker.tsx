"use client";

/**
 * Onboarding 身分選擇（5-1d-3）— 首次登入選擇教師 / 學生。
 * 選擇後由 gate 重新評估：學生續填 profile，教師直接進入。
 */

import { useState } from "react";
import { GraduationCap, Loader2, School } from "lucide-react";

import { Role, selectRole } from "@/lib/identity";

const OPTIONS: {
  role: Role;
  label: string;
  desc: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  {
    role: "student",
    label: "我是學生",
    desc: "跟隨學習路徑寫程式、與 AI 對話、完成測驗",
    icon: GraduationCap,
  },
  {
    role: "teacher",
    label: "我是教師",
    desc: "建立班級、管理學生名冊、查看學習狀況",
    icon: School,
  },
];

export function RolePicker({ onComplete }: { onComplete: () => void }) {
  const [busy, setBusy] = useState<Role | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pick = async (role: Role) => {
    if (busy) return;
    setBusy(role);
    setError(null);
    try {
      await selectRole(role);
      onComplete();
    } catch {
      setError("設定失敗，請重試");
      setBusy(null);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-canvas px-4 py-8">
      <div className="w-full max-w-md">
        <h1 className="text-center text-xl font-semibold text-text-primary">
          歡迎使用 Codedge
        </h1>
        <p className="mt-2 text-center text-sm text-text-secondary">
          請選擇你的身分以繼續。
        </p>

        <div className="mt-6 space-y-3">
          {OPTIONS.map((o) => (
            <button
              key={o.role}
              onClick={() => pick(o.role)}
              disabled={busy !== null}
              className="flex w-full items-center gap-4 rounded-lg border border-border-default bg-bg-default p-4 text-left transition-colors hover:border-border-emphasis hover:bg-surface-2 disabled:opacity-50"
            >
              <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-border-default bg-bg-canvas text-text-secondary">
                {busy === o.role ? (
                  <Loader2 className="size-5 animate-spin" />
                ) : (
                  <o.icon className="size-5" />
                )}
              </div>
              <div className="min-w-0">
                <div className="text-sm font-medium text-text-primary">
                  {o.label}
                </div>
                <div className="mt-0.5 text-xs text-text-muted">{o.desc}</div>
              </div>
            </button>
          ))}
        </div>

        {error && (
          <p className="mt-4 text-center text-xs text-accent-red">{error}</p>
        )}
      </div>
    </div>
  );
}
