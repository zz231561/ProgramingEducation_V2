"use client";

/**
 * 幽靈解鎖卡（DEV-4）— 開啟後 Learn 頁 locked unit 變可點（僅瀏覽）。
 *
 * 純前端便利開關（存 localStorage、僅 dev 生效）：不改 unit status、
 * 不觸發 BKT，locked unit 的「開始學習」等狀態轉移仍維持原限制。
 */

import { useEffect, useState } from "react";

import { getGhostUnlockFlag, setGhostUnlockFlag } from "@/lib/dev-mode";

export function DevUnlockCard() {
  const [on, setOn] = useState(false);

  useEffect(() => {
    // localStorage 只在 client 有值：mount 後同步一次
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setOn(getGhostUnlockFlag());
  }, []);

  const toggle = () => {
    const next = !on;
    setGhostUnlockFlag(next);
    setOn(next);
  };

  return (
    <div className="rounded-md border border-border-default bg-surface-1 p-4">
      <h3 className="text-sm font-medium text-text-primary">
        解鎖所有課程（幽靈解鎖）
      </h3>
      <p className="mt-1 text-xs text-text-muted">
        開啟後 Learn 頁可點進任何 locked 單元瀏覽內容；不改變單元狀態、不影響熟練度。
      </p>
      <div className="mt-3 flex items-center gap-3">
        <button
          type="button"
          role="switch"
          aria-checked={on}
          onClick={toggle}
          className={`relative h-5 w-9 rounded-pill border transition-colors ${
            on
              ? "border-btn-primary-bg bg-btn-primary-bg"
              : "border-border-emphasis bg-surface-2"
          }`}
        >
          <span
            className={`absolute top-0.5 size-3.5 rounded-full bg-text-primary transition-all ${
              on ? "left-[18px]" : "left-0.5"
            }`}
          />
        </button>
        <span className="text-sm text-text-secondary">
          {on ? "已開啟" : "已關閉"}
        </span>
      </div>
    </div>
  );
}
