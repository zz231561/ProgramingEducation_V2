"use client";

/**
 * 首次登入 profile gate（5-1c-2）— 學生未填身分資料則擋在填寫頁。
 *
 * 僅 role=student 受限；教師/admin 直接放行。任何非 404 錯誤一律 fail-open
 * （不因後端暫時性問題把使用者鎖在門外）。
 */

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { api, ApiRequestError } from "@/lib/api";
import { getMyProfile } from "@/lib/profile";

import { ProfileSetupForm } from "./profile-setup-form";

type State =
  | { mode: "checking" }
  | { mode: "needs"; email: string }
  | { mode: "pass" };

export function ProfileGate({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<State>({ mode: "checking" });

  useEffect(() => {
    let cancelled = false;
    const set = (s: State) => {
      if (!cancelled) setState(s);
    };

    void (async () => {
      try {
        const me = await api<{ role: string; email: string }>("/users/me");
        if (me.role !== "student") {
          set({ mode: "pass" });
          return;
        }
        try {
          await getMyProfile();
          set({ mode: "pass" });
        } catch (e) {
          if (e instanceof ApiRequestError && e.status === 404) {
            set({ mode: "needs", email: me.email });
          } else {
            set({ mode: "pass" }); // 非 404 → 不阻擋
          }
        }
      } catch {
        set({ mode: "pass" }); // /users/me 失敗（401 已由 api 重導）→ 不阻擋
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  if (state.mode === "checking") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg-canvas">
        <Loader2 className="size-5 animate-spin text-text-muted" />
      </div>
    );
  }

  if (state.mode === "needs") {
    return (
      <ProfileSetupForm
        email={state.email}
        onComplete={() => setState({ mode: "pass" })}
      />
    );
  }

  return <>{children}</>;
}
