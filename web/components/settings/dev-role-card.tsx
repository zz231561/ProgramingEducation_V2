"use client";

/** 身分切換卡 — 直接修改 users.role，以真實角色權限驗證學生端與教師端。 */

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
    api<{ role: string }>("/users/me").then(
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
        直接修改 DB role，切換後可用真實權限驗證學生端與教師端。
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
