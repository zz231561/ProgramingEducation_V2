"use client";

/**
 * 草稿自動存檔 hook（U2e）— 近實時：停頓 0.4 秒即存；連續輸入不間斷時
 * 至多每 2 秒也強制存一次。卸載/關頁時以 keepalive 搶救未存變更。
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { saveDraft, saveDraftBeacon } from "./code-files";

const DEBOUNCE_MS = 400;
const MAX_WAIT_MS = 2000;

export type DraftSaveStatus = "idle" | "saving" | "saved";

export function useDraftAutosave(): {
  status: DraftSaveStatus;
  schedule: (code: string) => void;
  markSaved: (code: string) => void;
} {
  const [status, setStatus] = useState<DraftSaveStatus>("idle");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const latestRef = useRef<string | null>(null);
  const savedRef = useRef<string | null>(null);
  const pendingSinceRef = useRef<number | null>(null);

  const schedule = useCallback((code: string) => {
    latestRef.current = code;
    if (code === savedRef.current) return; // 內容未變（如編輯器 mount 通知）不排程
    const now = Date.now();
    pendingSinceRef.current ??= now;
    // 連續輸入時 debounce 不能無限後延：離首次未存變更最多等 MAX_WAIT_MS
    const delay = Math.min(
      DEBOUNCE_MS,
      Math.max(0, pendingSinceRef.current + MAX_WAIT_MS - now),
    );
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      timerRef.current = null;
      pendingSinceRef.current = null;
      const snapshot = latestRef.current ?? code;
      setStatus("saving");
      try {
        await saveDraft(snapshot);
        savedRef.current = snapshot;
        setStatus("saved");
      } catch {
        setStatus("idle"); // 失敗不打擾使用者；下次變更會再試
      }
    }, delay);
  }, []);

  /** 還原草稿後標記基準，避免無變更也觸發存檔。 */
  const markSaved = useCallback((code: string) => {
    latestRef.current = code;
    savedRef.current = code;
  }, []);

  useEffect(() => {
    const flush = () => {
      if (latestRef.current !== null && latestRef.current !== savedRef.current) {
        saveDraftBeacon(latestRef.current);
        savedRef.current = latestRef.current;
      }
    };
    window.addEventListener("beforeunload", flush);
    return () => {
      window.removeEventListener("beforeunload", flush);
      if (timerRef.current) clearTimeout(timerRef.current);
      flush(); // SPA 導航離開 Workspace 時同樣搶救
    };
  }, []);

  return { status, schedule, markSaved };
}
