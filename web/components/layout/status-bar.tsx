"use client";

import { Circle } from "lucide-react";

export function StatusBar() {
  return (
    <footer className="flex h-6 shrink-0 items-center border-t border-border-muted bg-bg-default px-3 text-xs text-text-muted">
      {/* 左側：連線狀態 */}
      <div className="flex items-center gap-1.5">
        <Circle className="size-2 fill-accent-green text-accent-green" />
        <span>Connected</span>
      </div>

      <span className="mx-2 text-border-default">│</span>
      <span>C++</span>

      <span className="mx-2 text-border-default">│</span>
      <span>UTF-8</span>

      <span className="mx-2 text-border-default">│</span>
      <span>Ln 1, Col 1</span>

      {/* 右側 */}
      <div className="ml-auto flex items-center gap-3">
        <span>精熟度 —</span>
        <span>使用者</span>
      </div>
    </footer>
  );
}
