"use client";

/**
 * Active Reflection 載入 hook（Phase 2-5d）。
 *
 * 訂閱 sessionStorage 內的 `active_reflection_id`，呼叫 GET /reflection/{id} 取資料；
 * 同 tab 變更透過 custom event，跨 tab 變更透過 storage event。
 */

import { useCallback, useEffect, useState } from "react";

import { ApiRequestError } from "@/lib/api";
import {
  ACTIVE_REFLECTION_EVENT,
  clearActiveReflectionId,
  getActiveReflectionId,
} from "@/lib/active-reflection";
import { Reflection, getReflection } from "@/lib/reflection";

export interface UseActiveReflectionState {
  reflection: Reflection | null;
  loading: boolean;
  error: string | null;
  /** 手動觸發重新載入（PATCH 後呼叫） */
  refresh: () => Promise<void>;
  /** 清除 active 並讓 sidebar 顯示空狀態 */
  clear: () => void;
  /** 樂觀更新本地 reflection（PATCH 成功時 caller 直接傳新資料避免再 fetch） */
  setReflection: (r: Reflection) => void;
}

export function useActiveReflection(): UseActiveReflectionState {
  const [reflection, setReflection] = useState<Reflection | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  const refresh = useCallback(async () => {
    const id = getActiveReflectionId();
    if (!id) {
      setReflection(null);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setReflection(await getReflection(id));
    } catch (e) {
      setReflection(null);
      // 反思被刪除（404）→ 清除過期 ID，UI 顯示空狀態而不是錯誤
      if (e instanceof ApiRequestError && e.status === 404) {
        clearActiveReflectionId();
      } else {
        setError(e instanceof Error ? e.message : "載入失敗");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // 初次載入 + 訂閱變更
  useEffect(() => {
    refresh();
    const onChange = () => setVersion((v) => v + 1);
    window.addEventListener(ACTIVE_REFLECTION_EVENT, onChange);
    window.addEventListener("storage", onChange);
    return () => {
      window.removeEventListener(ACTIVE_REFLECTION_EVENT, onChange);
      window.removeEventListener("storage", onChange);
    };
  }, [refresh]);

  // version 變動 → 重新 fetch
  useEffect(() => {
    if (version > 0) refresh();
  }, [version, refresh]);

  const clear = useCallback(() => {
    clearActiveReflectionId();
    setReflection(null);
  }, []);

  return { reflection, loading, error, refresh, clear, setReflection };
}
