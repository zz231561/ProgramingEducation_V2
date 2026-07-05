"use client";

/**
 * 身分切換卡（DEV-6）— student ⇄ teacher，真改 users.role。
 *
 * 目前教師端 UI 尚未建置（Phase 5），切換後行為差異在後端授權層；
 * 顯示當前角色以確認切換生效。
 */

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { devSetRole } from "@/lib/dev-mode";

const ROLE_LABEL: Record<string, string> = {
  student: "學生",
  teacher: "教師",
  admin: "管理員",
};

export function DevRoleCard() {
  const [role, setRole] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api<{ role: string }>("/auth/me").then(
      (me) => {
        if (!cancelled) setRole(me.role);
      },
      () => {
        if (!cancelled) setError("無法取得目前角色");
      },
    );
    return () => {
      cancelled = true;
    };
  }, []);

  const target = role === "teacher" ? "student" : "teacher";

  const handleSwitch = async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await devSetRole(target as "student" | "teacher");
      setRole(result.role);
    } catch {
      setError("切換失敗");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <h3 className="text-sm font-medium text-text-primary">身分切換</h3>
      <p className="mt-1 text-xs text-text-muted">
        真改 DB role（與真實帳號行為一致）；教師端 UI 於 Phase 5 建置，現階段差異在後端授權。
      </p>
      <div className="mt-3 flex items-center gap-3">
        <span className="text-sm text-text-secondary">
          目前角色：
          <span className="text-text-primary">
            {role ? (ROLE_LABEL[role] ?? role) : "載入中…"}
          </span>
        </span>
        <button
          type="button"
          onClick={handleSwitch}
          disabled={busy || role === null}
          className="inline-flex h-8 items-center rounded-md border border-btn-default-border bg-btn-default-bg px-3 text-sm text-text-primary hover:bg-surface-2 disabled:opacity-50"
        >
          切換為{ROLE_LABEL[target]}
        </button>
      </div>
      {error && <p className="mt-2 text-xs text-accent-red">{error}</p>}
    </div>
  );
}
