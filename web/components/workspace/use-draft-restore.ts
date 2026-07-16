"use client";

/**
 * 進 Workspace 還原草稿 hook（U2e）— 內容 + 檔名關聯一起還原；
 * 404/失敗 fail-open 用預設範本。自 workspace/page.tsx 拆出。
 */

import { useEffect, useState } from "react";

import { getDraft } from "@/lib/code-files";

export function useDraftRestore({
  markSaved,
  restoreName,
}: {
  /** 還原後標記自動存檔基準（避免無變更也觸發存檔） */
  markSaved: (code: string) => void;
  /** 還原最後開啟的命名檔案關聯 */
  restoreName: (name: string) => void;
}): string | null | undefined {
  // null = 載入中（不掛編輯器）；undefined = 無草稿（用預設範本）
  const [draftCode, setDraftCode] = useState<string | null | undefined>(null);

  useEffect(() => {
    let cancelled = false;
    getDraft().then(
      (d) => {
        if (cancelled) return;
        markSaved(d.code);
        if (d.opened_name) restoreName(d.opened_name);
        setDraftCode(d.code);
      },
      () => !cancelled && setDraftCode(undefined),
    );
    return () => {
      cancelled = true;
    };
  }, [markSaved, restoreName]);

  return draftCode;
}
