"use client";

/**
 * 身分設定卡（5-1d-4）— 顯示目前身分，可切換教師/學生。
 * 切換＝後端全清該帳號所有資料（不可復原），故二段確認 + 明確警告。
 * 成功後導回根路徑讓 onboarding gate 重新引導。
 */

import { useEffect, useState } from "react";
import { TriangleAlert } from "lucide-react";

import { api } from "@/lib/api";
import { Role, selectRole } from "@/lib/identity";

const LABEL: Record<string, string> = {
  student: "學生",
  teacher: "教師",
  admin: "管理員",
};

export function IdentityCard() {
  const [role, setRole] = useState<string | null>(null);
  const [armed, setArmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api<{ role: string }>("/users/me").then(
      (m) => !cancelled && setRole(m.role),
      () => !cancelled && setError("無法取得目前身分"),
    );
    return () => {
      cancelled = true;
    };
  }, []);

  const target: Role = role === "teacher" ? "student" : "teacher";

  const doSwitch = async () => {
    setBusy(true);
    setError(null);
    try {
      await selectRole(target);
      window.location.href = "/"; // 資料已清空 + 身分變更 → 重新走 onboarding
    } catch {
      setError("切換失敗，請重試");
      setBusy(false);
      setArmed(false);
    }
  };

  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <h3 className="text-sm font-medium text-text-primary">身分設定</h3>
      <p className="mt-1 text-xs text-text-muted">
        目前身分：
        <span className="text-text-secondary">
          {role ? (LABEL[role] ?? role) : "載入中…"}
        </span>
      </p>

      {!armed ? (
        <button
          type="button"
          onClick={() => setArmed(true)}
          disabled={role === null}
          className="mt-3 rounded-md border border-border-default px-3 py-1.5 text-sm text-text-secondary transition-colors hover:bg-surface-2 hover:text-text-primary disabled:opacity-50"
        >
          切換為{LABEL[target]}
        </button>
      ) : (
        <div className="mt-3 rounded-md border border-accent-red p-3">
          <div className="flex items-start gap-2 text-xs text-accent-red">
            <TriangleAlert className="mt-0.5 size-4 shrink-0" />
            <span>
              切換身分將永久清空你目前所有資料（精熟度 / 課程進度 / 測驗紀錄 /
              對話 / 個人資料 / 班級），此操作無法復原。
            </span>
          </div>
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              onClick={doSwitch}
              disabled={busy}
              className="rounded-md border border-accent-red px-3 py-1.5 text-sm text-accent-red transition-colors hover:bg-surface-2 disabled:opacity-50"
            >
              {busy ? "處理中…" : `確認切換為${LABEL[target]}並清空資料`}
            </button>
            <button
              type="button"
              onClick={() => setArmed(false)}
              disabled={busy}
              className="rounded-md border border-border-default px-3 py-1.5 text-sm text-text-secondary transition-colors hover:bg-surface-2 hover:text-text-primary disabled:opacity-50"
            >
              取消
            </button>
          </div>
        </div>
      )}

      {error && <p className="mt-2 text-xs text-accent-red">{error}</p>}
    </div>
  );
}
