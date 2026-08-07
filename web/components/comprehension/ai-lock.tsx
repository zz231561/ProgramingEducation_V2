"use client";

/**
 * AI 鎖 — 變體挑戰進行中禁止使用 Coddy，避免 AI 直接洩漏答案。
 *
 * 為什麼需要真的鎖：Chat 掛在 AppShell 上、每一頁都能用 Ctrl+B 叫出來，
 * 學生在變體挑戰中隨時可以問「這題怎麼寫」——那道題目的用意正是**沒有外援**
 * 地遷移剛學會的概念，能問就失去驗證意義。
 *
 * Provider 必須掛在 ChatPanel 與挑戰 UI 的共同祖先（AppShell）。
 */

import { createContext, useCallback, useContext, useMemo, useState } from "react";

interface AiLockValue {
  /** 非 null = 鎖住，字串為顯示給學生的原因 */
  lockedReason: string | null;
  lockAi: (reason: string) => void;
  unlockAi: () => void;
}

const AiLockContext = createContext<AiLockValue>({
  lockedReason: null,
  lockAi: () => {},
  unlockAi: () => {},
});

export function AiLockProvider({ children }: { children: React.ReactNode }) {
  const [lockedReason, setLockedReason] = useState<string | null>(null);

  const lockAi = useCallback((reason: string) => setLockedReason(reason), []);
  const unlockAi = useCallback(() => setLockedReason(null), []);

  const value = useMemo(
    () => ({ lockedReason, lockAi, unlockAi }),
    [lockedReason, lockAi, unlockAi],
  );

  return <AiLockContext.Provider value={value}>{children}</AiLockContext.Provider>;
}

export function useAiLock() {
  return useContext(AiLockContext);
}
