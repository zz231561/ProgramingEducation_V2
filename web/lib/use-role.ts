"use client";

/**
 * 取得當前使用者角色（教師/學生）— 供角色化導航與頁面 gating 用。
 * 訂閱 ROLE_CHANGE_EVENT，讓 DEV 身分切換後即時更新，無需重整。
 */

import { useEffect, useState } from "react";

import { api } from "./api";
import { ROLE_CHANGE_EVENT } from "./dev-mode";

export type Role = "student" | "teacher" | "admin";

export function useRole(): Role | null {
  const [role, setRole] = useState<Role | null>(null);

  useEffect(() => {
    let cancelled = false;
    const refresh = () =>
      api<{ role: Role }>("/users/me").then(
        (me) => !cancelled && setRole(me.role),
        () => {}, // 取不到角色時保持 null（導航退回學生預設）
      );
    void refresh();
    window.addEventListener(ROLE_CHANGE_EVENT, refresh);
    return () => {
      cancelled = true;
      window.removeEventListener(ROLE_CHANGE_EVENT, refresh);
    };
  }, []);

  return role;
}
