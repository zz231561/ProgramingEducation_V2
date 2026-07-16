"use client";

/**
 * 進 Workspace 開機還原 hook（U2e）：
 * - 實作題 handoff（反思 + 檔名 + 起手碼）：自動開啟同名檔案——
 *   草稿仍掛在該檔＝續用最新工作內容；已存過該檔＝載入；否則以起手碼建檔。
 * - 一般進入：還原草稿內容 + 最後開啟的檔名關聯。
 * - 404/失敗 fail-open 用預設範本。自 workspace/page.tsx 拆出。
 */

import { useEffect, useState } from "react";

import {
  getHandedOffReflectionId,
  getHandoffFileName,
  getHandoffStarterCode,
} from "@/lib/active-reflection";
import {
  getCodeFile,
  getDraft,
  listCodeFiles,
  saveCodeFile,
  saveDraft,
} from "@/lib/code-files";

async function resolveHandoffCode(
  fileName: string,
  defaultCode: string,
): Promise<string> {
  // 草稿仍掛在此檔 → 草稿是最新工作內容（named file 只在 Ctrl+S 時更新）
  const draft = await getDraft().catch(() => null);
  if (draft?.opened_name === fileName) return draft.code;

  const files = await listCodeFiles();
  const existing = files.find((f) => f.name === fileName);
  if (existing) return (await getCodeFile(existing.id)).code;

  // 首次進入：以起手碼建檔（立即出現在我的程式碼）
  const starter = getHandoffStarterCode() ?? defaultCode;
  await saveCodeFile(fileName, starter);
  return starter;
}

export function useDraftRestore({
  defaultCode,
  markSaved,
  restoreName,
}: {
  /** 起手碼/草稿皆無時的預設範本 */
  defaultCode: string;
  /** 還原後標記自動存檔基準（避免無變更也觸發存檔） */
  markSaved: (code: string) => void;
  /** 還原最後開啟的命名檔案關聯 */
  restoreName: (name: string) => void;
}): string | null | undefined {
  // null = 載入中（不掛編輯器）；undefined = 無草稿（用預設範本）
  const [initialCode, setInitialCode] = useState<string | null | undefined>(
    null,
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const handoffFile = getHandedOffReflectionId()
        ? getHandoffFileName()
        : null;
      if (handoffFile) {
        try {
          const code = await resolveHandoffCode(handoffFile, defaultCode);
          // 持久化檔名關聯，重整後仍停留在此檔
          void saveDraft(code, handoffFile).catch(() => {});
          if (cancelled) return;
          markSaved(code);
          restoreName(handoffFile);
          setInitialCode(code);
          return;
        } catch {
          // fall through：改走一般草稿還原
        }
      }
      try {
        const d = await getDraft();
        if (cancelled) return;
        markSaved(d.code);
        if (d.opened_name) restoreName(d.opened_name);
        setInitialCode(d.code);
      } catch {
        if (!cancelled) setInitialCode(undefined);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [defaultCode, markSaved, restoreName]);

  return initialCode;
}
