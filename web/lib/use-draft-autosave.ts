"use client";

/**
 * 草稿自動存檔 hook（U2e）— 停止輸入 2 秒後 PUT /code/draft；
 * 卸載/關頁時以 keepalive 搶救未存變更。
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { saveDraft, saveDraftBeacon } from "./code-files";

const AUTOSAVE_DELAY_MS = 2000;

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

  const schedule = useCallback((code: string) => {
    latestRef.current = code;
    if (code === savedRef.current) return; // 內容未變（如編輯器 mount 通知）不排程
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      timerRef.current = null;
      setStatus("saving");
      try {
        await saveDraft(code);
        savedRef.current = code;
        setStatus("saved");
      } catch {
        setStatus("idle"); // 失敗不打擾使用者；下次變更會再試
      }
    }, AUTOSAVE_DELAY_MS);
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
