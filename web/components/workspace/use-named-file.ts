"use client";

/**
 * 命名檔案狀態 hook（U2e 快捷鍵修訂）— 仿主流編輯器：
 * - Ctrl/Cmd+S：已命名 → 直接覆寫；未命名 → 開另存對話框（檔名反白）
 * - 開新檔案：內容未存過「我的程式碼」時先確認，再重設為預設範本
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { saveCodeFile, saveDraft } from "@/lib/code-files";

const SAVED_FLASH_MS = 1500;

export function useNamedFile({
  getCode,
  injectCode,
  defaultCode,
}: {
  /** 取得編輯器目前內容 */
  getCode: () => string;
  /** 以程式碼取代編輯器內容 */
  injectCode: (code: string) => void;
  /** 開新檔案時的預設範本 */
  defaultCode: string;
}) {
  const [currentName, setCurrentName] = useState<string | null>(null);
  const [saveAsOpen, setSaveAsOpen] = useState(false);
  const [savedFlash, setSavedFlash] = useState(false);
  // 每次成功儲存 +1，通知側欄重抓列表
  const [refreshToken, setRefreshToken] = useState(0);
  // 內容自上次「存入我的程式碼 / 載入檔案」後是否被使用者改過
  const namedDirtyRef = useRef(false);
  // 程式化注入（載入/開新檔）觸發的 onChange 不算使用者修改
  const suppressRef = useRef<string | null>(null);
  const flashTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /** 由編輯器 onChange 呼叫：標記使用者修改。 */
  const markTyped = useCallback((code: string) => {
    if (suppressRef.current === code) {
      suppressRef.current = null;
      return;
    }
    namedDirtyRef.current = true;
  }, []);

  /** 由草稿還原檔名關聯（進頁時；不回寫伺服器）。 */
  const restoreName = useCallback((name: string) => {
    setCurrentName(name);
    namedDirtyRef.current = false;
  }, []);

  /** 從側欄載入檔案後呼叫。 */
  const markLoaded = useCallback((code: string, name: string) => {
    suppressRef.current = code;
    setCurrentName(name);
    namedDirtyRef.current = false;
    // 持久化檔名關聯（重整/再登入後停留在此檔）；失敗不擋操作
    void saveDraft(code, name).catch(() => {});
  }, []);

  const saveNamed = useCallback(
    async (name: string) => {
      const code = getCode();
      await saveCodeFile(name, code);
      setCurrentName(name);
      namedDirtyRef.current = false;
      void saveDraft(code, name).catch(() => {}); // 持久化檔名關聯
      setRefreshToken((n) => n + 1);
      setSavedFlash(true);
      if (flashTimerRef.current) clearTimeout(flashTimerRef.current);
      flashTimerRef.current = setTimeout(
        () => setSavedFlash(false),
        SAVED_FLASH_MS,
      );
    },
    [getCode],
  );

  /** Ctrl/Cmd+S 入口：已命名直接覆寫，失敗或未命名開對話框。 */
  const requestSave = useCallback(() => {
    if (currentName) {
      saveNamed(currentName).catch(() => setSaveAsOpen(true));
    } else {
      setSaveAsOpen(true);
    }
  }, [currentName, saveNamed]);

  /** 重設編輯器為預設範本並清除檔名關聯（不含未存確認）。 */
  const resetToDefault = useCallback(() => {
    suppressRef.current = defaultCode;
    injectCode(defaultCode);
    setCurrentName(null);
    namedDirtyRef.current = false;
    void saveDraft(defaultCode, null).catch(() => {}); // 清除檔名關聯
  }, [injectCode, defaultCode]);

  const newFile = useCallback(() => {
    const code = getCode();
    const unsaved = currentName
      ? namedDirtyRef.current
      : code.trim() !== "" && code !== defaultCode;
    if (
      unsaved &&
      !confirm(
        "目前內容尚未儲存至「我的程式碼」，開新檔案將取代編輯區內容。確定繼續？",
      )
    )
      return;
    resetToDefault();
  }, [currentName, getCode, defaultCode, resetToDefault]);

  // Ctrl/Cmd+S 攔截（走 ref 讓 listener 只掛一次）
  const requestSaveRef = useRef(requestSave);
  useEffect(() => {
    requestSaveRef.current = requestSave;
  });
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        requestSaveRef.current();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      if (flashTimerRef.current) clearTimeout(flashTimerRef.current);
    };
  }, []);

  return {
    currentName,
    saveAsOpen,
    setSaveAsOpen,
    savedFlash,
    refreshToken,
    markTyped,
    markLoaded,
    restoreName,
    saveNamed,
    newFile,
    resetToDefault,
  };
}
