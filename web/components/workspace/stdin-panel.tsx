"use client";

import { X } from "lucide-react";

interface StdinPanelProps {
  /** stdin 內容 */
  value: string;
  /** 內容變更 */
  onChange: (value: string) => void;
  /** 關閉面板 */
  onClose: () => void;
}

/**
 * stdin 輸入面板 — Editor 上方滑出，多行文字輸入
 */
export function StdinPanel({ value, onChange, onClose }: StdinPanelProps) {
  return (
    <div className="flex flex-col border-b border-border-default bg-bg-default">
      {/* Header */}
      <div className="flex h-7 items-center justify-between px-3">
        <span className="text-xs text-text-secondary">
          標準輸入 (stdin) — 每行一筆測試資料
        </span>
        <button
          onClick={onClose}
          className="flex size-5 items-center justify-center rounded text-text-muted hover:text-text-secondary transition-colors"
          title="關閉 stdin"
        >
          <X className="size-3.5" />
        </button>
      </div>

      {/* 輸入區 */}
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="輸入測試資料（每行一筆）..."
        className="h-20 resize-none bg-bg-canvas px-3 py-2 font-mono text-xs text-text-primary placeholder:text-text-muted focus:outline-none"
        spellCheck={false}
      />
    </div>
  );
}
