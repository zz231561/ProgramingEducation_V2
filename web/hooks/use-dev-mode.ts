"use client";

/**
 * 開發者模式 hooks（DEV-2/4）。
 *
 * - `useDevMode`：是否為 dev 帳號（後端 /dev/status 判定，非 dev 元件不渲染）
 */

import { useEffect, useState } from "react";

import {
  fetchIsDev,
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

