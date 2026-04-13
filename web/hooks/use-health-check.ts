"use client";

import { useState, useEffect, useCallback } from "react";

export interface HealthStatus {
  status: "ok" | "degraded" | "disconnected";
  database: "connected" | "disconnected";
  redis: "connected" | "disconnected";
}

const POLL_INTERVAL = 30_000; // 30 秒

/** 定期 poll /api/health，回傳後端連線狀態。 */
export function useHealthCheck(): HealthStatus {
  const [health, setHealth] = useState<HealthStatus>({
    status: "disconnected",
    database: "disconnected",
    redis: "disconnected",
  });

  const check = useCallback(async () => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5_000);

    try {
      const res = await fetch("/api/health", { signal: controller.signal });
      if (!res.ok) throw new Error("not ok");
      const body = await res.json();
      setHealth({
        status: body.status ?? "disconnected",
        database: body.services?.database ?? "disconnected",
        redis: body.services?.redis ?? "disconnected",
      });
    } catch {
      setHealth({
        status: "disconnected",
        database: "disconnected",
        redis: "disconnected",
      });
    } finally {
      clearTimeout(timeoutId);
    }
  }, []);

  useEffect(() => {
    check();
    const id = setInterval(check, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [check]);

  return health;
}
