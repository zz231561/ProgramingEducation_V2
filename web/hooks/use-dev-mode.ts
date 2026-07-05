"use client";

/**
 * 開發者模式 hooks（DEV-2/4）。
 *
 * - `useDevMode`：是否為 dev 帳號（後端 /dev/status 判定，非 dev 元件不渲染）
 * - `useGhostUnlock`：幽靈解鎖是否生效（dev 且開關開啟才為 true）
 */

import { useEffect, useState } from "react";

import {
  GHOST_UNLOCK_EVENT,
  fetchIsDev,
  getGhostUnlockFlag,
} from "@/lib/dev-mode";

export function useDevMode(): boolean {
  const [isDev, setIsDev] = useState(false);
  useEffect(() => {
    let cancelled = false;
    fetchIsDev().then((v) => {
      if (!cancelled && v) setIsDev(true);
    });
    return () => {
      cancelled = true;
    };
  }, []);
  return isDev;
}

export function useGhostUnlock(): boolean {
  const isDev = useDevMode();
  const [flag, setFlag] = useState(false);
  useEffect(() => {
    // localStorage 只在 client 有值：mount 後同步一次 + 訂閱開關變更
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setFlag(getGhostUnlockFlag());
    const sync = () => setFlag(getGhostUnlockFlag());
    window.addEventListener(GHOST_UNLOCK_EVENT, sync);
    return () => window.removeEventListener(GHOST_UNLOCK_EVENT, sync);
  }, []);
  return isDev && flag;
}
