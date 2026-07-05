"use client";

/**
 * Settings「開發者工具」區塊殼（DEV-2）— 僅 dev 帳號渲染。
 *
 * 注意：不渲染只是 UX，防線在後端（每個 /dev 端點掛 require_dev_user）。
 */

import { TerminalSquare } from "lucide-react";

import { useDevMode } from "@/hooks/use-dev-mode";

import { DevDiagnosisCard } from "./dev-diagnosis-card";
import { DevMasteryCard } from "./dev-mastery-card";
import { DevQuestionBankCard } from "./dev-question-bank-card";
import { DevResetCard } from "./dev-reset-card";
import { DevRoleCard } from "./dev-role-card";
import { DevUnlockCard } from "./dev-unlock-card";

export function DevToolsSection() {
  const isDev = useDevMode();
  if (!isDev) return null;

  return (
    <section className="mt-10">
      <div className="flex items-center gap-2">
        <TerminalSquare className="size-4 text-text-secondary" />
        <h2 className="text-sm font-medium uppercase tracking-wide text-text-secondary">
          開發者工具
        </h2>
      </div>
      <p className="mt-1 text-xs text-text-muted">
        僅開發者帳號可見。以下操作直接修改你帳號的學習資料，供功能測試使用。
      </p>
      <div className="mt-4 space-y-4">
        <DevRoleCard />
        <DevUnlockCard />
        <DevMasteryCard />
        <DevDiagnosisCard />
        <DevQuestionBankCard />
        <DevResetCard />
      </div>
    </section>
  );
}
