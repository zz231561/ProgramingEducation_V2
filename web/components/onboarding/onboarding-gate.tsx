"use client";

/**
 * Onboarding gate（5-1c-2 / 5-1d-3）— 依序引導：
 *   ① 未選身分 → 身分選擇頁（RolePicker）
 *   ② 學生且未填 profile → 身分資料填寫頁（ProfileSetupForm）
 *   ③ 其餘 → 放行
 *
 * 教師在 ① 之後直接放行。任何非 404 錯誤一律 fail-open（不因後端暫時性問題
 * 把使用者鎖在門外）。
 */

import { useCallback, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { api, ApiRequestError } from "@/lib/api";
import { getMyProfile } from "@/lib/profile";

import { ProfileSetupForm } from "./profile-setup-form";
import { RolePicker } from "./role-picker";

type State =
  | { mode: "checking" }
  | { mode: "role" }
  | { mode: "profile"; email: string }
  | { mode: "pass" };

export function OnboardingGate({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<State>({ mode: "checking" });

  const evaluate = useCallback(async (): Promise<void> => {
    try {
      const me = await api<{ role: string; role_selected: boolean; email: string }>(
        "/users/me",
      );
      if (!me.role_selected) {
        setState({ mode: "role" });
        return;
      }
      if (me.role !== "student") {
        setState({ mode: "pass" });
        return;
      }
      try {
        await getMyProfile();
        setState({ mode: "pass" });
      } catch (e) {
        if (e instanceof ApiRequestError && e.status === 404) {
          setState({ mode: "profile", email: me.email });
        } else {
          setState({ mode: "pass" }); // 非 404 → 不阻擋
        }
      }
    } catch {
      setState({ mode: "pass" }); // /users/me 失敗（401 已由 api 重導）→ 不阻擋
    }
  }, []);

  useEffect(() => {
    // evaluate 為 async，setState 發生在 microtask（非 effect 同步階段）
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void evaluate();
  }, [evaluate]);

  if (state.mode === "checking") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg-canvas">
        <Loader2 className="size-5 animate-spin text-text-muted" />
      </div>
    );
  }

  if (state.mode === "role") {
    // 選完身分後重新評估（學生 → 續填 profile；教師 → 放行）
    return (
      <RolePicker
        onComplete={() => {
          setState({ mode: "checking" });
          void evaluate();
        }}
      />
    );
  }

  if (state.mode === "profile") {
    return (
      <ProfileSetupForm
        email={state.email}
        onComplete={() => setState({ mode: "pass" })}
      />
    );
  }

  return <>{children}</>;
}
