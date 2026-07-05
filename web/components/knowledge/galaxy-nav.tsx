"use client";

/**
 * 星系切換導覽（K5 視覺調整二）— 半透明左右按鈕 + 章名指示。
 *
 * 疊在圖譜 canvas 上（absolute），灰階半透明符合 R8 白名單；
 * 切換動畫由父層 KnowledgeGraph 操作 cytoscape 鏡頭。
 */

import { ChevronLeft, ChevronRight } from "lucide-react";

interface Props {
  /** 目前星系顯示名（含進度序），如「運算子（4/10）」。 */
  label: string;
  canPrev: boolean;
  canNext: boolean;
  onPrev: () => void;
  onNext: () => void;
}

const BUTTON_CLASS =
  "absolute top-1/2 z-10 flex size-9 -translate-y-1/2 items-center justify-center " +
  "rounded-pill border border-border-default bg-surface-1/70 text-text-secondary " +
  "transition-colors hover:bg-surface-2 hover:text-text-primary " +
  "disabled:pointer-events-none disabled:opacity-40";

export function GalaxyNav({ label, canPrev, canNext, onPrev, onNext }: Props) {
  return (
    <>
      <button
        type="button"
        aria-label="上一個星系"
        disabled={!canPrev}
        onClick={onPrev}
        className={`${BUTTON_CLASS} left-3`}
      >
        <ChevronLeft className="size-5" />
      </button>
      <button
        type="button"
        aria-label="下一個星系"
        disabled={!canNext}
        onClick={onNext}
        className={`${BUTTON_CLASS} right-3`}
      >
        <ChevronRight className="size-5" />
      </button>
      <div className="absolute bottom-3 left-1/2 z-10 -translate-x-1/2 rounded-pill border border-border-default bg-surface-1/70 px-3 py-1 text-xs text-text-secondary">
        {label}
      </div>
    </>
  );
}
